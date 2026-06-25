import os
import glob
import re
import time

def main():
    # 1. Get the absolute path to your slurm script so it works from ANY depth
    slurm_script = os.path.abspath("submit.slurm")
    
    if not os.path.exists(slurm_script):
        print(f"Error: Could not find {slurm_script}. Make sure you run this from the directory containing submit.slurm.")
        return

    # 2. Use recursive globbing to find every run.in file, no matter how deep
    print("Searching for nested run.in files...")
    run_files = glob.glob("**/run.in", recursive=True)
    
    if not run_files:
        print("No run.in files found in any subdirectories!")
        return

    # Save our starting directory so we can always return to it safely
    original_dir = os.getcwd()

    for run_file in sorted(run_files):
        
        # Read the input file
        with open(run_file, 'r') as f:
            content = f.read()
            
        # 1. Update ginit_option to "restart"
        content = re.sub(r'ginit_option\s*=\s*".*"', 'ginit_option = "restart"', content, flags=re.IGNORECASE)
        content = re.sub(r"ginit_option\s*=\s*'.*'", 'ginit_option = "restart"', content, flags=re.IGNORECASE)
        
        # 2. Update delt_option to "check_restart"
        content = re.sub(r'delt_option\s*=\s*".*"', 'delt_option = "check_restart"', content, flags=re.IGNORECASE)
        content = re.sub(r"delt_option\s*=\s*'.*'", 'delt_option = "check_restart"', content, flags=re.IGNORECASE)
        
        # 3. Handle append_old
        if re.search(r'append_old\s*=', content, re.IGNORECASE):
            content = re.sub(r'append_old\s*=\s*\.\w+\.', 'append_old = .true.', content, flags=re.IGNORECASE)
        else:
            content = re.sub(r'(&gs2_diagnostics_knobs)', r'\1\n  append_old = .true.', content, flags=re.IGNORECASE)
            
        # Write the updated content back to the file
        with open(run_file, 'w') as f:
            f.write(content)
            
        # Extract just the folder path from the file path
        target_dir = os.path.dirname(run_file)
        print(f"Updated flags in {run_file}. Resubmitting...")
        
        # Move into the specific nested directory, resubmit using absolute path, and move back
        os.chdir(target_dir)
        os.system(f"sbatch {slurm_script} run.in")
        os.chdir(original_dir)
        
        # Pause briefly to avoid hammering the Slurm scheduler
        time.sleep(0.1)

    print("\nAll nested jobs successfully updated and resubmitted for restart!")

if __name__ == "__main__":
    main()
