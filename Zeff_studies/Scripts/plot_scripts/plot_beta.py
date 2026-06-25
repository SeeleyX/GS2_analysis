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
        """Helper to format Fortran numbers (e.g., 1.0d0) into clean strings for filenames."""
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

                # Track which species block we are inside
                if clean_line.startswith('&species_parameters'):
                    if '1' in clean_line:
                        current_species = 1
                    elif '2' in clean_line:
                        current_species = 2
                    else:
                        species_count += 1
                        current_species = species_count
                elif clean_line.startswith('&') or clean_line == '/':
                    # If we hit a new block or end block, we are no longer in a species block
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


def plot_beta_scan(target_dirs):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharex=True)

    colors = ['blue', 'red', 'green', 'purple', 'orange', 'black']
    
    # Dictionary to hold parameters for the filename
    plot_params = {}

    for i, target_dir in enumerate(target_dirs):

        search_pattern = os.path.join(target_dir, "**", "*.out.nc")
        nc_filepaths = glob.glob(search_pattern, recursive=True)

        if not nc_filepaths:
            print(f"No .out.nc files found in {target_dir} or its subdirectories.")
            continue

        print(f"Found {len(nc_filepaths)} files in {target_dir} tree")

        betas = []
        gammas = []
        omegas = []

        for nc_filepath in nc_filepaths:

            directory = os.path.dirname(nc_filepath)

            # Grab base parameters from the first valid directory we process
            if not plot_params:
                plot_params = get_run_parameters(directory)

            try:
                ds = xr.open_dataset(nc_filepath)

                # beta
                try:
                    beta_val = float(ds['beta'].values)
                except KeyError:
                    folder_name = os.path.basename(directory)
                    beta_val = float(folder_name.replace('beta_', ''))

                beta_pct = beta_val * 100.0

                # eps -> R/a
                # Use the new param dict, fallback to reading again if missing
                eps = plot_params.get('eps')
                if eps is None:
                    temp_params = get_run_parameters(directory)
                    eps = temp_params.get('eps')

                if eps is not None and eps > 0:
                    R_over_a = 1.0 / eps
                else:
                    R_over_a = 1 / 0.17
                    print(f"Warning: eps missing in {directory}")

                # growth + frequency
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
                print(f"Skipping {nc_filepath}: {e}")

        if not betas:
            continue

        # Sort by beta
        sorted_indices = np.argsort(betas)
        betas = np.array(betas)[sorted_indices]
        gammas = np.array(gammas)[sorted_indices]
        omegas = np.array(omegas)[sorted_indices]
        
        color = colors[i % len(colors)]
        label = os.path.basename(os.path.normpath(target_dir))
        
        # Growth-rate plot
        ax1.plot(betas, gammas, marker='s', linestyle='--', linewidth=1, color=color, label=label)
        
        # Frequency plot
        ax2.plot(betas, omegas, marker='s', linestyle='--', linewidth=1, color=color, label=label)
        
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')
    ax1.set_xlabel(r'$\beta$ (%)')
    # ax1.set_yscale('log')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()
    
    ax2.set_xlabel(r'$\beta$ (%)')
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()

    # --- SAVE FIGURE LOGIC ---
    if not os.path.isdir('Figures'):
        print("\n--- ERROR ---")
        print("The 'Figures' folder does not exist. Plot was NOT saved.")
        plt.close(fig)
        sys.exit(1)
    
    z = plot_params.get('zeff', 'NA')
    a = plot_params.get('aky', 'NA')
    p = plot_params.get('pk', 'NA')
    s = plot_params.get('shat', 'NA')
    t1 = plot_params.get('tprim1', 'NA')
    t2 = plot_params.get('tprim2', 'NA')
    
    # New filename structure including both tprim1 and tprim2
    filename = f"scan_zeff{z}_aky{a}_pk{p}_shat{s}_tprim1-{t1}_tprim2-{t2}.png"
    save_path = os.path.join('Figures', filename)
    
    plt.savefig(save_path, dpi=300)
    plt.close(fig) # Closes the figure to free memory
    
    print(f"\n--- SUCCESS ---")
    print(f"Plot saved to: {save_path}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python plot_beta.py folder1 folder2 folder3 ...")
        sys.exit(1)

    target_directories = sys.argv[1:]

    for d in target_directories:
        if not os.path.isdir(d):
            print(f"Error: {d} does not exist.")
            sys.exit(1)
            
    plot_beta_scan(target_directories)