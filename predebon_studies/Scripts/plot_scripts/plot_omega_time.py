import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_gamma_time_evolution(base_dir):
    """
    Parses a directory of ky scans, extracts the full time-history of the 
    instantaneous growth rate for each mode, and plots them together to inspect convergence.
    """
    # Extract rho value for the title and filename
    match = re.search(r'rho_([0-9.]+)', base_dir)
    rho_val = match.group(1) if match else "unknown"

    # 1. Find all .out.nc files recursively
    search_pattern = os.path.join(base_dir, "**", "*.out.nc")
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Extracting time histories...")

    runs_data = []

    # 2. Extract full time arrays and instantaneous gamma
    for file in nc_files:
        try:
            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            t = ds['t'].values
            
            # ri=1 is the running growth rate diagnostic calculated by GS2 over time
            gamma_t = ds['omega'].isel(ri=1).squeeze().values
            
            runs_data.append({
                'ky': ky,
                't': t,
                'gamma': gamma_t
            })
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not runs_data:
        print("Error: No valid data could be parsed.")
        return

    # 3. Sort by ky so the legend entries and color schemes align sequentially
    runs_data.sort(key=lambda x: x['ky'])

    # 4. Initialize Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Generate a clean color spectrum based on the number of ky modes found
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(runs_data)))

    # 5. Plot each mode's history
    for i, run in enumerate(runs_data):
        ax.plot(run['t'], run['gamma'], color=colors[i], linewidth=2, 
                label=rf'$k_y \rho_i = {run["ky"]:.2f}$')

    # Formatting
    ax.set_xlabel(r'Time $t \, [a / v_{th}]$', fontsize=11)
    ax.set_ylabel(r'Instantaneous Growth Rate $\gamma(t) \, [v_{th}/a]$', fontsize=11)
    ax.set_title(rf'Growth Rate Time Evolution and Convergence ($\rho = {rho_val}$)', fontsize=13, pad=15)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', linewidth=0.8, linestyle=':')

    # Move the legend outside the box if you have a massive amount of scans
    if len(runs_data) > 8:
        ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize=9, frameon=True)
    else:
        ax.legend(loc="best", fontsize=10)

    fig.tight_layout()
    
    # 6. Save and Display
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"gamma_time_evolution_rho_{rho_val}.png")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Time-evolution plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    # Fallback default to 'rho_0.96' if no argument passed via shell
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "rho_0.96"
    plot_gamma_time_evolution(target_directory)