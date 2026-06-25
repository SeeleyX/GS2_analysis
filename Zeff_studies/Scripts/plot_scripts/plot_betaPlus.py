import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np
import sys
import os
import re
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


def plot_beta_scan(target_dirs):

    # --- Pass 1: Collect all data ---
    scan_data_list = []
    global_params = {}

    for target_dir in target_dirs:
        search_pattern = os.path.join(target_dir, "**", "*.out.nc")
        nc_filepaths = glob.glob(search_pattern, recursive=True)

        if not nc_filepaths:
            continue

        local_params = {}
        betas, gammas, omegas = [], [], []

        for nc_filepath in nc_filepaths:
            directory = os.path.dirname(nc_filepath)

            if not local_params:
                local_params = get_run_parameters(directory)

                # --- Override Zeff from parent folder name if present ---
                parent_name = os.path.basename(os.path.normpath(target_dir))

                # Example matches:
                # Zeff_2.0_scan
                # myrun_Zeff_1.5_test
                # Zeff_3
                import re

                match = re.search(r'Zeff[_-]?([0-9]*\.?[0-9]+)', parent_name, re.IGNORECASE)

                if match:
                    local_params['zeff'] = match.group(1)

                if not global_params:
                    global_params = local_params

            try:
                ds = xr.open_dataset(nc_filepath)

                try:
                    beta_val = float(ds['beta'].values)
                except KeyError:
                    folder_name = os.path.basename(directory)
                    beta_val = float(folder_name.replace('beta_', ''))

                beta_pct = beta_val * 100.0

                eps = local_params.get('eps')
                if eps is None:
                    temp_params = get_run_parameters(directory)
                    eps = temp_params.get('eps')

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
                
            except Exception as e:
                pass

        if betas:
            sorted_indices = np.argsort(betas)
            
            # Safely extract Zeff as a float for the colormap
            try:
                z_float = float(local_params.get('zeff', 1.0))
            except ValueError:
                z_float = 1.0
                
            scan_data_list.append({
                'label': os.path.basename(os.path.normpath(target_dir)),
                'betas': np.array(betas)[sorted_indices],
                'gammas': np.array(gammas)[sorted_indices],
                'omegas': np.array(omegas)[sorted_indices],
                'zeff_float': z_float
            })

    if not scan_data_list:
        print("No valid data found to plot.")
        return

    # --- Pass 2: Setup Colormap based on Zeff domain ---
    zeffs = [data['zeff_float'] for data in scan_data_list]
    z_min, z_max = min(zeffs), max(zeffs)
    
    # If there is only one Zeff value, we give the map a tiny range so it doesn't crash
    if z_min == z_max:
        norm = mcolors.Normalize(vmin=z_min * 0.9, vmax=z_max * 1.1)
    else:
        norm = mcolors.Normalize(vmin=z_min, vmax=z_max)
        
    cmap = cm.cividis  # You can change this to 'plasma', 'inferno', etc.
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # --- Pass 3: Plot the Data ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharex=True)

    for data in scan_data_list:
        # Assign color from the gradient based on the specific Zeff value
        line_color = cmap(norm(data['zeff_float']))
        
        ax1.plot(data['betas'], data['gammas'], marker='s', linestyle='--', linewidth=1, color=line_color)
        ax2.plot(data['betas'], data['omegas'], marker='s', linestyle='--', linewidth=1, color=line_color)
        
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')
    ax1.set_xlabel(r'$\beta$ (%)')
    ax1.grid(True, which='both', linestyle='-', alpha=0.2)
    # ax1.set_yscale('symlog', linthresh=0.1)
    
    ax2.set_xlabel(r'$\beta$ (%)')
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')
    ax2.grid(True, which='both', linestyle='-', alpha=0.2)
    # ax2.set_yscale('symlog', linthresh=0.1)
    
    # Add the shared heatmap colorbar to the right of the subplots
    cbar = fig.colorbar(sm, ax=[ax1, ax2], orientation='vertical', fraction=0.05, pad=0.02)
    cbar.set_label(r'$Z_\mathrm{eff}$')
    
    # --- Pass 4: Save Figure ---
    if not os.path.isdir('Figures'):
        print("\n--- ERROR ---")
        print("The 'Figures' folder does not exist. Plot was NOT saved.")
        plt.close(fig)
        sys.exit(1)
    
    a = global_params.get('aky', 'NA')
    p = global_params.get('pk', 'NA')
    s = global_params.get('shat', 'NA')
    t1 = global_params.get('tprim1', 'NA')
    t2 = global_params.get('tprim2', 'NA')
    
    # Dynamically name the file based on the domain of Zeff
    if z_min == z_max:
        z_str = f"{z_min}"
    else:
        z_str = f"{z_min}-{z_max}"
    
    filename = f"scan_zeff{z_str}_aky{a}_pk{p}_shat{s}_tprim1-{t1}_tprim2-{t2}.png"
    save_path = os.path.join('Figures', filename)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"\n--- SUCCESS ---")
    print(f"Plot saved to: {save_path}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python plot_beta.py folder1 folder2 folder3 ...")
        sys.exit(1)

    raw_directories = sys.argv[1:]
    target_directories = expand_target_directories(raw_directories)
    
    if not target_directories:
        print("Error: No valid target directories containing scans were found.")
        sys.exit(1)

    plot_beta_scan(target_directories)