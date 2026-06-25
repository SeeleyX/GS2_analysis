# Script 'read me' file

Files included within this directory will be run using the ```gs2_venv``` virtual environment. More detailed instructions will be given to specific more complicated scripts; however, most are ran with the simple instruction of run this script using this directory:
```bash
python Scripts/example.py Inputs/Example_directory
```

When plotting the mode structure against the poloidal angle, we use ```plot_mode_struc.py```. For this plot you must suggest which value of $\kappa$ you are using (give an argument in the bash command).
```bash
python Scripts/plot_mode_struc.py Inputs/ITG_kyscan 2.2
```
Where ```2.2``` is the value of elongation.

Plotting the total flux as a function of $k_y$ will automatically plot every value of elongation in the given directory and runs as seen above. 
```bash
python Scripts/plot_flux_ratio.py Inputs/ITG_kyscan
```

Plotting ```plot_mode.py``` and ```plot_single_spectrum.py``` you need to specify what type of parameter is being varied. For example for a single $k_y$ spectrum plot of a triangulation dataset you must type:
```bash
python Scripts/plot_ky_spectrum.py Inputs/ITG_kyscan/tri_0.0 tri
```
Where ```tri``` defines the parameter using the GS2 input parameter. 