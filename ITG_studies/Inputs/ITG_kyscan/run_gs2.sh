#!/bin/bash

# 1. Define the input file from the first argument
INPUT_FILE=$1

# 2. Check if a file was provided
if [ -z "$INPUT_FILE" ]; then
    echo "Usage: ./run_gs2.sh <input_file.in>"
    exit 1
fi

# 3. Extract the aky value using grep and awk
KY_VAL=$(grep -i "^[[:space:]]*aky" $INPUT_FILE | awk -F'=' '{print $2}' | tr -d ' ')
TRI_VAL=$(grep -i "^[[:space:]]*tri[[:space:]]*=" $INPUT_FILE | awk -F'=' '{print $2}' | tr -d ' ')
# 4. Define the target directory name
DIR_NAME="miller_tri${TRI_VAL}_ky${KY_VAL}"
# 5. Create the directory (if it doesn't already exist)
mkdir -p $DIR_NAME

# 6. Copy the input file into the directory
cp $INPUT_FILE $DIR_NAME/

# 7. Move into the directory and execute GS2
echo "Starting GS2 run in directory: $DIR_NAME with aky = $KY_VAL"
cd $DIR_NAME
mpirun -n 4 /Users/williamseeley/gyrokinetics/gs2/bin/gs2 $(basename $INPUT_FILE)

# 8. Return to the original directory when finished
cd ..
echo "Run complete. Outputs saved in $DIR_NAME/"
