# GS2_analysis
A personal repository for codes and documentation relating to the analysis and setup of the gyrokinetic code GS2.


Initialising GS2 on the Viking cluster requires running tests built into GS2 
**SSH into the Viking cluster**
```bash
   ssh your_username@viking.york.ac.uk
```
**Load the base Python module**
```bash
   module load Python/3.11.3-GCCcore-12.3.0
```

**Create the virtual environment**
```bash
   python3 -m venv ~/GS2env
```

**Activate the environment**
```bash
   source ~/GS2env/bin/activate
```

**Install Python dependencies**
```bash
   pip install numpy netCDF4 xarray matplotlib f90nml pytest
```

**Navigate to the GS2 source directory**
```bash
   cd ~/software/src/gs2
```

**Load the GS2 toolchain**
```bash
   module purge
   module load GCC OpenMPI netCDF-Fortran FFTW
```

**Set environment variables**
```bash
    export GK_SYSTEM=viking
    export MAKEFLAGS="-IMakefiles"
```

**Run all tests**

This hangs at the 'namelists_collection/.' test. It also hangs on other tests when running tests individually. Believe it is tests that involve the PyTest library. 

```bash
    make tests
```

**Run linear physics tests**
```bash
    make linear_tests NTESTPROCS=6 TEST_LEVEL=2
```

**Run nonlinear physics tests**
```bash
    make nonlinear_tests NTESTPROCS=6 TEST_LEVEL=2
```

To run code more computationally intensive than these tests on Viking, one must use the compute nodes. To access one of these nodes, you must request access and enter a queue using the following command:

**Request an interactive compute node**
```bash
   srun --nodes=1 --ntasks=8 --time=01:00:00 --pty /bin/bash
```
Where --ntasks>1 to run GS2 with MPI. The time one plans to spend on the node can be altered, too, using the --time keyword. 

## Adding files to this GitHub page 
Once cloning this file to where you are working on it, setting up an SSH authentication key, one can edit this page. 

Add the file(s) using,
```bash
   git add example.py
```

Commit the git, making reference to what you are doing,
```bash
   git commit -m "Additional example script, does this example function." 
```
Push, to a certain branch, can merge branches later for merging straight to the original branch:
```bash
   git push origin main
```

## Adding a bash command

In the directory you want to add the .sh file. Type into the command prompt
```bash
   cat << 'EOF' > example.sh
 ```
Following this, one can create the .sh file, and then complete the file by typing into the prompt:
```bash
   EOF
```
To run the bash command, first you initiate the file using,
```bash
   chmod +x example.sh
```
Then you can run using the following (additional files will be inputs for the file):
```bash
   ./example.sh example.in
```

