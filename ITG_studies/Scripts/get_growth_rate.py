import sys
import glob
import xarray as xr

def analyze_gs2_output(target_path):
    # 1. Search for the .out.nc file in the provided directory
    # If the user passed a direct file instead of a directory, handle that too
    if target_path.endswith('.out.nc'):
        nc_files = [target_path]
    else:
        # Look inside the directory for any file ending in .out.nc
        target_path = target_path.rstrip('/')
        search_pattern = f"{target_path}/*.out.nc"
        nc_files = glob.glob(search_pattern)

    # 2. Check if a file was actually found
    if not nc_files:
        print(f"Error: No .out.nc file found in '{target_path}'.")
        return
    elif len(nc_files) > 1:
        print(f"Warning: Multiple .out.nc files found. Analyzing the first one: {nc_files[0]}")
    
    filename = nc_files[0]
    
    # 3. Extract the data
    try:
        ds = xr.open_dataset(filename)

        # Extract omega at the final time step (t=-1)
        omega_complex = ds['omega'].isel(t=-1)

        # ri=0 is Real Frequency (ω), ri=1 is Growth Rate (γ)
        # .squeeze() handles any lingering length-1 dimensions safely
        real_freq = omega_complex.isel(ri=0).squeeze().values
        growth_rate = omega_complex.isel(ri=1).squeeze().values

        print(f"File: {filename}")
        print(f"--- Final Linear Results ---")
        print(f"Real Frequency (ω): {real_freq.item():.5f}")
        print(f"Growth Rate (γ):    {growth_rate.item():.5f}")
        print(f"----------------------------")

        ds.close()

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    # Check if the user provided a directory argument
    if len(sys.argv) < 2:
        print("Usage: python get_growth_rate.py <directory_or_file_path>")
    else:
        target = sys.argv[1]
        analyze_gs2_output(target)