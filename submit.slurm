#!/bin/bash
#SBATCH --job-name=GS2_beta_scan
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --mem=128G
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
export LD_LIBRARY_PATH=$EBROOTNETCDFMINFORTRAN/lib:$EBROOTNETCDF/lib:$LD_LIBRARY_PATH

export GK_SYSTEM=viking
export MAKEFLAGS="-IMakefiles"
export PATH="$HOME/software/src/gs2/bin:$PATH"

# Activate your pre-existing Python environment
source ~/GS2env/bin/activate

# ==========================================
# 3. EXECUTE THE JOB
# ==========================================
# CRITICAL: Remove memory stack limits. 
# GS2 often crashes or hangs without this when running in parallel.
ulimit -s unlimited

# Set a hint for OpenMPI to use stable communication paths
export OMPI_MCA_btl=self,vader,tcp

echo "Starting GS2 with mpirun..."

# Use mpirun to launch the script. 
./beta_studies/Inputs/run_gs2.sh beta_studies/Inputs/ASDEX_beta_high_nperiod.in

# Safely close the environment
deactivate
