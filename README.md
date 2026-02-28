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

**Request an interactive compute node**
```bash
   srun --nodes=1 --ntasks=8 --time=01:00:00 --pty /bin/bash
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

**Reactivate the Python environment**
```bash
   source ~/GS2env/bin/activate
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
