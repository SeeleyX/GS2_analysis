import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_ky_spectrum(base_dir, num_avg_steps=10):
    """
    Parses a directory of ky scans, time-averages the final few timesteps,
    and plots growth rate and real frequency on separate, stacked subplots.
    """
    # Extract rho value for the title/filename
    match = re.search(r'rho_([0-9.]+)', base_dir)
    rho_val = match.group(1) if match else "0.96"

    # 1. Find all .out.nc files in the subdirectories
    search_pattern = os.path.join(base_dir, "**", "*.out.nc")
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Extracting data (averaging last {num_avg_steps} steps)...")

    ky_list = []
    gamma_list = []
    omega_list = []

    # 2. Extract and time-average data from each file
    for file in nc_files:
        try:
            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            
            # Time-averaging window
            omega_window = ds['omega'].isel(t=slice(-num_avg_steps, None))
            omega_complex = omega_window.mean(dim='t')
            
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            ky_list.append(ky)
            gamma_list.append(growth_rate)
            omega_list.append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not ky_list:
        print("Error: No valid data could be parsed.")
        return

    # 3. Sort arrays by wavenumber
    sorted_indices = np.argsort(ky_list)
    ky_arr = np.array(ky_list)[sorted_indices]
    gamma_arr = np.array(gamma_list)[sorted_indices]
    omega_arr = np.array(omega_list)[sorted_indices]

    # 4. Create a 2-row subplot configuration sharing the X-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    # --- Top Subplot: Growth Rate (gamma) ---
    # Plotted with a cyan line and filled circle markers
    ax1.plot(ky_arr, gamma_arr, color='c', marker='o', markersize=6, linewidth=2)
    ax1.set_ylabel(r'Growth Rate ($\gamma [v_{th}/a]$)', fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.axhline(0, color='black', linewidth=0.8, linestyle=':')

    # ax1.set_yscale('log')

    # --- Bottom Subplot: Real Frequency (omega) ---
    ax2.plot(ky_arr, omega_arr, color='tab:blue', marker='o', markersize=6, linewidth=2, linestyle='--')
    ax2.set_ylabel(r'Real Frequency ($\omega [v_{th}/a]$)', fontsize=11)
    ax2.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=11)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.axhline(0, color='black', linewidth=0.8, linestyle=':')

    # Apply log scale to the shared x-axis
    ax2.set_xscale('log')

    plt.suptitle(rf'Linear Wavenumber Spectrum ($\rho = {rho_val}$)', fontsize=13, y=0.98)
    fig.tight_layout()
    
    # 5. Save and Show Output
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) 
    save_path = os.path.join(output_dir, f"ky-scan_rho_{rho_val}_subplots.png")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "rho_0.96"
    plot_ky_spectrum(target_directory, num_avg_steps=10)