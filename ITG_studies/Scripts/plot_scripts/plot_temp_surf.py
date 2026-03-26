import sys
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def get_binned_data(file_path, num_bins=50):
    try:
        ds = xr.open_dataset(file_path)
        rplot = ds['rplot'].values.flatten()
        zplot = ds['zplot'].values.flatten()
        
        var_name = 'tpar' if 'tpar' in ds.data_vars else 'phi'
        target_var = ds[var_name]

        slice_args = {d: -1 if d == 't' else 0 for d in target_var.dims if d in ['t', 'species', 'kx', 'ky']}
        data_slice = target_var.isel(**slice_args)
        
        real = data_slice.isel(ri=0).values.flatten()
        imag = data_slice.isel(ri=1).values.flatten()
        data_abs = np.sqrt(real**2 + imag**2)
        
        bins = np.linspace(rplot.min(), rplot.max(), num_bins + 1)
        centers = 0.5 * (bins[:-1] + bins[1:])
        
        binned_avg = []
        valid_centers = []
        for b in range(num_bins):
            mask = (rplot >= bins[b]) & (rplot < bins[b+1])
            if np.any(mask):
                binned_avg.append(np.mean(data_abs[mask]))
                valid_centers.append(centers[b])
        
        ds.close()
        return rplot, zplot, np.array(valid_centers), np.array(binned_avg), os.path.basename(file_path)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None, None, None, None

def plot_three_cases(f1, f2, f3):
    files = [f1, f2, f3]
    results = [get_binned_data(f) for f in files]
    results = [r for r in results if r[0] is not None]

    if not results: return

    global_binned_max = max([np.max(r[3]) for r in results])
    
    # Increase height (10) to prevent vertical clipping
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    
    for i, (r, z, centers, avg, fname) in enumerate(results):
        ax1 = axes[i]
        norm_avg = avg / global_binned_max
        
        # --- Flux Surface ---
        ax1.plot(r, z, color='black', linewidth=1.5, alpha=0.2)
        ax1.plot(3.0, 0.0, marker='+', color='black', markersize=14, markeredgewidth=2)
        
        ax1.set_xticks([]); ax1.set_yticks([])
        # Explicitly setting limits with a tiny bit of extra vertical padding (1.2 instead of 1.1)
        ax1.set_xlim(2.4, 3.6); ax1.set_ylim(-1.2, 1.2)
        ax1.set_aspect('equal', adjustable='box')
        for s in ax1.spines.values(): s.set_visible(False)
        
        # --- Temperature Axis ---
        ax2 = ax1.twinx()
        ax2.plot(centers, norm_avg, color='tab:blue', linewidth=3.5)
        ax2.set_ylim(0, 1.05) 
        
        for s in ['top', 'bottom', 'left']: ax2.spines[s].set_visible(False)
        
        if i == 2:
            ax2.set_ylabel(r'$\delta T_N$', fontsize=24, color='tab:blue', fontweight='bold', labelpad=20)
            ax2.spines['right'].set_visible(True)
            ax2.tick_params(axis='y', labelcolor='tab:blue', labelsize=18)
        else:
            ax2.set_yticklabels([])
            ax2.spines['right'].set_visible(False)
            ax2.tick_params(axis='y', length=0)

    # Use constrained_layout instead of tight_layout for more robust spacing
    plt.subplots_adjust(wspace=0.1) 
    
    output_name = "Figures/poster_temp_surface_full.png"
    
    # CRITICAL: pad_inches adds a safety margin around the save
    plt.savefig(output_name, 
                dpi=600, 
                transparent=True, 
                bbox_inches='tight', 
                pad_inches=0.2)
    
    print(f"Saved: {output_name} with vertical padding.")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py file1 file2 file3")
    else:
        plot_three_cases(sys.argv[1], sys.argv[2], sys.argv[3])