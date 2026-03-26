import sys
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker 

def plot_poster_geometry(file_path):
    print(f"Extracting geometry and temperature from: '{file_path}'...\n")
    
    try:
        ds = xr.open_dataset(file_path)
        
        # Extract the geometry
        theta = ds['theta'].values
        rplot = ds['rplot'].values
        zplot = ds['zplot'].values
        
        # Check which variable we are plotting
        if 'tpar' in ds.data_vars:
            target_var = ds['tpar']
        else:
            print("Warning: 'tpar' not found. Falling back to electrostatic potential 'phi'.")
            target_var = ds['phi']

        # --- DYNAMIC SLICING ---
        slice_args = {}
        if 't' in target_var.dims:
            slice_args['t'] = -1
        if 'species' in target_var.dims:
            slice_args['species'] = 0
        if 'kx' in target_var.dims:
            slice_args['kx'] = 0
        if 'ky' in target_var.dims:
            slice_args['ky'] = 0
            
        data_slice = target_var.isel(**slice_args)

        # Calculate the amplitude (magnitude)
        data_real = data_slice.isel(ri=0).values
        data_imag = data_slice.isel(ri=1).values
        data_abs = np.sqrt(data_real**2 + data_imag**2)
        
        # Normalize the amplitude
        max_val = np.max(data_abs)
        if max_val > 0:
            data_abs = data_abs / max_val
            
        ds.close()
    except Exception as e:
        print(f"Error opening or reading file: {e}")
        return

    # --- R-AVERAGING LOGIC (For the 1D Line Graph) ---
    num_bins = 50 
    r_bins = np.linspace(rplot.min(), rplot.max(), num_bins + 1)
    r_centers = 0.5 * (r_bins[:-1] + r_bins[1:]) # Find the middle of each bin for plotting
    
    # Figure out which bin each rplot value falls into
    bin_indices = np.digitize(rplot, r_bins)
    
    # Calculate the average amplitude inside each R bin
    data_avg_binned = np.zeros(num_bins)
    for i in range(1, num_bins + 1):
        mask = (bin_indices == i)
        if np.any(mask):
            data_avg_binned[i-1] = np.mean(data_abs[mask])
        else:
            data_avg_binned[i-1] = np.nan 
    # -------------------------

# --- Figure 1: Dual Y-Axis Plot (Flux Surface + Temp Graph) ---
    fig1, ax1 = plt.subplots(figsize=(8, 12)) # Taller canvas to safely fit the new 1:1 ratio limits
    
    # Left Y-Axis: Plot the Flux Surface Geometry (Z vs R)
    ax1.plot(rplot, zplot, color='black', linewidth=2, alpha=0.6, label='Flux Surface')
    ax1.set_xlabel('R', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Z', fontsize=16, fontweight='bold', color='black')
    ax1.tick_params(axis='y', labelcolor='black', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    
    # --- HARDCODE THE LIMITS AND EXACT TICK MARKS ---
    ax1.set_xlim(2.4, 3.6)
    ax1.set_ylim(-1.1, 1.1)
    
    # Force the exact numbers to appear on the axes
    ax1.set_xticks([2.4, 2.7, 3.0, 3.3, 3.6])
    ax1.set_yticks([-1.1, -0.5, 0.0, 0.5, 1.1])
    
    # FORCE EQUAL ASPECT RATIO 
    ax1.set_aspect('equal', adjustable='box')
    # -------------------------------------------------------------------------
    
    # Right Y-Axis: Plot the R-Averaged Temperature (Temp vs R)
    ax2 = ax1.twinx() 
    
    # Filter out the NaN values so the line connects smoothly
    valid_mask = ~np.isnan(data_avg_binned)  
    r_valid = r_centers[valid_mask]          
    data_valid = data_avg_binned[valid_mask] 
    
    # Plot using the filtered data
    ax2.plot(r_valid, data_valid, color='tab:blue', linewidth=2, label='Temp Perturbation')
    
    # --- HARDCODE LIMITS AND TICKS FOR TEMPERATURE ---
    ax2.set_ylim(0.0, 0.06)
    ax2.set_yticks([0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    # -------------------------------------------------------------------------

    # Set the label using raw string formatting for LaTeX rendering
    ax2.set_ylabel(r'$\delta T$', fontsize=18, fontweight='bold', color='tab:blue')
    ax2.tick_params(axis='y', labelcolor='tab:blue', labelsize=12)
    
    # Add a grid and a combined legend for clarity
    # ax1.grid(False)
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    
    # Move legend slightly out of the way of the strict bounds
    # ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', fontsize=12)
    
    fig1.tight_layout()

    # --- Figure 2: 3D Toroidal Spiral ---
    fig2 = plt.figure(figsize=(8, 8))
    ax2_3d = fig2.add_subplot(111, projection='3d')
    
    q_approx = 1.4 
    toroidal_angle = theta * q_approx
    
    X = rplot * np.cos(toroidal_angle)
    Y = rplot * np.sin(toroidal_angle)
    Z = zplot

    ax2_3d.plot(X, Y, Z, color='red', linewidth=3)

    max_range_3d = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0
    mid_x = (X.max()+X.min()) * 0.5
    mid_y = (Y.max()+Y.min()) * 0.5
    mid_z = (Z.max()+Z.min()) * 0.5
    
    ax2_3d.set_xlim(mid_x - max_range_3d, mid_x + max_range_3d)
    ax2_3d.set_ylim(mid_y - max_range_3d, mid_y + max_range_3d)
    ax2_3d.set_zlim(mid_z - max_range_3d, mid_z + max_range_3d)

    ax2_3d.axis('off') 
    fig2.tight_layout()

    # --- Save the plots (High Quality) ---
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    file_basename = os.path.basename(file_path).replace('.out.nc', '')
    
    save_path_2d = os.path.join(output_dir, f"poster_sharedX_temp_2D_{file_basename}.png")
    fig1.savefig(save_path_2d, dpi=600, transparent=True, bbox_inches='tight')
    
    save_path_3d = os.path.join(output_dir, f"poster_flux_tube_3D_{file_basename}.png")
    fig2.savefig(save_path_3d, dpi=600, transparent=True, bbox_inches='tight')
    
    print(f"High-Res Shared X-Axis Plot saved to: '{save_path_2d}'")
    print(f"High-Res 3D Plot saved to: '{save_path_3d}'")
    
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_flux_tube.py <path_to_out_nc_file>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    plot_poster_geometry(target_file)