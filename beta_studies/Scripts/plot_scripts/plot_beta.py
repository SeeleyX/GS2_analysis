import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob

def get_eps_from_in_file(directory):
    """Scans .in files in the directory to find the 'eps' parameter."""
    in_files = glob.glob(os.path.join(directory, "*.in"))
    for fpath in in_files:
        try:
            with open(fpath, 'r') as f:
                for line in f:
                    # Strip out Fortran comments starting with '!'
                    clean_line = line.split('!')[0]
                    if '=' in clean_line:
                        key, val = clean_line.split('=', 1)
                        if key.strip().lower() == 'eps':
                            # Handle Fortran double precision format (e.g., 1.0D-3 -> 1.0e-3)
                            val_clean = val.strip().replace('d', 'e').replace('D', 'e')
                            return float(val_clean)
        except Exception as e:
            pass # Move to the next file if there's a read error
    return None

def plot_beta_scan(target_dir):
    search_pattern = os.path.join(target_dir, "beta_*", "*.out.nc")
    nc_filepaths = glob.glob(search_pattern)
    
    if not nc_filepaths:
        print(f"Error: No .out.nc files found matching '{search_pattern}'")
        return

    print(f"Found {len(nc_filepaths)} files. Extracting data...")

    betas = []
    gammas = []
    omegas = []
    
    for nc_filepath in nc_filepaths:
        directory = os.path.dirname(nc_filepath)
        try:
            ds = xr.open_dataset(nc_filepath)
            
            # 1. Extract the beta value and convert to PERCENTAGE
            try:
                beta_val = float(ds['beta'].values)
            except KeyError:
                folder_name = os.path.basename(directory)
                beta_val = float(folder_name.replace('beta_', ''))
            
            beta_pct = beta_val * 100.0  
            
            # 2. Extract eps from the .in file to get R/a
            eps = get_eps_from_in_file(directory)
            if eps is not None and eps > 0:
                R_over_a = 1.0 / eps
            else:
                R_over_a = 1 / 0.17  # Fallback just in case
                print(f"  -> Warning: 'eps' not found in .in files inside {directory}. Assuming R/a = 3.0")

            # 3. Extract growth rate and frequency arrays at final time step
            gamma_array = ds['omega'].isel(t=-1, kx=0, ri=1).values
            omega_array = ds['omega'].isel(t=-1, kx=0, ri=0).values
            
            # 4. Find the max and normalize to Major Radius (R)
            max_idx = np.argmax(gamma_array)
            max_gamma = gamma_array[max_idx] * R_over_a
            corr_omega = omega_array[max_idx] * R_over_a
            
            betas.append(beta_pct)
            gammas.append(max_gamma)
            omegas.append(corr_omega)
            
            ds.close()
            
        except Exception as e:
            print(f"  -> Skipping {nc_filepath} due to error: {e}")

    if not betas:
        print("No valid data could be extracted.")
        return

    # Sort the data by beta value so the line plot connects sequentially
    sorted_indices = np.argsort(betas)
    betas = np.array(betas)[sorted_indices]
    gammas = np.array(gammas)[sorted_indices]
    omegas = np.array(omegas)[sorted_indices]

    # Create the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharex=True)
    
    # Plot Growth Rate vs Beta
    ax1.plot(betas, gammas, marker='s', linestyle='--', linewidth=1, color='blue', label='Max Growth Rate')
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')  
    ax1.set_title(r'$ R/L_n = 0.7, k_y\rho_i = 0.4 $')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot Real Frequency vs Beta
    ax2.plot(betas, omegas, marker='s', linestyle='--', linewidth=1, color='blue', label='Real Freq (at max $\\gamma$)')
    ax2.set_xlabel(r'$\beta$ (%)') 
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')  
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Check if the user provided the directory argument
    if len(sys.argv) != 2:
        print("Usage: python plot_beta.py <directory_name>")
        print("Example: python plot_beta.py high_nperiod")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    
    # Ensure the directory exists before trying to plot
    if not os.path.isdir(target_directory):
        print(f"Error: The directory '{target_directory}' does not exist.")
        sys.exit(1)
        
    plot_beta_scan(target_directory)