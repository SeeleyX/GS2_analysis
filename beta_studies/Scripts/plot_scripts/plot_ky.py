import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np
import sys
import os
import glob
import re
from collections import defaultdict


def get_eps_from_in_file(directory):
    """Scans .in files in the directory to find the 'eps' parameter."""
    in_files = glob.glob(os.path.join(directory, "*.in"))

    for fpath in in_files:
        try:
            with open(fpath, 'r') as f:
                for line in f:
                    clean_line = line.split('!')[0]
                    if '=' in clean_line:
                        key, val = clean_line.split('=', 1)
                        if key.strip().lower() == 'eps':
                            val_clean = val.strip().replace('d', 'e').replace('D', 'e')
                            return float(val_clean)
        except Exception:
            pass
    return None


def plot_aky_scan(target_dirs):

    scan_data = defaultdict(lambda: {'aky': [], 'gammas': [], 'omegas': []})

    for target_dir in target_dirs:

        search_pattern = os.path.join(target_dir, "**", "*.out.nc")
        nc_filepaths = glob.glob(search_pattern, recursive=True)

        if not nc_filepaths:
            print(f"No .out.nc files found in {target_dir} or its subdirectories.")
            continue

        print(f"Found {len(nc_filepaths)} files in {target_dir} tree. Extracting...")

        for nc_filepath in nc_filepaths:
            directory = os.path.dirname(nc_filepath)

            try:
                ds = xr.open_dataset(nc_filepath)

                # 1. Extract aky
                try:
                    aky_val = float(ds['ky'].values) 
                except KeyError:
                    aky_match = re.search(r'aky_([0-9\.]+)', nc_filepath)
                    if aky_match:
                        aky_val = float(aky_match.group(1))
                    else:
                        print(f"Warning: Could not determine aky for {nc_filepath}. Skipping.")
                        ds.close()
                        continue

                # 2. Extract Beta
                try:
                    beta_val = float(ds['beta'].values)
                except KeyError:
                    folder_name = os.path.basename(directory)
                    beta_val = float(folder_name.replace('beta_', ''))

                beta_pct = beta_val * 100.0
                beta_key = round(beta_pct, 3) 

                # 3. Extract eps -> R/a
                eps = get_eps_from_in_file(directory)
                if eps is not None and eps > 0:
                    R_over_a = 1.0 / eps
                else:
                    R_over_a = 1 / 0.17

                # 4. Extract growth + frequency
                gamma_array = ds['omega'].isel(t=-1, kx=0, ri=1).values
                omega_array = ds['omega'].isel(t=-1, kx=0, ri=0).values
                
                max_idx = np.argmax(gamma_array)
                max_gamma = gamma_array[max_idx] * R_over_a
                corr_omega = omega_array[max_idx] * R_over_a
                
                scan_data[beta_key]['aky'].append(aky_val)
                scan_data[beta_key]['gammas'].append(max_gamma)
                scan_data[beta_key]['omegas'].append(corr_omega)
                
                ds.close()
                
            except Exception as e:
                print(f"Skipping {nc_filepath}: {e}")

    if not scan_data:
        print("Error: No valid data could be grouped.")
        return

    # --- Plotting Phase ---
    # Stack vertically (2 rows, 1 col) and share the X axis
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(8, 8), sharex=True)
    fig.suptitle(r'$R/L_n=0.5$', fontsize=16)

    # 1. Setup Colormap
    beta_keys = sorted(scan_data.keys())
    min_beta = min(beta_keys)
    max_beta = max(beta_keys)
    
    cmap = cm.get_cmap('cool')
    norm = mcolors.Normalize(vmin=min_beta, vmax=max_beta)

    for beta_key in beta_keys:
        
        akys = np.array(scan_data[beta_key]['aky'])
        gammas = np.array(scan_data[beta_key]['gammas'])
        omegas = np.array(scan_data[beta_key]['omegas'])

        sorted_indices = np.argsort(akys)
        akys = akys[sorted_indices]
        gammas = gammas[sorted_indices]
        omegas = omegas[sorted_indices]

        # 2. Get the specific color for this beta
        line_color = cmap(norm(beta_key))

        # Plot using the assigned color
        ax1.plot(akys, gammas, marker='o', linestyle='-', linewidth=1.5, color=line_color)
        ax2.plot(akys, omegas, marker='o', linestyle='-', linewidth=1.5, color=line_color)

    # Configure ax1 (Top: Growth Rate)
    # Removing x-label here since they share the x-axis
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')
    ax1.set_title("Growth Rate")
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Configure ax2 (Bottom: Real Frequency)
    ax2.set_xlabel(r'$k_y\rho_i$')
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')
    ax2.set_title("Real Frequency")
    ax2.grid(True, linestyle='--', alpha=0.7)

    # 3. Add the Colorbar
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    
    # Link the colorbar to both ax1 and ax2 so it scales correctly alongside them
    cbar = fig.colorbar(sm, ax=[ax1, ax2], fraction=0.08, pad=0.05)
    cbar.set_label(r'$\beta$ (%)', rotation=270, labelpad=15)
    
    # Let Matplotlib handle spacing automatically
    plt.show()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python plot_aky.py folder1 folder2 folder3 ...")
        sys.exit(1)

    target_directories = sys.argv[1:]

    for d in target_directories:
        if not os.path.isdir(d):
            print(f"Error: {d} does not exist.")
            sys.exit(1)
            
    plot_aky_scan(target_directories)