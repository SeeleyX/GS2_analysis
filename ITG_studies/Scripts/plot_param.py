import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_parameter_scan(base_dir, param_type):
    # Dictionary to automatically map command line arguments to nice plot labels
    PARAM_LABELS = {
        'kappa': (r'$\kappa$', 'Elongation'),
        'kap': (r'$\kappa$', 'Elongation'),
        'tri': (r'$\delta$', 'Triangularity'),
        'eps': (r'$\epsilon$', 'Inverse Aspect Ratio'),
        'shat': (r'$\hat{s}$', 'Magnetic Shear'),
        'tprim': (r'$a/L_T$', 'Temperature Gradient')
    }
    
    # Get the fancy labels, or default to the raw input if it's not in the dictionary
    sym, formal_name = PARAM_LABELS.get(param_type, (param_type, param_type.capitalize()))

    # 1. Find all .out.nc files recursively
    search_pattern = f"{base_dir}/**/*.out.nc"
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Extracting and organizing {formal_name} data...")

    # Dictionary to group our data: {param_value: {'ky': [], 'gamma': [], 'omega': []}}
    data_by_param = {}

    # 2. Extract data and sort it by the scanned parameter
    for file in nc_files:
        try:
            # Look for the parameter and its value in the file path 
            # (Allows for negative numbers like tri_-0.2)
            match = re.search(rf'{param_type}_?([+-]?[0-9]*\.?[0-9]+)', file)
            
            if match:
                param_val = float(match.group(1))
            else:
                continue # Skip files that don't belong to this scan

            ds = xr.open_dataset(file)
            
            ky = float(ds['ky'].squeeze().values)
            
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            if param_val not in data_by_param:
                data_by_param[param_val] = {'ky': [], 'gamma': [], 'omega': []}
                
            data_by_param[param_val]['ky'].append(ky)
            data_by_param[param_val]['gamma'].append(growth_rate)
            data_by_param[param_val]['omega'].append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not data_by_param:
        print(f"Error: Could not find any data matching the parameter '{param_type}'.")
        return

    # 3. Create a figure with two subplots side-by-side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Sort the parameter values so our legend goes in numerical order
    sorted_params = sorted(data_by_param.keys())

    # Generate a smooth color gradient for our lines
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(sorted_params)))

    # 4. Plot the data for each parameter value
    for idx, p_val in enumerate(sorted_params):
        ky_list = data_by_param[p_val]['ky']
        gamma_list = data_by_param[p_val]['gamma']
        omega_list = data_by_param[p_val]['omega']
        
        sorted_indices = np.argsort(ky_list)
        ky_arr = np.array(ky_list)[sorted_indices]
        gamma_arr = np.array(gamma_list)[sorted_indices]
        omega_arr = np.array(omega_list)[sorted_indices]

        label_str = rf'{sym} = {p_val}'
        color = colors[idx]

        # Growth Rate
        ax1.plot(ky_arr, gamma_arr, marker='o', linewidth=2, color=color, label=label_str)
        
        # Real Frequency
        ax2.plot(ky_arr, omega_arr, marker='s', linewidth=2, linestyle='--', color=color, label=label_str)

    # 5. Format Subplot 1 (Growth Rate)
    ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax1.set_ylabel(r'Growth Rate ($\gamma [v_{th}/a]$)', fontsize=12)
    ax1.set_title(f'ITG Growth Rate vs. {formal_name}', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(title=formal_name, fontsize=10)

    # 6. Format Subplot 2 (Real Frequency)
    ax2.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax2.set_ylabel(r'Real Frequency ($\omega [v_{th}/a]$)', fontsize=12)
    ax2.set_title(f'Real Frequency vs. {formal_name}', fontsize=14)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.axhline(0, color='black', linewidth=1, linestyle=':')
    ax2.legend(title=formal_name, fontsize=10)

    fig.tight_layout()
    
    # 7. Save to the Figures folder dynamically
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{param_type}_scan_ky_spectrum.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plots successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python plot_parameter_scan.py <folder_name> <param_type>")
        print("Example: python plot_parameter_scan.py Inputs/ITG_kyscan tri")
        print("Example: python plot_parameter_scan.py Inputs/ITG_kyscan kappa")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    param_type = sys.argv[2]
    
    plot_parameter_scan(target_directory, param_type)