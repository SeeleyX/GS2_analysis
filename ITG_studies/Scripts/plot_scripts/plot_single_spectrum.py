import sys
import os
import glob
import re
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def extract_miller_params_from_in_file(base_dir):
    """Scans the directory for a GS2 .in file and extracts eps, akappa, and tri."""
    in_files = glob.glob(f"{base_dir}/**/*.in", recursive=True)
    
    params = {'eps': 0.18, 'akappa': 1.0, 'tri': 0.0}
    
    if in_files:
        target_file = in_files[0]
        print(f"DEBUG - Reading parameters from: {target_file}")
        
        with open(target_file, 'r') as f:
            content = f.read()
            
            # This regex pattern catches standard decimals AND scientific notation (like 0.18E+01)
            num_pattern = r'([+-]?\d*\.?\d+(?:[eEdD][+-]?\d+)?)'
            
            eps_match = re.search(r'\beps\s*=\s*' + num_pattern, content)
            kappa_match = re.search(r'\bakappa\s*=\s*' + num_pattern, content)
            tri_match = re.search(r'\btri\s*=\s*' + num_pattern, content)
            
            # Helper to convert Fortran 'D/d' to Python 'E/e' before converting to float
            def parse_fortran_float(val_str):
                return float(re.sub(r'[dD]', 'e', val_str))
            
            if eps_match: params['eps'] = parse_fortran_float(eps_match.group(1))
            if kappa_match: params['akappa'] = parse_fortran_float(kappa_match.group(1))
            if tri_match: params['tri'] = parse_fortran_float(tri_match.group(1))
            
    return params

def plot_ky_spectrum_and_geometry(base_dir, param_type, target_val=None):
    if target_val is None:
        match = re.search(rf'{param_type}_?([0-9.]+)', base_dir)
        if match:
            target_val = float(match.group(1))
        else:
            print(f"Error: Could not determine '{param_type}' value from folder name '{base_dir}'.")
            return

    print(f"Extracting data from '{base_dir}' for {param_type} = {target_val}...")

    search_pattern = f"{base_dir}/**/*.out.nc"
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    ky_list = []
    gamma_list = []
    omega_list = []

    for file in nc_files:
        try:
            match = re.search(rf'{param_type}_?([0-9.]+)', file)  
            if match:
                file_val = float(match.group(1))
                if file_val != target_val:
                    continue  
            else:
                continue
                
            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            omega_complex = ds['omega'].isel(t=-1)
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            ky_list.append(ky)
            gamma_list.append(growth_rate)
            omega_list.append(real_freq)
            ds.close()
            
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not ky_list:
        print(f"No valid data found matching {param_type} = {target_val}.")
        return

    sorted_indices = np.argsort(ky_list)
    ky_arr = np.array(ky_list)[sorted_indices]
    gamma_arr = np.array(gamma_list)[sorted_indices]
    omega_arr = np.array(omega_list)[sorted_indices]

    # --- Setup the Miller Parameters ---
    miller_params = extract_miller_params_from_in_file(base_dir)
    print(f"DEBUG - Extracted Miller Params: {miller_params}")
    
    r_max = miller_params['eps']
    R0 = 1.0  # Normalized major radius
    kappa = miller_params['akappa']
    delta = miller_params['tri']
    theta = np.linspace(0, 2 * np.pi, 100)

    # --- Plotting ---
    fig, (ax_spec, ax_geom) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [2, 1]})

    # Panel 1: Spectrum
    color1 = 'tab:red'
    ax_spec.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax_spec.set_ylabel(r'Growth Rate ($\gamma [v_{th}/a]$)', color=color1, fontsize=12)
    ax_spec.plot(ky_arr, gamma_arr, marker='o', color=color1, linewidth=2, label=r'$\gamma$')
    ax_spec.tick_params(axis='y', labelcolor=color1)
    ax_spec.grid(True, linestyle='--', alpha=0.6)

    ax_spec_twin = ax_spec.twinx()  
    color2 = 'tab:blue'
    ax_spec_twin.set_ylabel(r'Real Frequency ($\omega [v_{th}/a]$)', color=color2, fontsize=12)
    ax_spec_twin.plot(ky_arr, omega_arr, marker='s', color=color2, linewidth=2, linestyle='--', label=r'$\omega$')
    ax_spec_twin.tick_params(axis='y', labelcolor=color2)
    ax_spec_twin.axhline(0, color='black', linewidth=1, linestyle=':')

    ax_spec.set_title(rf'ITG Growth Rate Spectrum ({param_type} = {target_val})', fontsize=14)

    # Panel 2: Flux Surface Geometry (Nested)
    num_surfaces = 5
    # Create an array of minor radii from a small core value up to your r_max
    radii = np.linspace(r_max / num_surfaces, r_max, num_surfaces)
    
    for r_val in radii:
        R_surf = R0 + r_val * np.cos(theta + delta * np.sin(theta))
        Z_surf = kappa * r_val * np.sin(theta)
        
        # Make the outermost surface thicker, inner ones thinner
        is_boundary = (r_val == r_max)
        line_w = 2 if is_boundary else 1
        alpha_v = 1.0 
        
        ax_geom.plot(R_surf, Z_surf, color='black', linewidth=line_w, alpha=alpha_v)

    ax_geom.set_aspect('equal') 
    ax_geom.set_xlabel('R (Normalized)', fontsize=12)
    ax_geom.set_ylabel('Z (Normalized)', fontsize=12)
    
    # THE FIX: Added the "r" before the string to make it raw
    geom_title = rf"Geometry: $\kappa$={kappa}, $\delta$={delta}"
    ax_geom.set_title(geom_title, fontsize=14)
    ax_geom.grid(True, linestyle=':', alpha=0.7)

    fig.tight_layout()
    
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) 
    save_path = os.path.join(output_dir, f"ky_spectrum_with_geom_{param_type}_{target_val}.png")
    plt.savefig(save_path, dpi=300)
    
    print(f"Plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python plot_single_spectrum.py <folder_name> <param_type> [target_val]")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    param_type = sys.argv[2]
    target_value = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    plot_ky_spectrum_and_geometry(target_directory, param_type, target_value)