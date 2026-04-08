import xarray as xr
import matplotlib.pyplot as plt
import sys
import os

def plot_growth_and_freq(nc_filepaths):
    # Create the figure and subplots once
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Loop through all files passed from the command line
    for nc_filepath in nc_filepaths:
        print(f"Loading data from: {nc_filepath}")
        
        # Skip if the file doesn't exist
        if not os.path.exists(nc_filepath):
            print(f"  -> Warning: The file '{nc_filepath}' was not found. Skipping.")
            continue
            
        ds = xr.open_dataset(nc_filepath)
        
        # Try to pull the exact beta value from the netCDF file for the legend
        try:
            beta_val = float(ds['beta'].values)
            label_suffix = f" ($\\beta$ = {beta_val:.4f})"
        except KeyError:
            # Fallback to the filename if the beta variable isn't found
            filename = os.path.basename(nc_filepath)
            label_suffix = f" ({filename})"
        
        # Extract variables
        ky = ds['ky'].values
        freq = ds['omega'].isel(t=-1, kx=0, ri=0).values
        gamma = ds['omega'].isel(t=-1, kx=0, ri=1).values
        
        # Plot Growth Rate (Gamma) on top subplot
        ax1.plot(ky, gamma, marker='o', linestyle='-',linewidth=0.5, label=f'Growth Rate{label_suffix}')
        
        # Plot Real Frequency (Omega) on bottom subplot
        ax2.plot(ky, freq, marker='s', linestyle='-',linewidth=0.5, label=f'Real Freq{label_suffix}')
        
        # Close the dataset
        ds.close()

    # Format the Growth Rate subplot
    ax1.set_ylabel('Growth Rate $[v_{th}/a]$')
    ax1.set_title('Linear Growth Rate and Frequency vs $k_y$')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left') # Moves legend slightly outside
    
    # Format the Real Frequency subplot
    ax2.set_xlabel('$k_y \\rho_i$')
    ax2.set_ylabel('Real Frequency $[v_{th}/a]$')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Adjust layout to fit the external legends and show
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Check if the user provided at least one file path argument
    if len(sys.argv) < 2:
        print("Usage: python plot_omega.py <outputfile1> [outputfile2 ...]")
        sys.exit(1)
        
    # Get all file paths from the command line (everything after the script name)
    file_paths = sys.argv[1:]
    
    # Run the plotting function
    plot_growth_and_freq(file_paths)