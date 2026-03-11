import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# Load the GS2 output file
filename = '../Inputs/cyclone_itg_miller_base.out.nc'
ds = xr.open_dataset(filename)

# 1. Time Coordinate
t = ds['t'].values

# 2. Extract Frequency and Growth Rate over Time
# .squeeze() safely drops kx and ky dimensions if they are length 1
real_freq_t = ds['omega'].isel(ri=0).squeeze().values
growth_rate_t = ds['omega'].isel(ri=1).squeeze().values

# 3. Extract Potential Amplitude over Time
# 'phi2' is the standard GS2 variable for the squared potential amplitude
phi2_t = ds['phi2'].squeeze().values

# 4. Extract Final Ballooning Structure (No 't' dimension)
phi_ri = ds['phi'].squeeze()
phi_complex = phi_ri.isel(ri=0) + 1j * phi_ri.isel(ri=1)
theta = ds['theta'].values
phi_mag = np.abs(phi_complex)

# --- Plotting ---
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# Panel 1: Growth Rate vs Time
axs[0, 0].plot(t, growth_rate_t, color='blue', label=r'$\gamma$')
axs[0, 0].set_xlabel('Time ($R/v_{ti}$)')
axs[0, 0].set_ylabel('Growth Rate')
axs[0, 0].set_title(r'Linear Growth Rate ($\gamma$) vs Time')
axs[0, 0].grid(True, linestyle='--')

# Panel 2: Real Frequency vs Time
axs[0, 1].plot(t, real_freq_t, color='orange', label=r'$\omega$')
axs[0, 1].set_xlabel('Time ($R/v_{ti}$)')
axs[0, 1].set_ylabel('Real Frequency')
axs[0, 1].set_title(r'Mode Frequency ($\omega$) vs Time')
axs[0, 1].grid(True, linestyle='--')

# Panel 3: Potential Amplitude vs Time (Log Scale)
# A straight line on a log plot indicates clean exponential growth
axs[1, 0].plot(t, phi2_t, color='green')
axs[1, 0].set_yscale('log') 
axs[1, 0].set_xlabel('Time ($R/v_{ti}$)')
axs[1, 0].set_ylabel(r'$|\phi|^2$')
axs[1, 0].set_title('Potential Amplitude vs Time (Log Scale)')
axs[1, 0].grid(True, linestyle='--')

# Panel 4: Final Ballooning Structure
axs[1, 1].plot(theta, phi_mag / np.max(phi_mag), color='purple')
axs[1, 1].axvline(0, color='red', linestyle=':', alpha=0.5, label='Outboard Midplane')
axs[1, 1].set_xlabel(r'Poloidal Angle $\theta$ (radians)')
axs[1, 1].set_ylabel(r'$|\phi| / |\phi|_{max}$')
axs[1, 1].set_title('Final Eigenmode Structure')
axs[1, 1].legend()
axs[1, 1].grid(True, linestyle='--')

plt.tight_layout()
plt.show()