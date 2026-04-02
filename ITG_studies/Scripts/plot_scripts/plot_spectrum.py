import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_ky_spectrum(base_dir, poster_style=True):
    # --- STYLING TOGGLE ---
    POSTER_STYLE = poster_style

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

    # --- Setup Dynamic Style Variables ---
    if POSTER_STYLE:
        # Wide, rectangular figure for posters
        fig_size = (12, 8) 
        lw = 4
        label_fs = 34
        save_name = f"miller_ky-scan_kappa_{kappa_val}_poster.png"
    else:
        # Standard proportions for papers
        fig_size = (9, 6)
        lw = 2
        label_fs = 12
        save_name = f"miller_ky-scan_kappa_{kappa_val}.png"

    # 4. Create the dual-axis plot
    fig, ax1 = plt.subplots(figsize=fig_size)
    ax2 = ax1.twinx()  

    color1 = 'tab:red'
    color2 = 'tab:blue'

    # Plot the lines (markers removed for pure lines)
    ax1.plot(ky_arr, gamma_arr, color=color1, linewidth=lw, label=r'$\gamma$')
    ax2.plot(ky_arr, omega_arr, color=color2, linewidth=lw, linestyle='--', label=r'$\omega$')

    # Apply symlog scales to X, and both Y axes
    ax1.set_xscale('symlog', linthresh=0.1)
    ax1.set_yscale('symlog', linthresh=1e-0)
    ax2.set_yscale('symlog', linthresh=1e-0)

    # 5. Apply Conditional Formatting
    if POSTER_STYLE:
        # Hide standard spines for BOTH axes
        for spine in ax1.spines.values(): spine.set_visible(False)
        for spine in ax2.spines.values(): spine.set_visible(False)
        
        # Remove standard ticks
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax2.set_yticks([])
        
        # Draw custom thick arrows
        # X-axis (Black)
        ax1.annotate('', xy=(1.05, 0), xytext=(0, 0), xycoords='axes fraction', 
                    arrowprops=dict(arrowstyle="-|>", color='black', lw=4, mutation_scale=25))
        # Left Y-axis (Red for Gamma)
        ax1.annotate('', xy=(0, 1.05), xytext=(0, 0), xycoords='axes fraction', 
                    arrowprops=dict(arrowstyle="-|>", color=color1, lw=4, mutation_scale=25))
        # Right Y-axis (Blue for Omega)
        ax2.annotate('', xy=(1.0, 1.05), xytext=(1.0, 0), xycoords='axes fraction', 
                    arrowprops=dict(arrowstyle="-|>", color=color2, lw=4, mutation_scale=25))

        # Add large floating text labels near the arrows
        ax1.text(1.05, -0.05, r'$k_y \rho_i$', transform=ax1.transAxes, fontsize=label_fs, va='top', ha='center', fontweight='bold')
        ax1.text(-0.05, 1.05, r'$\gamma$', transform=ax1.transAxes, color=color1, fontsize=label_fs+6, va='center', ha='right', fontweight='bold')
        ax2.text(1.05, 1.05, r'$\omega$', transform=ax2.transAxes, color=color2, fontsize=label_fs+6, va='center', ha='left', fontweight='bold')

        # Add zero lines for clear marginal stability thresholds
        ax1.axhline(0, color='gray', linewidth=2, linestyle=':', alpha=0.7)
        
    else:
        # --- Standard Paper Formatting ---
        ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=label_fs)
        ax1.set_ylabel(r'Growth Rate ($\gamma$)', color=color1, fontsize=label_fs)
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, linestyle='--', alpha=0.6)

        ax2.set_ylabel(r'Real Frequency ($\omega$)', color=color2, fontsize=label_fs)
        ax2.tick_params(axis='y', labelcolor=color2)
        ax2.axhline(0, color='black', linewidth=1, linestyle=':')

        plt.title(rf'Miller ITG Growth Rate Spectrum ($\kappa = {kappa_val}$)', fontsize=14)

    fig.tight_layout()
    
    # 6. Handle Directory Creation and Saving
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) 
    
    save_path = os.path.join(output_dir, save_name)
    dpi_val = 400 if POSTER_STYLE else 300
    
    plt.savefig(save_path, dpi=dpi_val, bbox_inches='tight')
    
    mode_text = "POSTER" if POSTER_STYLE else "STANDARD"
    print(f"\n✅ {mode_text} format plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan/kappa_1.0/e_tprim_6.9/"
    # Easily toggle the style right here!
    plot_ky_spectrum(target_directory, poster_style=True)