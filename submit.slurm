#!/bin/bash
#SBATCH --job-name=GS2_beta_scan
#SBATCH --time=4:00:00          
#SBATCH --nodes=1                
#SBATCH --ntasks-per-node=32     
#SBATCH --mem=10G                
#SBATCH --output=slurm-%j.out    

# ==========================================
# 1. ENVIRONMENT SETUP
# ==========================================
# Purge everything first to start with a clean slate
module purge

# Load the Python module needed for your venv
module load Python/3.11.3-GCCcore-12.3.0

# Load the GS2 toolchain modules
module load GCC OpenMPI netCDF-Fortran FFTW

# ==========================================
# 2. SET VARIABLES & ACTIVATE VENV
# ==========================================
# Set GS2 specific environment variables
export GK_SYSTEM=viking
export MAKEFLAGS="-IMakefiles"
export PATH="$HOME/software/src/gs2/bin:$PATH"

# Activate your pre-existing Python environment
source ~/GS2env/bin/activate

# ==========================================
# 3. EXECUTE THE JOB
# ==========================================
# Run your GS2 script 
# (Make sure you submit this from the directory containing beta_studies)
./beta_studies/Inputs/run_gs2.sh beta_studies/Inputs/ASDEX_beta_high_nperiod.in

# Safely close the environment when the job finishes
deactivate
