#%%
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot_real_imag_components(nc_filepaths, labels=None, target_ky=None): 
    valid_files = [f for f in nc_filepaths if os.path.exists(f)]
    n_files = len(valid_files)
    
    if n_files == 0:
        print("Error: No valid files found.")
        return

    # Create subplots dynamically based on the number of files
    fig, axes = plt.subplots(n_files, 1, figsize=(10, 4 * n_files), sharex=True)
    
    if n_files == 1:
        axes = [axes]

    for i, (ax, nc_filepath) in enumerate(zip(axes, valid_files)):
        print(f"Processing: {nc_filepath}")
        ds = xr.open_dataset(nc_filepath)
        
        # 1. Determine which k_y index to plot
        if target_ky is not None:
            # Find the k_y closest to the user's target
            ky_vals = ds['ky'].values
            plot_idx = np.abs(ky_vals - target_ky).argmin()
            plot_ky_val = ky_vals[plot_idx]
            print(f"  -> Target ky={target_ky} requested. Closest match found: ky={plot_ky_val:.4f}")
        else:
            # Default to the most unstable k_y mode
            gamma = ds['omega'].isel(t=-1, kx=0, ri=1).values
            plot_idx = np.argmax(gamma)
            plot_ky_val = ds['ky'].isel(ky=plot_idx).values
            print(f"  -> No target ky provided. Defaulting to max growth rate at ky={plot_ky_val:.4f}")
        
        # Pull the automatically generated label
        custom_label = labels[i] if labels is not None else os.path.basename(nc_filepath)

        try:
            beta_val = float(ds['beta'].values)
            title_str = (
                f"{custom_label} : "
                f"$\\beta$={beta_val:.4f} "
                f"($k_y \\rho_i \\approx${plot_ky_val:.2f})"
            )
        except KeyError:
            title_str = f"{custom_label} ($k_y \\rho_i \\approx${plot_ky_val:.2f})"

        # Extract theta
        theta = ds['theta'].values
        
        # 2. Extract phi and apar for the selected mode
        phi_data = ds['phi'].isel(kx=0, ky=plot_idx)
        apar_data = ds['apar'].isel(kx=0, ky=plot_idx)
        
        if 't' in phi_data.dims:
            phi_data = phi_data.isel(t=-1)
            apar_data = apar_data.isel(t=-1)
            
        # Extract Real (ri=0) and Imaginary (ri=1) components
        R_phi = phi_data.isel(ri=0).values
        I_phi = phi_data.isel(ri=1).values
        R_apar = apar_data.isel(ri=0).values
        I_apar = apar_data.isel(ri=1).values
        
        # 3. Normalize by the peak magnitude of Phi
        phi_mag = np.sqrt(R_phi**2 + I_phi**2)
        max_phi = np.max(phi_mag)
        
        if max_phi > 0:
            R_phi = R_phi / max_phi
            I_phi = I_phi / max_phi
            R_apar = R_apar / max_phi
            I_apar = I_apar / max_phi
            
        # 4. Plot the lines
        ax.plot(theta, R_phi,  color='black', linestyle='--', label='$R(\\Phi)$')
        ax.plot(theta, I_phi,  color='blue',  linestyle='-',  label='$I(\\Phi)$')
        ax.plot(theta, R_apar, color='pink',  linestyle='-',  label='$R(A_\\parallel)$')
        ax.plot(theta, I_apar, color='red',   linestyle=':',  label='$I(A_\\parallel)$')
        
        # Format the subplot
        ax.set_xlim(-10,10)
        ax.set_title(title_str)
        ax.set_ylabel('Norm. Amplitude')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
        
        ds.close()

    axes[-1].set_xlabel('Extended Poloidal Angle ($\\theta$)')
    plt.tight_layout()
    
    # Dynamically name the figure based on the parent directory of the first file
    first_file_parent = os.path.basename(os.path.dirname(os.path.abspath(valid_files[0])))
    fig_name = f"Figures/eigenfunctions_{first_file_parent}.png"
    
    # Uncomment the line below if you want it to automatically save every time
    # plt.savefig(fig_name, dpi=300, bbox_inches='tight')
    
    plt.show()


# ==========================================
# TERMINAL MODE
# ==========================================
if __name__ == "__main__" and not sys.argv[0].endswith('ipykernel_launcher.py'):
    if len(sys.argv) < 2:
        print("Usage: python plot_eigenfunction.py <file1.nc> [file2.nc ...] [target_ky]")
        sys.exit(1)
        
    file_paths = []
    target_ky = None
    
    # Sort through the command line arguments
    for arg in sys.argv[1:]:
        try:
            val = float(arg)
            target_ky = val
        except ValueError:
            file_paths.append(arg)
            
    # Automatically generate labels using the parent directory name
    labels = [os.path.basename(os.path.dirname(os.path.abspath(fp))) for fp in file_paths]

    plot_real_imag_components(file_paths, labels, target_ky)


# ==========================================
# INTERACTIVE CELL MODE (For VS Code)
# ==========================================
#%% 
import sys
# Define your interactive files here
interactive_files = ["../../rhot_0.96_first_ntheta_192/ky_1.0/run.out.nc"]
interactive_target_ky = None 

# Automatically generate labels for interactive mode as well
interactive_labels = [os.path.basename(os.path.dirname(os.path.abspath(fp))) for fp in interactive_files]

plot_real_imag_components(interactive_files, interactive_labels, interactive_target_ky)
#%%