import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_total_heat_flux(base_dir):
    # Search through nested subfolders
    search_pattern = f"{base_dir}/**/*.out.nc"
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Extracting total heat flux data...")

    data_by_kappa = {}

    # Extract data
    for file in nc_files:
        try:
            match = re.search(r'kappa_([0-9.]+)', file)
            if match:
                kappa = float(match.group(1))
            else:
                continue

            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            
            # Grab the total heat flux variable
            if 'hflux_tot' in ds:
                flux_var = ds['hflux_tot']
            else:
                ds.close()
                continue
                
            # Extract the final time step value
            if 't' in flux_var.dims:
                flux_val = float(flux_var.isel(t=-1).values)
            else:
                flux_val = float(flux_var.values)
            
            if kappa not in data_by_kappa:
                data_by_kappa[kappa] = {'ky': [], 'flux': []}
                
            data_by_kappa[kappa]['ky'].append(ky)
            # Use absolute value in case of reversed flux
            data_by_kappa[kappa]['flux'].append(abs(flux_val)) 
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not data_by_kappa:
        print("No valid flux data extracted.")
        return

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_kappas = sorted(data_by_kappa.keys())
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(sorted_kappas)))

    # Plot each elongation
    for idx, kappa in enumerate(sorted_kappas):
        ky_list = data_by_kappa[kappa]['ky']
        flux_list = data_by_kappa[kappa]['flux']
        
        # Sort by ky
        sorted_indices = np.argsort(ky_list)
        ky_arr = np.array(ky_list)[sorted_indices]
        flux_arr = np.array(flux_list)[sorted_indices]

        # NORMALIZATION REMOVED HERE
        # We are plotting the raw flux_arr directly now

        label_str = rf'$\kappa = {kappa}$'
        ax.plot(ky_arr, flux_arr, marker='o', linewidth=2, color=colors[idx], label=label_str)

    # Format the plot
    ax.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=14)
    ax.set_ylabel(r'Total Heat Flux ($Q_{tot}=Q_i+Q_e$)', fontsize=14)
    ax.set_yscale('log')
    
    ax.grid(True, linestyle=':', alpha=0.7)
    ax.legend(title='Elongation', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Optional: If the spread between kappas is massive, uncomment the next line to use a log scale
    # ax.set_yscale('log')
    
    fig.tight_layout()
    
    # Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, "total_flux_spectrum.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan"
    plot_total_heat_flux(target_directory)