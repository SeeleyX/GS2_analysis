import io
import pandas as pd
import matplotlib.pyplot as plt

# Your data
data = """series,x,y,f
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

df = pd.read_csv(io.StringIO(data))

# Filter data based on the 'f' flag
df_pos = df[df['f'] == 1]
df_neg = df[df['f'] == -1]

# Setup plot
fig, ax = plt.subplots(figsize=(7, 5))

# Plot +1 as filled circles and -1 as small x's
ax.scatter(df_pos['x'], df_pos['y'], color='c', marker='o', s=50)
ax.scatter(df_neg['x'], df_neg['y'], color='c', marker='x', s=50)

# Axis Labels and Formatting
ax.set_xlabel(r'$k_y \rho_i$', fontsize=12)
ax.set_ylabel(r'Growth Rate $\gamma / (c_s / L)$', fontsize=12)
ax.grid(True, which="both", linestyle="--", linewidth=0.5)
ax.legend(loc='upper left')

# Toggle scale as needed:
ax.set_xscale('log')
ax.set_yscale('log')

plt.tight_layout()
plt.savefig('gyro_plot.png', dpi=300)