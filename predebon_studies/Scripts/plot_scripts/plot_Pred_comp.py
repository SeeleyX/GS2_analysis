import sys
import os
import glob
import re
import io
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# --- LITERATURE DATA (PREDEBON ET AL. 2023) ---
PAPER_DATA = """series,x,y,f
84793_rhot_0.96,0.04907058732088477,0.11086031784226905,1
84793_rhot_0.96,0.1022496513312955,0.2852488358068424,1
84793_rhot_0.96,0.19930440990393464,0.3217086117293842,1
84793_rhot_0.96,0.2974609438908062,0.19545409601731858,1
84793_rhot_0.96,0.9889380389907361,0.6620572143707689,-1
84793_rhot_0.96,1.181581732618102,1.0711511200934258,-1
84793_rhot_0.96,1.3503140378698728,1.4101123990690794,-1
84793_rhot_0.96,1.577856970853078,1.7035044938756025,-1
84793_rhot_0.96,1.7635054720471388,1.9545409601731878,-1
84793_rhot_0.96,1.9276321212478975,2.057940602869778,-1
84793_rhot_0.96,2.4620924014946266,2.204365381849705,-1
84793_rhot_0.96,2.8769823534612957,2.0936087387579905,-1
84793_rhot_0.96,3.437414337286243,1.7936237390528276,-1
84793_rhot_0.96,4.841855824371818,1.8563365529925646,-1
84793_rhot_0.96,4.907058732088477,3.1622776601683795,-1
84793_rhot_0.96,5.733952702606364,3.6282858286906725,-1
84793_rhot_0.96,6.850918360881589,2.952223641322022,-1
84793_rhot_0.96,7.829243614405852,1.7936237390528276,-1
84793_rhot_0.96,29.09163405623883,10,-1
84793_rhot_0.96,74.05684692262442,38.202303649947275,-1"""

def plot_ky_spectrum(base_dir, num_avg_steps=10, vth_over_cs=1.0, L_over_a=1.0):
    """
    Parses a directory of ky scans, extracts growth rates and frequencies,
    normalizes the scale, and plots everything on a single plot using 
    conditional shape markers based on the sign of the real frequency.
    """
    # Extract rho value for the title/filename
    match = re.search(r'rho_([0-9.]+)', base_dir)
    rho_val = match.group(1) if match else "0.96"

    # 1. Find all .out.nc files
    search_pattern = os.path.join(base_dir, "**", "*.out.nc")
    nc_files = glob.glob(search_pattern, recursive=True)
    
    if not nc_files:
        print(f"Error: No .out.nc files found inside '{base_dir}'.")
        return

    print(f"Found {len(nc_files)} files. Processing data...")

    ky_list, gamma_list, omega_list = [], [], []

    # 2. Extract and time-average data
    for file in nc_files:
        try:
            ds = xr.open_dataset(file)
            ky = float(ds['ky'].squeeze().values)
            
            omega_window = ds['omega'].isel(t=slice(-num_avg_steps, None))
            omega_complex = omega_window.mean(dim='t')
            
            real_freq = float(omega_complex.isel(ri=0).squeeze().values)
            growth_rate = float(omega_complex.isel(ri=1).squeeze().values)
            
            ky_list.append(ky)
            gamma_list.append(growth_rate)
            omega_list.append(real_freq)
            ds.close()
        except Exception as e:
            print(f"Skipping {file} due to error: {e}")

    if not ky_list:
        print("Error: No valid data could be parsed.")
        return

    # 3. Sort arrays by wavenumber
    sorted_indices = np.argsort(ky_list)
    ky_arr = np.array(ky_list)[sorted_indices]
    gamma_arr = np.array(gamma_list)[sorted_indices]
    omega_arr = np.array(omega_list)[sorted_indices]

    # --- NORMALIZATION CONVERSION ---
    freq_conversion_factor = vth_over_cs * L_over_a
    gamma_arr_scaled = gamma_arr * freq_conversion_factor
    omega_arr_scaled = omega_arr * freq_conversion_factor

    # --- LOAD AND PARSE PAPER DATA ---
    df_paper = pd.read_csv(io.StringIO(PAPER_DATA))
    df_paper_pos = df_paper[df_paper['f'] == 1]
    df_paper_neg = df_paper[df_paper['f'] == -1]

    # Define the two designated colors
    color_gs2 = 'tab:blue'
    color_paper = 'tab:orange'

    # 4. Generate the Single Consolidated Plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # --- PLOT GS2 DATA ---
    # Plot the baseline continuous simulation trace
    ax.plot(ky_arr, gamma_arr_scaled, color=color_gs2, linestyle='-', linewidth=2, zorder=2)
    
    # Dynamic marker splitting based on GS2 frequency signs
    gs2_pos_mask = omega_arr_scaled >= 0
    gs2_neg_mask = omega_arr_scaled < 0
    
    ax.scatter(ky_arr[gs2_pos_mask], gamma_arr_scaled[gs2_pos_mask], 
               color=color_gs2, marker='o', s=50, zorder=3)
    ax.scatter(ky_arr[gs2_neg_mask], gamma_arr_scaled[gs2_neg_mask], 
               color=color_gs2, marker='x', s=50, zorder=3)

    # --- PLOT PREDEBON ET AL. 2023 DATA ---
    # Circle for positive frequency, cross for negative frequency (unified color)
    ax.scatter(df_paper_pos['x'], df_paper_pos['y'], 
               color=color_paper, marker='o', s=60, zorder=4)
    ax.scatter(df_paper_neg['x'], df_paper_neg['y'], 
               color=color_paper, marker='x', s=60, zorder=4)

    # --- AXES & LOG SCALE CONFIGURATION ---
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'Poloidal Wavenumber ($k_y \rho_i$)', fontsize=12)
    ax.set_ylabel(r'Growth Rate $\gamma / (c_s / a)$', fontsize=12)
    ax.set_title(rf'Linear Growth Rate Spectrum Comparison ($\rho = {rho_val}$)', fontsize=13, pad=15)
    ax.grid(True, which="both", linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', linewidth=0.8, linestyle=':')

    # --- CUSTOM LEGEND BLOCK ---
    # Builds a clean matrix mapping 2 colors (datasets) and 2 shapes (frequencies)
    legend_elements = [
        Line2D([0], [0], color=color_gs2, lw=2, marker='o', markersize=8, label='GS2 Simulation'),
        Line2D([0], [0], color=color_paper, marker='o', markerfacecolor=color_paper, markersize=8, label='Predebon et al. 2023'),
        Line2D([0], [0], color='none', label=''), # Corrected invisible spacing element
        Line2D([0], [0], marker='o', color='darkgray', linestyle='None', markersize=8, label=r'Positive Freq. ($\omega > 0$)'),
        Line2D([0], [0], marker='x', color='darkgray', linestyle='None', markersize=8, label=r'Negative Freq. ($\omega < 0$)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', framealpha=0.95)

    plt.tight_layout()
    
    # 5. Save Output
    output_dir = "Figures"
    os.makedirs(output_dir, exist_ok=True) 
    save_path = os.path.join(output_dir, f"ky-scan_rho_{rho_val}.png")
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Consolidated plot successfully saved to: '{save_path}'")
    plt.show()

if __name__ == "__main__":
    target_directory = sys.argv[1] if len(sys.argv) > 1 else "rho_0.96"
    
    # Updated to perfectly match the GS2 default -> GENE conversion
    VT_OVER_CS = np.sqrt(2.0)  # Accounts for the GS2 sqrt(2) velocity definition
    L_OVER_A = 1.0             # Remains 1.0 because GENE L_ref = a in this run

    plot_ky_spectrum(target_directory, num_avg_steps=10, vth_over_cs=VT_OVER_CS, L_over_a=L_OVER_A)