import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob


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


def plot_beta_scan(target_dirs):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharex=True)

    colors = [
        'blue',
        'red',
        'green',
        'purple',
        'orange',
        'black'
    ]

    for i, target_dir in enumerate(target_dirs):

        # CHANGED HERE: Using "**" and recursive=True to search all subdirectories
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
                eps = get_eps_from_in_file(directory)

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
        ax1.plot(
            betas,
            gammas,
            marker='s',
            linestyle='--',
            linewidth=1,
            color=color,
            label=label
        )
        
        # Frequency plot
        ax2.plot(
            betas,
            omegas,
            marker='s',
            linestyle='--',
            linewidth=1,
            color=color,
            label=label
        )

    fig.suptitle(r'$R/L_n=0.5$', fontsize=16)
        
    ax1.set_ylabel(r'$\gamma(v_{th}/R)$')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()
    
    ax2.set_xlabel(r'$\beta$ (%)')
    ax2.set_ylabel(r'$\omega(v_{th}/R)$')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()
    plt.show()


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