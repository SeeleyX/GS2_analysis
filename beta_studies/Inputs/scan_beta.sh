#!/bin/bash

BASE_FILE=$1

# Check if the base file exists
if [ ! -f "$BASE_FILE" ]; then
    echo "Error: $BASE_FILE not found!"
    exit 1
fi

# Loop from 0.0088 (low beta) to 0.0148 (high beta) in steps of 0.001
for beta in $(seq 0.0088 0.001 0.0148); do
    
    echo "======================================="
    echo " Starting automated run for beta = $beta"
    echo "======================================="
    
    TEMP_FILE="temp_beta_${beta}.in"
    
    # Use sed to find the line starting with 'beta' and replace it
    sed "s/^[[:space:]]*beta[[:space:]]*=.*/  beta = $beta/" "$BASE_FILE" > "$TEMP_FILE"
    
    # Execute your existing run script
    ./run_gs2.sh "$TEMP_FILE"
    
    # Remove the temporary input file to keep the directory clean
    rm "$TEMP_FILE"

done

echo "--- Full Parameter Scan Complete! ---"