import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_ky_spectrum(base_dir):
    match = re.search(r'kappa_([0-9.]+)', base_dir)
    if match:
        kappa_val = match.group(1)
    else:
        kappa_val = "unknown"

    # 1. Find all .out.nc files in the subdirectories
    search_pattern = f"{base_dir}/*/*.out.nc"
    nc_files = glob.glob(search_pattern)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files in {base_dir}. Extracting data...")

    ky_list = []
    gamma_list = []
    omega_list = []

    # 2. Extract data from each file
    for file in nc_files:
        try:
            ds = xr.open_dataset(file)
            
            # Extract ky directly from the NetCDF coordinate
            ky = float(ds['ky'].squeeze().values)
            
            # Extract complex frequency at the final time step
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            ky_list.append(ky)
            gamma_list.append(growth_rate)
            omega_list.append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    # 3. Sort the lists so the plot lines connect correctly
    sorted_indices = np.argsort(ky_list)
    ky_arr = np.array(ky_list)[sorted_indices]
    gamma_arr = np.array(gamma_list)[sorted_indices]
    omega_arr = np.array(omega_list)[sorted_indices]

    # 4. Create the dual-axis plot
    fig, ax1 = plt.subplots(figsize=(9, 6))

    # Axis 1: Growth Rate (red)
    color1 = 'tab:red'
    ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax1.set_ylabel(r'Growth Rate ($\gamma$)', color=color1, fontsize=12)
    ax1.plot(ky_arr, gamma_arr, marker='o', color=color1, linewidth=2, label=r'$\gamma$')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Axis 2: Real Frequency (blue)
    ax2 = ax1.twinx()  
    color2 = 'tab:blue'
    ax2.set_ylabel(r'Real Frequency ($\omega$)', color=color2, fontsize=12)
    ax2.plot(ky_arr, omega_arr, marker='s', color=color2, linewidth=2, linestyle='--', label=r'$\omega$')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Add a horizontal line at y=0
    ax2.axhline(0, color='black', linewidth=1, linestyle=':')

    # Title and Layout
    plt.title(rf'Miller ITG Growth Rate Spectrum ($\kappa = {kappa_val}$)', fontsize=14)
    fig.tight_layout()
    
    # 5. Handle Directory Creation and Saving
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) # Creates the folder if it doesn't exist
    
    save_path = os.path.join(output_dir, f"miller_ky-scan_kappa_{kappa_val}.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan/kappa_1.0"
    plot_ky_spectrum(target_directory)