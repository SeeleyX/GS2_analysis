import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_parallel_mode_structure(base_dir, param_type, target_val=None, poster_style=True):
    # --- STYLING TOGGLE ---
    POSTER_STYLE = poster_style

    # 1. If a target value wasn't explicitly given, cleanly extract it from the folder name
    if target_val is None:
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
            match = re.search(rf'{param_type}_?([0-9.]+)', file)  

            if match:
                file_val = float(match.group(1))
                if file_val != target_val:
                    continue  
            else:
                continue 
                
            ds = xr.open_dataset(file)
            
            ky = float(ds['ky'].squeeze().values)
            
            theta = ds['theta'].squeeze().values
            shat = float(ds['shat'].squeeze().values)

            kx_local = shat * ky * theta
            
            phi_complex = ds['phi'].squeeze()
            phi_real = phi_complex.isel(ri=0).values
            phi_imag = phi_complex.isel(ri=1).values
            
            phi_mag = np.sqrt(phi_real**2 + phi_imag**2)
            phi_mag_normalized = phi_mag / np.max(phi_mag)
            
            mode_data[ky] = {'kx': kx_local, 'phi': phi_mag_normalized} 

            ds.close()
            
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not mode_data:
        print(f"No data found matching {param_type} = {target_val}.")
        return

    # --- Setup Dynamic Style Variables ---
    if POSTER_STYLE:
        fig_size = (12, 8) 
        lw = 4
        label_fs = 34
        legend_fs = 16
        save_name = f"mode_structure_{param_type}_{target_val}_poster.png"
    else:
        fig_size = (10, 6)
        lw = 2
        label_fs = 14
        legend_fs = 10
        save_name = f"mode_structure_{param_type}_{target_val}.png"

    # Setup the plot
    fig, ax = plt.subplots(figsize=fig_size)
    
    sorted_kys = sorted(mode_data.keys())
    colors = plt.cm.plasma(np.linspace(0, 0.9, len(sorted_kys)))

    # Plot each ky line 
    for idx, ky in enumerate(sorted_kys):
        kx = mode_data[ky]['kx']
        phi = mode_data[ky]['phi']
        
        label_str = rf'$k_y$ = {ky}'
        ax.plot(kx, phi, color=colors[idx], linewidth=lw, label=label_str)

    # Set x-limits from -5pi to 5pi 
    ax.set_xlim(-3 * np.pi, 3 * np.pi)

    # --- Apply Conditional Formatting ---
    if POSTER_STYLE:
        # Hide standard spines
        for spine in ax.spines.values(): 
            spine.set_visible(False)
        
        # Remove standard ticks
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Draw custom thick arrows
        ax.annotate('', xy=(1.05, 0), xytext=(0, 0), xycoords='axes fraction', 
                    arrowprops=dict(arrowstyle="-|>", color='black', lw=4, mutation_scale=25))
        ax.annotate('', xy=(0, 1.05), xytext=(0, 0), xycoords='axes fraction', 
                    arrowprops=dict(arrowstyle="-|>", color='black', lw=4, mutation_scale=25))

        # Add large floating text labels near the arrows
        ax.text(1.05, -0.05, r'$k_x = \hat{s} k_y \theta$', transform=ax.transAxes, fontsize=label_fs, va='top', ha='center', fontweight='bold')
        ax.text(-0.05, 1.05, r'$|\Phi_N|$', transform=ax.transAxes, fontsize=label_fs+4, va='center', ha='right', fontweight='bold')

        # Add a thick dashed zero line for the center of the mode
        ax.axvline(0, color='gray', linestyle='--', linewidth=2, alpha=0.7)

        # Mark pi and -pi with dotted vertical lines
        ax.axvline(np.pi, color='gray', linestyle=':', linewidth=2, alpha=0.6)
        ax.axvline(-np.pi, color='gray', linestyle=':', linewidth=2, alpha=0.6)

        # Add pi and -pi text markers at the bottom of the graph
        # Using get_xaxis_transform() places the text perfectly at the data's X coordinate, but bound to the bottom of the axis
        ax.text(np.pi, -0.05, r'$\pi$', transform=ax.get_xaxis_transform(), fontsize=label_fs, va='top', ha='center', fontweight='bold')
        ax.text(-np.pi, -0.05, r'$-\pi$', transform=ax.get_xaxis_transform(), fontsize=label_fs, va='top', ha='center', fontweight='bold')

        # Commented out the legend for the poster version!
        # legend = ax.legend(title='Wavenumber', fontsize=legend_fs, frameon=False, bbox_to_anchor=(1.05, 1), loc='upper left')
        # legend.get_title().set_fontsize(str(legend_fs + 2))
        # legend.get_title().set_fontweight('bold')

    else:
        # --- Standard Paper Formatting ---
        ax.set_title(f'Mode Structure vs Radial Wavenumber ({param_type} = {target_val})', fontsize=16)
        ax.set_xlabel(r'Local Radial Wavenumber ($k_x = \hat{s} k_y \theta$)', fontsize=label_fs)
        ax.set_ylabel(r'Normalised Amplitude ($|\Phi_N|$)', fontsize=label_fs)
        
        ax.axvline(0, color='black', linestyle='--', alpha=0.5)
        ax.grid(True, linestyle=':', alpha=0.7)
        
        ax.legend(title='Wavenumber', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=legend_fs)

    fig.tight_layout()
    
    # Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, save_name)
    
    dpi_val = 400 if POSTER_STYLE else 300
    plt.savefig(save_path, dpi=dpi_val, bbox_inches='tight')
    
    mode_text = "POSTER" if POSTER_STYLE else "STANDARD"
    print(f"\n✅ {mode_text} format plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python plot_mode_structure.py <folder_name> <param_type> [target_val]")
        print("Example: python plot_mode_structure.py Inputs/ITG_kyscan/kappa_1.1 kappa")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    param_type = sys.argv[2]
    
    target_value = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    plot_parallel_mode_structure(target_directory, param_type, target_value, poster_style=True)