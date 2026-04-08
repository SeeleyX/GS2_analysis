import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot_real_imag_components(nc_filepaths):
    # Filter out files that don't exist
    valid_files = [f for f in nc_filepaths if os.path.exists(f)]
    n_files = len(valid_files)
    
    if n_files == 0:
        print("Error: No valid files found.")
        return

    # Create subplots dynamically based on the number of files
    # Make the figure taller if there are many files
    fig, axes = plt.subplots(n_files, 1, figsize=(10, 4 * n_files), sharex=True)
    
    # If there's only 1 file, axes is a single object. We make it a list so we can loop over it safely.
    if n_files == 1:
        axes = [axes]

    for ax, nc_filepath in zip(axes, valid_files):
        print(f"Processing: {nc_filepath}")
        ds = xr.open_dataset(nc_filepath)
        
        # 1. Identify the most unstable k_y mode
        gamma = ds['omega'].isel(t=-1, kx=0, ri=1).values
        max_ky_idx = np.argmax(gamma)
        max_ky_val = ds['ky'].isel(ky=max_ky_idx).values
        
        # Try to pull the exact beta value for the subplot title
        try:
            beta_val = float(ds['beta'].values)
            title_str = f"$\\beta$={beta_val:.4f} (Max $\gamma$ at $k_y \\rho_i$={max_ky_val:.2f})"
        except KeyError:
            filename = os.path.basename(nc_filepath)
            title_str = f"{filename} ($k_y \\rho_i$={max_ky_val:.2f})"

        # Extract theta
        theta = ds['theta'].values
        
        # 2. Extract phi and apar for the most unstable mode
        phi_data = ds['phi'].isel(kx=0, ky=max_ky_idx)
        apar_data = ds['apar'].isel(kx=0, ky=max_ky_idx)
        
        if 't' in phi_data.dims:
            phi_data = phi_data.isel(t=-1)
            apar_data = apar_data.isel(t=-1)
            
        # Extract Real (ri=0) and Imaginary (ri=1) components
        R_phi = phi_data.isel(ri=0).values
        I_phi = phi_data.isel(ri=1).values
        R_apar = apar_data.isel(ri=0).values
        I_apar = apar_data.isel(ri=1).values
        
        # 3. Normalize by the peak magnitude of Phi to preserve relative scales
        phi_mag = np.sqrt(R_phi**2 + I_phi**2)
        max_phi = np.max(phi_mag)
        
        if max_phi > 0:
            R_phi = R_phi / max_phi
            I_phi = I_phi / max_phi
            R_apar = R_apar / max_phi
            I_apar = I_apar / max_phi
            
        # 4. Plot the lines with requested styles
        ax.plot(theta, R_phi,  color='black', linestyle='--', label='$R(\\Phi)$')
        ax.plot(theta, I_phi,  color='blue',  linestyle='-',  label='$I(\\Phi)$')
        ax.plot(theta, R_apar, color='pink',  linestyle='-',  label='$R(A_\\parallel)$')
        ax.plot(theta, I_apar, color='red',   linestyle=':',  label='$I(A_\\parallel)$')
        
        # Format the subplot
        ax.set_title(title_str)
        ax.set_ylabel('Normalized Amplitude')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
        
        ds.close()

    # Format the x-axis (only needed on the bottom subplot)
    axes[-1].set_xlabel('Extended Poloidal Angle ($\\theta$)')
    
    # Adjust layout so legends and subplots don't overlap
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_real_imag.py <outputfile1> [outputfile2 ...]")
        sys.exit(1)
        
    file_paths = sys.argv[1:]
    plot_real_imag_components(file_paths)