#!/bin/bash

# Usage: ./run_gs2.sh <input_file.in> <ky1> <ky2> <ky3> ...
# Example: ./run_gs2.sh jet84793_rho0.96_GS2.in 0.1 0.2 0.3 0.5 0.7 1.0

INPUT_FILE=$1
shift                     # shift so $@ now contains just the ky values
KY_VALUES=("$@")

# ── Checks ────────────────────────────────────────────────────────────────────
if [ -z "$INPUT_FILE" ]; then
    echo "Usage: ./run_gs2.sh <input_file.in> <ky1> <ky2> ..."
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: input file '$INPUT_FILE' not found"
    exit 1
fi

if [ ${#KY_VALUES[@]} -eq 0 ]; then
    echo "Error: no ky values provided"
    echo "Usage: ./run_gs2.sh <input_file.in> <ky1> <ky2> ..."
    exit 1
fi

BASE_NAME=$(basename "$INPUT_FILE" .in)   # e.g. jet84793_rho0.96_GS2

# ── Loop over ky values ───────────────────────────────────────────────────────
for KY in "${KY_VALUES[@]}"; do

    DIR_NAME="ky_${KY}"
    RUN_FILE="${BASE_NAME}_ky${KY}.in"

    echo "──────────────────────────────────────────"
    echo "Preparing run: ky = $KY  →  $DIR_NAME/"

    # Create run directory
    mkdir -p "$DIR_NAME"

    # Copy input file and replace aky value in the copy
    sed "s/^\([[:space:]]*aky[[:space:]]*=\).*/\1 ${KY}/" \
        "$INPUT_FILE" > "$DIR_NAME/$RUN_FILE"

    echo "  Written $DIR_NAME/$RUN_FILE with aky = $KY"

    # Run GS2 inside the directory
    cd "$DIR_NAME" || exit
    echo "  Launching GS2..."
    srun -n $SLURM_NTASKS "$HOME/software/src/gs2/bin/gs2" "$RUN_FILE"
    cd ..

    echo "  Done. Outputs in $DIR_NAME/"

done

echo "══════════════════════════════════════════"
echo "All ky runs complete."