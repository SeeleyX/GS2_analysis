import os
import re
import sys
import numpy as np
import time
from math import log10, floor

def round_to_3_sig_figs(x):
    """Rounds a number to exactly 3 significant figures."""
    if x == 0:
        return 0.0
    return round(x, -int(floor(log10(abs(x)))) + 2)

def extract_val(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return float(match.group(1).replace('d', 'e').replace('D', 'e'))
    return 0.0

def extract_array(pattern, text):
    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
    return [float(m.group(1).replace('d', 'e').replace('D', 'e')) for m in matches]

def extract_aky(text):
    """Extracts aky from the &kt_grids_single_parameters block."""
    pattern = r'&kt_grids_single_parameters(.*?)/'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        block = match.group(1)
        aky_match = re.search(r'aky\s*=\s*([0-9\.eEdD\+\-]+)', block, re.IGNORECASE)
        if aky_match:
            return aky_match.group(1).replace('d', 'e').replace('D', 'e')
    return "unknown"

def extract_zeff(text):
    """Extracts zeff from the &knobs block."""
    pattern = r'&knobs(.*?)/'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        block = match.group(1)
        zeff_match = re.search(r'zeff\s*=\s*([0-9\.eEdD\+\-]+)', block, re.IGNORECASE)
        if zeff_match:
            return zeff_match.group(1).replace('d', 'e').replace('D', 'e')
    return "unknown"

def replace_in_theta_block(text, var_name, new_value):
    """Replace or insert a variable inside &theta_grid_eik_knobs block"""
    pattern = r'(&theta_grid_eik_knobs.*?/)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Could not find &theta_grid_eik_knobs block")

    block = match.group(1)
    if re.search(rf'^[ \t]*{var_name}[ \t]*=', block, re.MULTILINE):
        new_block = re.sub(
            rf'(^[ \t]*{var_name}[ \t]*=).*',
            rf'\1 {new_value:.6g}',
            block,
            flags=re.MULTILINE
        )
    else:
        new_block = block.rstrip("/ \n") + f"\n  {var_name} = {new_value:.6g}\n/"
    return text.replace(block, new_block)

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <template_file> [run]")
        sys.exit(1)

    template_file = sys.argv[1]
    run_mode = len(sys.argv) > 2 and sys.argv[2].lower() == "run"

    if not os.path.exists(template_file):
        print(f"Error: {template_file} not found.")
        sys.exit(1)

    with open(template_file, 'r') as f:
        template_text = f.read()

    # 0. Define the beta range we would like
    betamin = 0.0
    betamax = 0.018
    betastep = 0.001

    # 1. Get aky for the parent folder name
    aky_val = extract_aky(template_text)
    zeff_val = extract_zeff(template_text)
    parent_dir = f"Zeff_{zeff_val}_b_{betamin*100:.1f}-{(betamax-betastep)*100:.1f}"
    
    if run_mode:
        print(f"Running FULL scan in directory: {parent_dir}\n")
        os.makedirs(parent_dir, exist_ok=True)
    else:
        print(f"DRY RUN: Would create parent directory {parent_dir}\n")

    # Extract physics parameters
    eps = extract_val(r'^[ \t]*eps[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    dens = extract_array(r'^[ \t]*dens[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    temp = extract_array(r'^[ \t]*temp[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    fprim = extract_array(r'^[ \t]*fprim[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    tprim = extract_array(r'^[ \t]*tprim[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)

    sum_term = sum(d * t * (f + tp) for d, t, f, tp in zip(dens, temp, fprim, tprim))
    betas = np.arange(betamin, betamax, betastep)
    processed_beta_primes = set()

    for beta in betas:
        raw_beta_prime = -beta * eps * sum_term
        beta_prime_rounded = round_to_3_sig_figs(raw_beta_prime)

        if beta_prime_rounded in processed_beta_primes:
            continue
        
        processed_beta_primes.add(beta_prime_rounded)
        print(f"beta = {beta:.3f} | beta_prime_input = {beta_prime_rounded:.6g}")

        if not run_mode:
            continue

        # 2. Create nested path: aky_0.4/beta_0.012
        sub_dir_name = f"beta_{beta:.3f}"
        full_path = os.path.join(parent_dir, sub_dir_name)
        os.makedirs(full_path, exist_ok=True)

        # Modify text
        new_text = re.sub(r'(^[ \t]*beta[ \t]*=).*', rf'\1 {beta:.5f}', template_text, flags=re.MULTILINE)
        new_text = replace_in_theta_block(new_text, "beta_prime_input", beta_prime_rounded)

        # Write and Submit
        run_file = os.path.join(full_path, "run.in")
        with open(run_file, 'w') as f:
            f.write(new_text)

        # Move into the specific beta folder to submit
        os.chdir(full_path)
        # Note: we use ../../ because we are now two folders deep (aky_*/beta_*)
        os.system("sbatch ../../submit.slurm run.in")
        os.chdir("../..") # Go back to root

        time.sleep(0.1)

    print(f"\nDone. Processed {len(processed_beta_primes)} unique values in {parent_dir}.")

if __name__ == "__main__":
    main()
