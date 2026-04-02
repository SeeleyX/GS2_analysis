import sys
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
from scipy.interpolate import interp1d

def plot_single_turn_flux_surfaces(f1, f2, f3):
    files = [f1, f2, f3]
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    
    last_lc = None 

    for i, file_path in enumerate(files):
        ax = axes[i]
        
        try:
            ds = xr.open_dataset(file_path)
            
            # Extract theta and create the slightly expanded mask (-pi - 0.2 to pi + 0.2)
            theta = ds['theta'].values.flatten()
            mask = (theta >= -np.pi - 0.2) & (theta <= np.pi + 0.2)
            
            # Apply the mask
            rplot = ds['rplot'].values.flatten()[mask]
            zplot = ds['zplot'].values.flatten()[mask]
            
            target_var = ds['tpar']
            slice_args = {d: -1 if d == 't' else 0 for d in target_var.dims if d in ['t', 'species', 'kx', 'ky']}
            
            data_slice = target_var.isel(**slice_args)
            real = data_slice.isel(ri=0).values.flatten()
            imag = data_slice.isel(ri=1).values.flatten()
            
            data_abs = np.sqrt(real**2 + imag**2)[mask]
            ds.close()

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

        # Local Normalization
        safe_max = np.nanmax(data_abs)
        if safe_max == 0 or np.isnan(safe_max):
            safe_max = 1.0
        norm_data = data_abs / safe_max

        # --- SMOOTHING INTERPOLATION ---
        n_orig = len(rplot)
        t_orig = np.linspace(0, 1, n_orig)
        t_smooth = np.linspace(0, 1, 1500) 

        r_spline = interp1d(t_orig, rplot, kind='cubic')
        z_spline = interp1d(t_orig, zplot, kind='cubic')
        r_smooth = r_spline(t_smooth)
        z_smooth = z_spline(t_smooth)

        c_spline = interp1d(t_orig, norm_data, kind='linear')
        norm_smooth = np.clip(c_spline(t_smooth), 0, 1)

        # --- Create Continuous Colored Line ---
        points = np.array([r_smooth, z_smooth]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        segment_values = 0.5 * (norm_smooth[:-1] + norm_smooth[1:])

        norm = mcolors.Normalize(vmin=0, vmax=1.0)

        lc = LineCollection(segments, cmap='inferno', norm=norm, array=segment_values)
        lc.set_linewidth(20.0) 
        ax.add_collection(lc)
        last_lc = lc 

        # Plot the magnetic axis cross
        ax.plot(3.0, 0.0, marker='+', color='black', markersize=14, markeredgewidth=2)

        # Formatting axes
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_aspect('equal', adjustable='box')

        rmin, rmax = min(r_smooth), max(r_smooth)
        zmin, zmax = min(z_smooth), max(z_smooth)
        dr, dz = (rmax - rmin) * 0.1, (zmax - zmin) * 0.1

        ax.set_xlim(rmin - dr, rmax + dr * 1.2)
        ax.set_ylim(zmin - dz, zmax + dz * 1.2)

        origin_r, origin_z = rmin - dr, zmin - dz
        
        ax.annotate('', xy=(rmax + dr, origin_z), xytext=(origin_r, origin_z),
                    arrowprops=dict(arrowstyle="-|>", color='black', lw=2.5, mutation_scale=20))
        ax.annotate('', xy=(origin_r, zmax + dz), xytext=(origin_r, origin_z),
                    arrowprops=dict(arrowstyle="-|>", color='black', lw=2.5, mutation_scale=20))

        ax.text(rmax + dr * 1.1, origin_z, 'R', fontsize=18, fontweight='bold', va='center', ha='left')
        ax.text(origin_r, zmax + dz * 1.1, 'Z', fontsize=18, fontweight='bold', va='bottom', ha='center')

    # --- Add the Shared, Vertical Tickless Colorbar ---
    if last_lc is not None:
        cbar = fig.colorbar(last_lc, ax=axes.ravel().tolist(), orientation='vertical', 
                            fraction=0.03, pad=0.04, aspect=30)
        
        cbar.set_ticks([]) 
        cbar.set_label(r'$\delta T_\parallel$', fontsize=24, fontweight='bold', labelpad=20)
        
        cbar.ax.annotate('', xy=(-0.6, 1.0), xytext=(-0.6, 0.0), 
                         xycoords='axes fraction', 
                         arrowprops=dict(arrowstyle="->", color='black', lw=2.5, mutation_scale=20))

    # --- SAVE THE FIGURE ---
    # Create the Figures directory if it doesn't already exist
    output_dir = "Figures"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define a sensible, clear filename
    output_path = os.path.join(output_dir, "ITG_temp_flux_surfaces.png")
    
    # Save the figure with high resolution and a tight bounding box
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=False)
    print(f"\n✅ Figure successfully saved to: {output_path}")

    # Display the plot on screen as well
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py file1 file2 file3")
    else:
        plot_single_turn_flux_surfaces(sys.argv[1], sys.argv[2], sys.argv[3])