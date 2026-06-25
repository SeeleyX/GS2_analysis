import os
import re
import sys
import time

def replace_aky(text, new_ky):
    """Finds the &kt_grids_single_parameters block and updates or inserts aky."""
    pattern = r'(&kt_grids_single_parameters.*?/)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Could not find &kt_grids_single_parameters block in the input file.")

    block = match.group(1)
    if re.search(r'^[ \t]*aky[ \t]*=', block, re.MULTILINE):
        new_block = re.sub(
            r'(^[ \t]*aky[ \t]*=).*',
            rf'\1 {new_ky:.4f}',
            block,
            flags=re.MULTILINE
        )
    else:
        new_block = block.rstrip("/ \n") + f"\n  aky = {new_ky:.4f}\n/"
    return text.replace(block, new_block)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scan_ky.py <template_file> [run]")
        sys.exit(1)

    template_file = sys.argv[1]
    run_mode = len(sys.argv) > 2 and sys.argv[2].lower() == "run"

    if not os.path.exists(template_file):
        print(f"Error: {template_file} not found.")
        sys.exit(1)

    with open(template_file, 'r') as f:
        template_text = f.read()

    # ── Define your ky array here ─────────────────────────────────────────────
    ky_values = [0.05,0.1,0.2,0.3,1.0,1.35, 1.6, 1.75, 1.9, 2.5, 2.9, 3.45, 4.7, 4.9, 5.7, 6.85, 7.85, 30, 75]
    # ──────────────────────────────────────────────────────────────────────────

    parent_dir = "rhot_0.96"
    
    if run_mode:
        print(f"Running LIVE scan. Output parent directory: {parent_dir}\n")
        os.makedirs(parent_dir, exist_ok=True)
    else:
        print(f"DRY RUN: Checking modifications for parent directory '{parent_dir}'\n")

    for ky in ky_values:
        print(f"Preparing configuration for ky = {ky:.3f}")

        if not run_mode:
            continue

        # Create localized subdirectory inside the parent folder
        sub_dir_name = f"ky_{ky:.2f}"
        full_path = os.path.join(parent_dir, sub_dir_name)
        os.makedirs(full_path, exist_ok=True)

        # Modify the input text to update aky
        new_text = replace_with_ky = replace_aky(template_text, ky)

        # Write out the target run file
        run_file = os.path.join(full_path, "run.in")
        with open(run_file, 'w') as f:
            f.write(new_text)

        # Drop down into the directory, submit the slurm script, and bounce back up
        os.chdir(full_path)
        # Note: We use ../../ because we are now two levels deep (ky_sweep_data/ky_0.10/)
        os.system("sbatch ../../submit.slurm run.in")
        os.chdir("../..") 

        time.sleep(0.1)

    if not run_mode:
        print("\nTo launch the live cluster jobs, append 'run' to your command:")
        print(f"python3 scan_ky.py {template_file} run")
    else:
        print(f"\nDone. Successfully submitted {len(ky_values)} jobs.")

if __name__ == "__main__":
    main()