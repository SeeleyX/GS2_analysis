#!/bin/bash
#SBATCH --job-name=GS2_ky_scan
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-%j.out

# ==========================================
# 1. ENVIRONMENT SETUP
# ==========================================
module purge
module load Python/3.11.3-GCCcore-12.3.0
module load GCC OpenMPI netCDF-Fortran FFTW

export LD_LIBRARY_PATH=$EBROOTNETCDFMINFORTRAN/lib:$EBROOTNETCDF/lib:$LD_LIBRARY_PATH
export GK_SYSTEM=viking
export MAKEFLAGS="-IMakefiles"
export PATH="$HOME/software/src/gs2/bin:$PATH"

source ~/GS2env/bin/activate

# ==========================================
# 2. EXECUTE THE SIMULATION
# ==========================================
ulimit -s unlimited
export OMPI_MCA_btl=self,vader,tcp

INPUT_FILE=$1
echo "Starting GS2 execution on $SLURM_NTASKS cores with input: $INPUT_FILE"

# Run GS2
srun -n $SLURM_NTASKS "$HOME/software/src/gs2/bin/gs2" "$INPUT_FILE"
GS2_EXIT_CODE=$?

if [ $GS2_EXIT_CODE -ne 0 ]; then
    echo "GS2 exited with code $GS2_EXIT_CODE -- exiting."
    deactivate
    exit $GS2_EXIT_CODE
fi

echo "GS2 completed successfully."
deactivate
exit 0
