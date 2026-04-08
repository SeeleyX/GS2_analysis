# Bash Command 'read me' file

Inside the ```gs2_venv``` enviroment, we can run the following bash commands and recieve different commands.

## Commands that run GS2

- ```run_gs2``` is a command that will run using a simple input file. It will produce an output folder with all attached filed, that is currently named ```miller_kap${KAP_VAL}_ky${KY_VAL}```, this should be altered to your needs. Running one set of input parameters, this command is run using:
```bash
./run_gs2.sh example.in
```
Where the values inside ```example.in``` give the folder name. Must insure than the inputs in the folder name are listed in the input file.

- ```scan_ky``` can scan over the ```aky``` parameter in the input file. This command runs the previous command in a loop until the desired $k_y$ parameter space has been scanned. 