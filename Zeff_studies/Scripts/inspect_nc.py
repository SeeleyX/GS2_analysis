import sys
import xarray as xr

# --- ANSI Color Codes for the Terminal ---
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'  # Resets the color back to normal

def inspect_gs2_output(file_path):
    print(f"\n{Colors.BOLD}Opening and inspecting: '{file_path}'...{Colors.RESET}\n")
    
    try:
        ds = xr.open_dataset(file_path)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Could not find the file '{file_path}'.{Colors.RESET}")
        return
    except Exception as e:
        print(f"{Colors.RED}Error opening file: {e}{Colors.RESET}")
        return

    # 1. Print Dimensions (the axes of your data)
    print(f"{Colors.CYAN}{Colors.BOLD}" + "-" * 50)
    print(" 📏 DIMENSIONS (Grid Sizes)")
    print("-" * 50 + f"{Colors.RESET}")
    
    for dim, size in ds.dims.items():
        print(f"  * {Colors.GREEN}{dim:<10}{Colors.RESET} : {size} elements")

    # 2. Print Coordinates (the actual values along those axes)
    print(f"\n{Colors.CYAN}{Colors.BOLD}" + "-" * 50)
    print(" 🗺️  COORDINATES (Grid Variables)")
    print("-" * 50 + f"{Colors.RESET}")
    
    for coord_name, coord_data in ds.coords.items():
        dims_str = ", ".join(coord_data.dims)
        print(f"  * {Colors.BLUE}{coord_name:<10}{Colors.RESET} : depends on ({dims_str})")

    # 3. Print Data Variables (the actual physics outputs)
    print(f"\n{Colors.CYAN}{Colors.BOLD}" + "-" * 50)
    print(" 📊 PHYSICS VARIABLES (Outputs)")
    print("-" * 50 + f"{Colors.RESET}")
    
    for var_name, var_data in ds.data_vars.items():
        dims_str = ", ".join(var_data.dims)
        desc = var_data.attrs.get('description', var_data.attrs.get('long_name', ''))
        
        print(f"  * {Colors.YELLOW}{Colors.BOLD}{var_name:<15}{Colors.RESET} : depends on ({dims_str})")
        if desc:
            print(f"      ↳ {desc}")

    ds.close()
    print(f"\n{Colors.CYAN}{Colors.BOLD}" + "-" * 50)
    print("Inspection complete.")
    print("-" * 50 + f"{Colors.RESET}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Usage: python inspect_nc.py <path_to_a_single_out_nc_file>{Colors.RESET}")
        print("Example: python inspect_nc.py Inputs/ITG_kyscan/tri_0.1/tri_0.1.out.nc")
        sys.exit(1)
        
    target_file = sys.argv[1]
    inspect_gs2_output(target_file)