#!/bin/bash

BASE_FILE=$1

# Check if the base file exists
if [ ! -f "$BASE_FILE" ]; then
    echo "Error: $BASE_FILE not found!"
    exit 1
fi

# Loop from 0.1 to 1.0 in steps of 0.1
for ky in $(seq 2.0 1.0 70.0); do
    
    echo "======================================="
    echo " Starting automated run for aky = $ky"
    echo "======================================="
    
    TEMP_FILE="temp_ky_${ky}.in"
    
    # Use sed to find the line starting with 'aky' and replace it
    # s/old/new/ is the substitution command
    sed "s/^[[:space:]]*aky[[:space:]]*=.*/  aky = $ky/" "$BASE_FILE" > "$TEMP_FILE"
    
    # Execute your existing run script
    ./run_gs2.sh "$TEMP_FILE"
    
    # Remove the temporary input file to keep the directory clean
    rm "$TEMP_FILE"

done

echo "--- Full Parameter Scan Complete! ---"
