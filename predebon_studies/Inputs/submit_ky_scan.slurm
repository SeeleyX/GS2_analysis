#!/bin/bash
#SBATCH --job-name=GS2_ky_scan
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --output=slurm-%A_%a.out   # %A = job ID, %a = array index
#SBATCH --array=0-4                # one job per ky value (0 to N-1)

module purge
module load Python/3.11.3-GCCcore-12.3.0
module load GCC OpenMPI netCDF-Fortran FFTW

export LD_LIBRARY_PATH=$EBROOTNETCDFMINFORTRAN/lib:$EBROOTNETCDF/lib:$LD_LIBRARY_PATH
export GK_SYSTEM=viking
export MAKEFLAGS="-IMakefiles"
export PATH="$HOME/software/src/gs2/bin:$PATH"

source ~/GS2env/bin/activate
ulimit -s unlimited
export OMPI_MCA_btl=self,vader,tcp

cd $SLURM_SUBMIT_DIR

# ── Define your ky values here ─────────────────────────────────────────────────
KY_VALUES=(0.03 0.1 0.3 1.0)

# SLURM_ARRAY_TASK_ID is automatically set to 0, 1, 2... by SLURM
KY=${KY_VALUES[$SLURM_ARRAY_TASK_ID]}

INPUT_FILE="jet84793_rho0.96_GS2.in"
DIR_NAME="ky_${KY}"
RUN_FILE="jet84793_rho0.96_GS2_ky${KY}.in"

echo "Array task $SLURM_ARRAY_TASK_ID: running ky = $KY"

# Create directory, patch ky, and run
mkdir -p "$DIR_NAME"
sed "s/^\([[:space:]]*aky[[:space:]]*=\).*/\1 ${KY}/" \
    "$INPUT_FILE" > "$DIR_NAME/$RUN_FILE"

cd "$DIR_NAME"
srun -n $SLURM_NTASKS "$HOME/software/src/gs2/bin/gs2" "$RUN_FILE"

deactivate