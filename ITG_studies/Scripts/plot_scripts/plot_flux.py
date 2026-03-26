import sys
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def plot_flux_tube_geometry(file_path):
    print(f"Extracting geometry from: '{file_path}'...\n")
    
    try:
        ds = xr.open_dataset(file_path)
        
        # Extract the variables
        theta = ds['theta'].values
        rplot = ds['rplot'].values
        zplot = ds['zplot'].values
        
        ds.close()
    except Exception as e:
        print(f"Error opening or reading file: {e}")
        return

    # Find the index where theta is closest to 0 (the outboard midplane)
    idx_theta_0 = np.argmin(np.abs(theta))
    
    # --- Create the Figure ---
    fig = plt.figure(figsize=(14, 6))

    # --- Panel 1: 2D Poloidal Cross-Section ---
    ax1 = fig.add_subplot(1, 2, 1)
    
    # Plot the full field line trace in 2D
    ax1.plot(rplot, zplot, color='tab:blue', linewidth=2, label='Field Line Trace')
    
    # Mark the exact location of theta = 0
    ax1.plot(rplot[idx_theta_0], zplot[idx_theta_0], marker='*', color='red', 
             markersize=15, label=r'$\theta = 0$ (Outboard Midplane)')
    
    ax1.set_aspect('equal')
    ax1.set_xlabel('Major Radius, R (Normalized)', fontsize=12)
    ax1.set_ylabel('Height, Z (Normalized)', fontsize=12)
    ax1.set_title('2D Poloidal Cross-Section of the Flux Tube', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right')

    # --- Panel 2: 3D Toroidal Spiral ---
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    
    # In a tokamak, the field line twists toroidally as it moves poloidally.
    # We use theta (scaled by an approximate safety factor q) for the toroidal angle.
    q_approx = 1.4 # From your input file pk=1.4
    toroidal_angle = theta * q_approx
    
    # Convert cylindrical (R, phi, Z) to Cartesian (X, Y, Z) for the 3D plot
    X = rplot * np.cos(toroidal_angle)
    Y = rplot * np.sin(toroidal_angle)
    Z = zplot

    # Plot the 3D spiral
    ax2.plot(X, Y, Z, color='tab:blue', linewidth=2)
    
    # Mark the theta = 0 point in 3D
    ax2.plot([X[idx_theta_0]], [Y[idx_theta_0]], [Z[idx_theta_0]], 
             marker='*', color='red', markersize=15)

    # Make the 3D axes scaled equally so the donut doesn't look squished
    max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0
    mid_x = (X.max()+X.min()) * 0.5
    mid_y = (Y.max()+Y.min()) * 0.5
    mid_z = (Z.max()+Z.min()) * 0.5
    
    ax2.set_xlim(mid_x - max_range, mid_x + max_range)
    ax2.set_ylim(mid_y - max_range, mid_y + max_range)
    ax2.set_zlim(mid_z - max_range, mid_z + max_range)

    ax2.set_xlabel('X', fontsize=10)
    ax2.set_ylabel('Y', fontsize=10)
    ax2.set_zlabel('Z', fontsize=10)
    ax2.set_title('3D View of the Magnetic Field Line', fontsize=14)

    fig.tight_layout()
    
    # Save the plot
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True)
    file_basename = os.path.basename(file_path).replace('.out.nc', '')
    save_path = os.path.join(output_dir, f"flux_tube_geometry_{file_basename}.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_flux_tube.py <path_to_out_nc_file>")
        print("Example: python plot_flux_tube.py Inputs/ITG_kyscan/tri_0.1/tri_0.1.out.nc")
        sys.exit(1)
        
    target_file = sys.argv[1]
    plot_flux_tube_geometry(target_file)