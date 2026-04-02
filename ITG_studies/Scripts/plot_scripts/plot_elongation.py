import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_elongation_scan(base_dir, poster_style=True):
    # --- STYLING TOGGLE ---
    # Set to True for big fonts/arrows, False for standard paper plots with grids/ticks
    POSTER_STYLE = poster_style

    # 1. STRICT SEARCH: Only look inside base_dir/kappa_*/miller_*/*.out.nc
    search_pattern = os.path.join(base_dir, "kappa_*", "miller_*", "*.out.nc")
    nc_files = glob.glob(search_pattern)
    
    if not nc_files:
        print(f"Error: No .out.nc files found matching '{search_pattern}'.")
        return

    print(f"Found {len(nc_files)} valid files. Extracting and organizing data...")

    data_by_kappa = {}

    # 2. Extract data
    for file in nc_files:
        try:
            match = re.search(r'kappa_([0-9.]+)', file)
            if match:
                kappa = float(match.group(1))
            else:
                continue

            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            if kappa not in data_by_kappa:
                data_by_kappa[kappa] = {'ky': [], 'gamma': [], 'omega': []}
                
            data_by_kappa[kappa]['ky'].append(ky)
            data_by_kappa[kappa]['gamma'].append(growth_rate)
            data_by_kappa[kappa]['omega'].append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not data_by_kappa:
        print("Error: Files were found, but no 'kappa_X.X' data could be extracted.")
        return

    # --- Setup Dynamic Style Variables ---
    if POSTER_STYLE:
        # Made the figure wider and shorter for a more rectangular, stretched look
        fig_size = (22, 6) 
        lw, ms = 4, 12
        label_fs, legend_fs = 34, 16
        save_name = "elongation_ky_scan_poster.png"
    else:
        fig_size = (16, 5)
        lw, ms = 2, 6
        label_fs, legend_fs = 12, 10
        save_name = "elongation_ky_scan.png"

    # 3. Create the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=fig_size)

    sorted_kappas = sorted(data_by_kappa.keys())
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(sorted_kappas)))

    # 4. Plot the data
    for idx, kappa in enumerate(sorted_kappas):
        ky_list = data_by_kappa[kappa]['ky']
        gamma_list = data_by_kappa[kappa]['gamma']
        omega_list = data_by_kappa[kappa]['omega']
        
        sorted_indices = np.argsort(ky_list)
        ky_arr = np.array(ky_list)[sorted_indices]
        gamma_arr = np.array(gamma_list)[sorted_indices]
        omega_arr = np.array(omega_list)[sorted_indices]

        label_str = rf'$\kappa = {kappa}$'
        color = colors[idx]

        ax1.plot(ky_arr, gamma_arr, marker='o', linewidth=lw, markersize=ms, color=color, label=label_str)
        ax2.plot(ky_arr, omega_arr, marker='s', linewidth=lw, markersize=ms, linestyle='--', color=color, label=label_str)

    # 5. Apply Conditional Formatting
    for ax in [ax1, ax2]:
        if POSTER_STYLE:
            # Hide spines and ticks for poster mode
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Draw custom thick arrows
            ax.annotate('', xy=(1.05, 0), xytext=(0, 0), xycoords='axes fraction', 
                        arrowprops=dict(arrowstyle="-|>", color='black', lw=4, mutation_scale=25))
            ax.annotate('', xy=(0, 1.05), xytext=(0, 0), xycoords='axes fraction', 
                        arrowprops=dict(arrowstyle="-|>", color='black', lw=4, mutation_scale=25))
        else:
            # Standard paper mode grid and ticks
            ax.grid(True, linestyle='--', alpha=0.6)

    # --- Format Subplot 1 (Growth Rate) ---
    if POSTER_STYLE:
        ax1.text(1.05, -0.05, r'$k_y \rho_i$', transform=ax1.transAxes, fontsize=label_fs, va='top', ha='center', fontweight='bold')
        ax1.text(-0.05, 1.05, r'$\gamma$', transform=ax1.transAxes, fontsize=label_fs+4, va='center', ha='right', fontweight='bold')
        # legend = ax1.legend(title='Elongation', fontsize=legend_fs, frameon=False, loc='upper left', bbox_to_anchor=(0.05, 0.95))
        # Add the zero line for marginal stability
        ax1.axhline(0, color='gray', linewidth=2, linestyle=':', alpha=0.7)
    else:
        ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=label_fs)
        ax1.set_ylabel(r'Growth Rate ($\gamma$)', fontsize=label_fs)
        # legend = ax1.legend(title='Elongation', fontsize=legend_fs)
        ax1.axhline(0, color='black', linewidth=1, linestyle=':')

    # if legend:
    #     legend.get_title().set_fontsize(str(legend_fs + 2))
    #     legend.get_title().set_fontweight('bold')

    # --- Format Subplot 2 (Real Frequency) ---
    if POSTER_STYLE:
        ax2.text(1.05, -0.05, r'$k_y \rho_i$', transform=ax2.transAxes, fontsize=label_fs, va='top', ha='center', fontweight='bold')
        ax2.text(-0.05, 1.05, r'$\omega$', transform=ax2.transAxes, fontsize=label_fs+4, va='center', ha='right', fontweight='bold')
        # Keep a subtle zero line for context
        ax2.axhline(0, color='gray', linewidth=2, linestyle=':', alpha=0.7)
    else:
        ax2.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=label_fs)
        ax2.set_ylabel(r'Real Frequency ($\omega$)', fontsize=label_fs)
        ax2.axhline(0, color='black', linewidth=1, linestyle=':')

    fig.tight_layout()
    
    # 6. Save to the Figures folder
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, save_name)
    
    dpi_val = 400 if POSTER_STYLE else 300
    plt.savefig(save_path, dpi=dpi_val, bbox_inches='tight')
    
    mode_text = "POSTER" if POSTER_STYLE else "STANDARD"
    print(f"\n✅ {mode_text} format plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "Inputs/ITG_kyscan"
    # You can quickly toggle the style right here
    plot_elongation_scan(target_directory, poster_style=True)