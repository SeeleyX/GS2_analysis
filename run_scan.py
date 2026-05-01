import os
import re
import sys
import numpy as np
import time

# --- CONFIGURATION ---
TEMPLATE_FILE = "template.in"

def extract_val(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return float(match.group(1).replace('d', 'e').replace('D', 'e'))
    return 0.0

def extract_array(pattern, text):
    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
    return [float(m.group(1).replace('d', 'e').replace('D', 'e')) for m in matches]


def replace_in_theta_block(text, var_name, new_value):
    """
    Replace or insert a variable inside &theta_grid_eik_knobs block
    """
    pattern = r'(&theta_grid_eik_knobs.*?/)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if not match:
        raise ValueError("Could not find &theta_grid_eik_knobs block")

    block = match.group(1)

    # Check if variable already exists
    if re.search(rf'^[ \t]*{var_name}[ \t]*=', block, re.MULTILINE):
        new_block = re.sub(
            rf'(^[ \t]*{var_name}[ \t]*=).*',
            rf'\1 {new_value:.6f}',
            block,
            flags=re.MULTILINE
        )
    else:
        # Insert before closing "/"
        new_block = block.rstrip("/ \n") + f"\n  {var_name} = {new_value:.6f}\n/"

    # Replace block in full text
    return text.replace(block, new_block)


def main():
    run_mode = len(sys.argv) > 1 and sys.argv[1].lower() == "run"

    if run_mode:
        print("Running FULL scan\n")
    else:
        print("Running DRY RUN\n")

    # Read template
    with open(TEMPLATE_FILE, 'r') as f:
        template_text = f.read()

    # Extract parameters
    eps = extract_val(r'^[ \t]*eps[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)

    dens = extract_array(r'^[ \t]*dens[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    temp = extract_array(r'^[ \t]*temp[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    fprim = extract_array(r'^[ \t]*fprim[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)
    tprim = extract_array(r'^[ \t]*tprim[ \t]*=[ \t]*([0-9\.eEdD\+\-]+)', template_text)

    print("eps =", eps)
    print("dens =", dens)
    print("temp =", temp)
    print("fprim =", fprim)
    print("tprim =", tprim)

    # Compute sum
    sum_term = sum(d * t * (f + tp) for d, t, f, tp in zip(dens, temp, fprim, tprim))

    print("sum_term =", sum_term)

    betas = np.arange(0.000, 0.085, 0.005)

    for beta in betas:
        beta_prime = -beta * eps * sum_term

        print(f"beta = {beta:.3f} | beta_prime_input = {beta_prime:.6f}")

        if not run_mode:
            continue

        dir_name = f"beta_{beta:.3f}"
        os.makedirs(dir_name, exist_ok=True)

        # Replace beta globally
        new_text = re.sub(
            r'(^[ \t]*beta[ \t]*=).*',
            rf'\1 {beta:.5f}',
            template_text,
            flags=re.MULTILINE
        )

        # Replace beta_prime_input ONLY in theta block
        new_text = replace_in_theta_block(
            new_text,
            "beta_prime_input",
            beta_prime
        )

        # Write file
        run_file = os.path.join(dir_name, "run.in")
        with open(run_file, 'w') as f:
            f.write(new_text)

        # Submit
        os.chdir(dir_name)
        os.system("sbatch ../submit.slurm run.in")
        os.chdir("..")

        time.sleep(0.1)

    print("\nDone.")


if __name__ == "__main__":
    main()