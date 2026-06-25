import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob

def get_run_parameters(directory):
    """
    Scans the first .in file found in the directory to extract
    zeff, aky, pk, shat, and tprim for species 1 and 2.
    """
    in_files = glob.glob(os.path.join(directory, "*.in"))
    if not in_files:
        return {}

    fpath = in_files[0]
    params = {'zeff': 'NA', 'aky': 'NA', 'pk': 'NA', 'shat': 'NA', 'tprim1': 'NA', 'tprim2': 'NA', 'eps': None}
    
    species_count = 0
    current_species = 0

    def clean_number(val_str):
        v = val_str.replace('d', 'e').replace('D', 'e').rstrip(',')
        try:
            f = float(v)
            if f.is_integer(): return str(int(f))
            return str(f)
        except ValueError:
            return v.strip()

    try:
        with open(fpath, 'r') as f:
            for line in f:
                clean_line = line.split('!')[0].strip().lower()
                if not clean_line:
                    continue

                if clean_line.startswith('&species_parameters'):
                    if '1' in clean_line:
                        current_species = 1
                    elif '2' in clean_line:
                        current_species = 2
                    else:
                        species_count += 1
                        current_species = species_count
                elif clean_line.startswith('&') or clean_line == '/':
                    current_species = 0

                if '=' in clean_line:
                    key, val = [x.strip() for x in clean_line.split('=', 1)]
                    
                    if key == 'zeff': params['zeff'] = clean_number(val)
                    elif key == 'aky': params['aky'] = clean_number(val)
                    elif key == 'pk': params['pk'] = clean_number(val)
                    elif key == 'shat': params['shat'] = clean_number(val)
                    elif key == 'eps': params['eps'] = float(val.replace('d', 'e').replace('D', 'e').rstrip(','))
                    elif key == 'tprim':
                        if current_species == 1:
                            params['tprim1'] = clean_number(val)
                        elif current_species == 2:
                            params['tprim2'] = clean_number(val)
                        
    except Exception as e:
        print(f"Error parsing {fpath}: {e}")

    return params


def expand_target_directories(directories):
    """
    Checks if a directory is a single scan or a 'master' folder containing multiple scans.
    Returns a flattened list of actual target directories to process.
    """
    expanded = []
    for d in directories:
        if not os.path.isdir(d):
            print(f"Warning: {d} does not exist or is not a directory.")
            continue
            
        subdirs = [os.path.join(d, item) for item in os.listdir(d) if os.path.isdir(os.path.join(d, item))]
        has_beta_folders = any(os.path.basename(sub).startswith('beta_') for sub in subdirs)
        
        if has_beta_folders:
            expanded.append(d)
        else:
            valid_sub_scans = []
            for sub in subdirs:
                sub_subdirs = [os.path.basename(item) for item in os.listdir(sub) if os.path.isdir(os.path.join(sub, item))]
                if any(s.startswith('beta_') for s in sub_subdirs):
                    valid_sub_scans.append(sub)
                    
            if valid_sub_scans:
                expanded.extend(sorted(valid_sub_scans))
            else:
                expanded.append(d)
                
    return expanded


def extract_data_from_directory(raw_dir):
    """
    Extracts, calculates, and sorts beta, gamma, and omega arrays for a given parent directory.
    """
    target_dirs = expand_target_directories([raw_dir])
    
    betas, gammas, omegas = [], [], []
    
    for target_dir in target_dirs:
        search_pattern = os.path.join(target_dir, "**", "*.out.nc")
        nc_filepaths = glob.glob(search_pattern, recursive=True)

        for nc_filepath in nc_filepaths:
            directory = os.path.dirname(nc_filepath)
            local_params = get_run_parameters(directory)

            try:
                ds = xr.open_dataset(nc_filepath)

                try:
                    beta_val = float(ds['beta'].values)
                except KeyError:
                    folder_name = os.path.basename(directory)
                    beta_val = float(folder_name.replace('beta_', ''))

                beta_pct = beta_val * 100.0

                eps = local_params.get('eps')
                if eps is not None and eps > 0:
                    R_over_a = 1.0 / eps
                else:
                    R_over_a = 1 / 0.17

                gamma_array = ds['omega'].isel(t=-1, kx=0, ri=1).values
                omega_array = ds['omega'].isel(t=-1, kx=0, ri=0).values
                
                max_idx = np.argmax(gamma_array)
                max_gamma = gamma_array[max_idx] * R_over_a
                corr_omega = omega_array[max_idx] * R_over_a
                
                betas.append(beta_pct)
                gammas.append(max_gamma)
                omegas.append(corr_omega)
                
                ds.close()
                
            except Exception:
                pass

    if betas:
        sorted_indices = np.argsort(betas)
        return np.array(betas)[sorted_indices], np.array(gammas)[sorted_indices], np.array(omegas)[sorted_indices]
    
    return None, None, None


def compare_plots(directories):
    # --- Setup Distinct Styles for Comparison ---
    colors = ['tab:blue', 'tab:red', 'tab:green', 'tab:orange', 'tab:purple']
    markers = ['o', 's', '^', 'D', 'v']
    linestyles = ['-', '--', '-.', ':', '-']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharex=True)
    
    valid_dirs_plotted = []

    # --- Extract and Plot Data for Each Directory ---
    for idx, raw_dir in enumerate(directories):
        print(f"Processing: {raw_dir}")
        betas, gammas, omegas = extract_data_from_directory(raw_dir)
        
        if betas is None:
            print(f"  -> No valid data found in {raw_dir}. Skipping.")
            continue
            
        label_name = os.path.basename(os.path.normpath(raw_dir))
        valid_dirs_plotted.append(label_name)
        
        # Cycle through styles based on index
        c = colors[idx % len(colors)]
        m = markers[idx % len(markers)]
        ls = linestyles[idx % len(linestyles)]
        
        ax1.plot(betas, gammas, marker=m, linestyle=ls, linewidth=1.5, color=c, label=label_name)
        ax2.plot(betas, omegas, marker=m, linestyle=ls, linewidth=1.5, color=c, label=label_name)

    if not valid_dirs_plotted:
        print("No valid data found to plot from any of the provided directories.")
        plt.close(fig)
        return

    # --- Formatting the Axes ---
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')
    ax1.set_xlabel(r'$\beta$ (%)')
    ax1.grid(True, which='both', linestyle='-', alpha=0.2)
    ax1.legend(loc='best')
    
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')
    ax2.set_xlabel(r'$\beta$ (%)')
    ax2.grid(True, which='both', linestyle='-', alpha=0.2)
    ax2.legend(loc='best')
    
    # --- Save Figure ---
    if not os.path.isdir('Figures'):
        os.makedirs('Figures') # Auto-create the directory if it doesn't exist
        print("Created 'Figures' directory.")
    
    # Create a dynamic filename based on the folders compared
    dir_names_str = "_vs_".join(valid_dirs_plotted)
    filename = f"compare_{dir_names_str}.png"
    save_path = os.path.join('Figures', filename)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"\n--- SUCCESS ---")
    print(f"Comparison plot saved to: {save_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_plots.py <folder1> <folder2> [folder3 ...]")
        sys.exit(1)

    raw_directories = sys.argv[1:]
    compare_plots(raw_directories)