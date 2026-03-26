import sys
import os
import glob
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def extract_data(base_dir):
    """Helper function to extract ky, gamma, and omega from a given directory."""
    search_pattern = f"{base_dir}/*/*.out.nc"
    nc_files = glob.glob(search_pattern)
    
    if not nc_files:
        print(f"Warning: No .out.nc files found inside '{base_dir}'.")
        return [], [], []

    print(f"Found {len(nc_files)} files in {base_dir}. Extracting data...")

    ky_list, gamma_list, omega_list = [], [], []

    for file in nc_files:
        try:
            ds = xr.open_dataset(file)
            
            ky = float(ds['ky'].squeeze().values)
            
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            ky_list.append(ky)
            gamma_list.append(growth_rate)
            omega_list.append(real_freq)
            
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    sorted_indices = np.argsort(ky_list)
    ky_arr = np.array(ky_list)[sorted_indices]
    gamma_arr = np.array(gamma_list)[sorted_indices]
    omega_arr = np.array(omega_list)[sorted_indices]

    return ky_arr, gamma_arr, omega_arr

def plot_ky_spectra(dir1, dir2, label1, label2):
    # Extract data for both directories
    ky1, gamma1, omega1 = extract_data(dir1)
    ky2, gamma2, omega2 = extract_data(dir2)

    # Update global plot parameters for a poster presentation
    plt.rcParams.update({
        'font.size': 16,
        'axes.labelsize': 18,
        'axes.titlesize': 20,
        'xtick.labelsize': 16,
        'ytick.labelsize': 16,
        'legend.fontsize': 16,
        'lines.linewidth': 2,
        'lines.markersize': 8
    })

    color1 = 'tab:blue'
    color2 = 'tab:green'
    
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) 
    
    safe_label1 = "".join(x for x in label1 if x.isalnum() or x in "._-").replace(" ", "_")
    safe_label2 = "".join(x for x in label2 if x.isalnum() or x in "._-").replace(" ", "_")

    # ==========================================
    # FIGURE 1: Growth Rate
    # ==========================================
    fig1, ax1 = plt.subplots(figsize=(8, 6))

    ax1.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)')
    ax1.set_ylabel(r'Growth Rate ($\gamma$)')
    ax1.axhline(0, color='black', linewidth=1.5, linestyle=':')

    
    if len(ky1) > 0:
        ax1.plot(ky1, gamma1, color=color1, label=label1)
    if len(ky2) > 0:
        ax1.plot(ky2, gamma2, color=color2, label=label2)
        
    # Symmetrical log scale to emphasize small modes but safely handle zeros/negatives
    ax1.set_yscale('symlog', linthresh=1e-0)
    ax1.set_xscale('symlog', linthresh=0.1)
    ax1.legend()
    fig1.tight_layout()
    
    save_path1 = os.path.join(output_dir, f"gamma_comp_{safe_label1}_vs_{safe_label2}.png")
    fig1.savefig(save_path1, bbox_inches='tight', dpi=300)
    print(f"Growth Rate plot saved to: '{save_path1}'")

    # ==========================================
    # FIGURE 2: Real Frequency
    # ==========================================
    fig2, ax2 = plt.subplots(figsize=(8, 6))

    ax2.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)')
    ax2.set_ylabel(r'Real Frequency ($\omega$)')
    
    if len(ky1) > 0:
        ax2.plot(ky1, omega1, color=color1, linestyle='--', label=label1)
    if len(ky2) > 0:
        ax2.plot(ky2, omega2, color=color2, linestyle='--', label=label2)
        
    ax2.axhline(0, color='black', linewidth=1.5, linestyle=':')
    
    ax2.legend()
    fig2.tight_layout()
    
    save_path2 = os.path.join(output_dir, f"omega_comp_{safe_label1}_vs_{safe_label2}.png")
    fig2.savefig(save_path2, bbox_inches='tight', dpi=300)
    print(f"Real Frequency plot saved to: '{save_path2}'")

    # Show both plots
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <directory1> <directory2>")
        sys.exit(1)
        
    target_dir1 = sys.argv[1]
    target_dir2 = sys.argv[2]
    
    label_1 = input(f"Enter the legend label for the first dataset ({target_dir1}): ")
    label_2 = input(f"Enter the legend label for the second dataset ({target_dir2}): ")
    
    plot_ky_spectra(target_dir1, target_dir2, label_1, label_2)