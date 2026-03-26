import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_parallel_mode_structure(base_dir, param_type, target_val=None):
    # 1. If a target value wasn't explicitly given, cleanly extract it from the folder name
    if target_val is None:
        # Matches formats like 'tri_0.0' or 'kappa_1.1'
        match = re.search(rf'{param_type}_?([0-9.]+)', base_dir)
        if match:
            target_val = float(match.group(1))
        else:
            print(f"Error: Could not determine '{param_type}' value from folder name '{base_dir}'.")
            return

    print(f"Extracting mode structures from '{base_dir}' for {param_type} = {target_val}...")

    # Search through all nested subfolders
    search_pattern = f"{base_dir}/**/*.out.nc"
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}' or its subfolders.")
        return

    mode_data = {}

    for file in nc_files:
        try:
            
            # Matches formats like 'miller_tri0.0' or 'kappa_1.1'
            match = re.search(rf'{param_type}_?([0-9.]+)', file)  

            if match:
                file_val = float(match.group(1))
                if file_val != target_val:
                    continue  # Skip files that don't match the target value
            else:
                continue # Skip files that don't have the parameter in the name
                
            ds = xr.open_dataset(file)
            
            # Extract ky directly from the file data
            ky = float(ds['ky'].squeeze().values)
            
            # Extract the parallel coordinate (theta) and magnetic shear (shat)
            theta = ds['theta'].squeeze().values
            shat = float(ds['shat'].squeeze().values)

            # Calculate the local radial wavenumber k_x(theta)
            kx_local = shat * ky * theta
            
            # Extract and process phi
            phi_complex = ds['phi'].squeeze()
            phi_real = phi_complex.isel(ri=0).values
            phi_imag = phi_complex.isel(ri=1).values
            
            # Calculate magnitude and normalize
            phi_mag = np.sqrt(phi_real**2 + phi_imag**2)
            phi_mag_normalized = phi_mag / np.max(phi_mag)
            
            mode_data[ky] = {'kx': kx_local, 'phi': phi_mag_normalized} 

            ds.close()
            
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not mode_data:
        print(f"No data found matching {param_type} = {target_val}.")
        return

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sorted_kys = sorted(mode_data.keys())
    colors = plt.cm.plasma(np.linspace(0, 0.9, len(sorted_kys)))

    # Plot each ky line
    for idx, ky in enumerate(sorted_kys):
        kx = mode_data[ky]['kx']
        phi = mode_data[ky]['phi']
        
        label_str = rf'$k_y$ = {ky}'
        ax.plot(kx, phi, color=colors[idx], linewidth=2, label=label_str)

    # Format the Plot
    ax.set_title(f'Mode Structure vs Radial Wavenumber ({param_type} = {target_val})', fontsize=16)
    ax.set_xlabel(r'Local Radial Wavenumber ($k_x = \hat{s} k_y \theta$)', fontsize=14)
    ax.set_ylabel(r'Normalised Amplitude ($|\Phi_N|$)', fontsize=14)

    # Set x-limits from -5pi to 5pi
    ax.set_xlim(-5 * np.pi, 5 * np.pi)
    
    ax.axvline(0, color='black', linestyle='--', alpha=0.5)
    ax.grid(True, linestyle=':', alpha=0.7)
    
    ax.legend(title='Wavenumber', bbox_to_anchor=(1.05, 1), loc='upper left')
    fig.tight_layout()
    
    # Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"mode_structure_{param_type}_{target_val}.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    # Ensure the user provided at least a folder and a parameter type
    if len(sys.argv) < 3:
        print("Usage: python plot_mode_structure.py <folder_name> <param_type> [target_val]")
        print("Example: python plot_mode_structure.py tri_0.0 tri")
        print("Example: python plot_mode_structure.py kappa_1.1 kappa")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    param_type = sys.argv[2]
    
    # Optional 3rd argument if the user wants to specify the value manually
    target_value = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    plot_parallel_mode_structure(target_directory, param_type, target_value)