import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_elongation_scan(base_dir):
    # 1. Find all .out.nc files in the subdirectories
    search_pattern = f"{base_dir}/*/*.out.nc"
    nc_files = glob.glob(search_pattern)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Extracting and organizing data...")

    # Dictionary to group our data by kappa: 
    # {kappa_value: {'ky': [], 'gamma': [], 'omega': []}}
    data_by_kappa = {}

    # 2. Extract data and sort it by elongation
    for file in nc_files:
        try:
            # Extract kappa from the folder name using regular expressions
            folder_name = os.path.basename(os.path.dirname(file))
            match = re.search(r'kap([0-9.]+)', folder_name)
            
            if match:
                kappa = float(match.group(1))
            else:
                print(f"Warning: Could not find 'kap' value in {folder_name}. Skipping.")
                continue

            ds = xr.open_dataset(file)
            
            # Extract ky from NetCDF
            ky = float(ds['ky'].squeeze().values)
            
            # Extract complex frequency at the final time step
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            # Initialize the dictionary for this kappa if it doesn't exist yet
            if kappa not in data_by_kappa:
                data_by_kappa[kappa] = {'ky': [], 'gamma': [], 'omega': []}
                
            # Store the data
            data_by_kappa[kappa]['ky'].append(ky)
            data_by_kappa[kappa]['gamma'].append(growth_rate)
            data_by_kappa[kappa]['omega'].append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    # 3. Create a figure with two subplots side-by-side (1 row, 2 columns)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Sort the kappas so our legend goes in numerical order
    sorted_kappas = sorted(data_by_kappa.keys())

    # Generate a smooth color gradient for our lines
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(sorted_kappas)))

    # 4. Plot the data for each elongation
    for idx, kappa in enumerate(sorted_kappas):
        # Grab the raw lists
        ky_list = data_by_kappa[kappa]['ky']
        gamma_list = data_by_kappa[kappa]['gamma']
        omega_list = data_by_kappa[kappa]['omega']
        
        # Sort them so the plot lines connect left-to-right smoothly
        sorted_indices = np.argsort(ky_list)
        ky_arr = np.array(ky_list)[sorted_indices]
        gamma_arr = np.array(gamma_list)[sorted_indices]
        omega_arr = np.array(omega_list)[sorted_indices]

        # Define line label and color
        label_str = rf'$\kappa = {kappa}$'
        color = colors[idx]

        # Subplot 1: Growth Rate
        ax1.plot(ky_arr, gamma_arr, marker='o', linewidth=2, color=color, label=label_str)
        
        # Subplot 2: Real Frequency
        ax2.plot(ky_arr, omega_arr, marker='s', linewidth=2, linestyle='--', color=color, label=label_str)

    # 5. Format Subplot 1 (Growth Rate)
    ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax1.set_ylabel(r'Growth Rate ($\gamma$)', fontsize=12)
    ax1.set_title('ITG Growth Rate vs. Elongation', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(title='Elongation', fontsize=10)

    # 6. Format Subplot 2 (Real Frequency)
    ax2.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax2.set_ylabel(r'Real Frequency ($\omega$)', fontsize=12)
    ax2.set_title('Real Frequency vs. Elongation', fontsize=14)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.axhline(0, color='black', linewidth=1, linestyle=':')
    ax2.legend(title='Elongation', fontsize=10)

    fig.tight_layout()
    
    # 7. Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, "elongation_ky_scan.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plots successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan"
    plot_elongation_scan(target_directory)