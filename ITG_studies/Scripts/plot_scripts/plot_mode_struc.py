import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_parallel_mode_structure(base_dir, target_kappa=1.0):
    # Search through all nested subfolders
    search_pattern = f"{base_dir}/**/*.out.nc"
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}' or its subfolders.")
        return

    print(f"Extracting mode structures for kappa = {target_kappa}...")

    mode_data = {}

    for file in nc_files:
        try:
            # Check the file path for 'kappa_X.X'
            match = re.search(r'kappa_([0-9.]+)', file)
            
            if match:
                kappa = float(match.group(1))
                if kappa != target_kappa:
                    continue
            else:
                continue
                
            ds = xr.open_dataset(file)
            
            # Extract ky directly from the file data
            ky = float(ds['ky'].squeeze().values)
            
            # Extract the parallel coordinate (theta)
            theta = ds['theta'].squeeze().values
            
            # THE FIX: Removed .isel(t=-1) because phi only has spatial dimensions here
            phi_complex = ds['phi'].squeeze()
            phi_real = phi_complex.isel(ri=0).values
            phi_imag = phi_complex.isel(ri=1).values
            
            # Calculate magnitude and normalize
            phi_mag = np.sqrt(phi_real**2 + phi_imag**2)
            phi_mag_normalized = phi_mag / np.max(phi_mag)
            
            mode_data[ky] = {'theta': theta, 'phi': phi_mag_normalized}
            
            ds.close()
            
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not mode_data:
        print(f"No data found for kappa = {target_kappa}.")
        return

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sorted_kys = sorted(mode_data.keys())
    colors = plt.cm.plasma(np.linspace(0, 0.9, len(sorted_kys)))

    # Plot each ky line
    for idx, ky in enumerate(sorted_kys):
        theta = mode_data[ky]['theta']
        phi = mode_data[ky]['phi']
        
        label_str = rf'$k_y$ = {ky}'
        ax.plot(theta, phi, color=colors[idx], linewidth=2, label=label_str)

    # Format the Plot
    ax.set_xlabel(r'Poloidal Angle ($\theta$)', fontsize=14)
    ax.set_ylabel(r'Normalised Amplitude ($|\Phi_N|$)', fontsize=14)
    
    ax.axvline(0, color='black', linestyle='--', alpha=0.5)
    ax.grid(True, linestyle=':', alpha=0.7)
    
    ax.legend(title='Wavenumber', bbox_to_anchor=(1.05, 1), loc='upper left')
    fig.tight_layout()
    
    # Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"mode_structure_kappa_{target_kappa}.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan"
    target_kappa = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    plot_parallel_mode_structure(target_directory, target_kappa)