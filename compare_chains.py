

# Install trianglechain package for plotting contours if you do not already have it
# Note: shell-style pip install commands are not valid in regular Python scripts.
import subprocess
import sys

# Install trianglechain package for plotting contours if you do not already have it
# Using subprocess avoids relying on importing pip as a module.
try:
    import trianglechain
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'trianglechain'])
    import trianglechain

import numpy as np
from trianglechain import TriangleChain
import matplotlib.pyplot as plt
import matplotlib
import os

# R-1 and skip  

from getdist import MCSamples
from cobaya.output import load_samples

###
new_model = False

if new_model:
    new_skip = 0.1
    new_prefix= "new_model/h_omega_l"
    new_chain_path ="./new_model/h_omega_l"
    new_gd_chain = load_samples(new_prefix, combined=True, to_getdist=True,skip=new_skip)

    new_r1 = new_gd_chain.getGelmanRubin()
    print(f"\n{new_prefix}")
    print("R-1 =", new_r1)
    print(f"skip = {new_skip}")

####
skip = 0.1
prefix = "mpi_chains/planck_tttee"
my_chain_path = "./mpi_chains/planck_tttee"
gd_chain = load_samples(prefix, combined=True, to_getdist=True,skip=skip)

r1 = gd_chain.getGelmanRubin()
print(f"\n{prefix}")
print("R-1 =", r1)
print(f"skip = {skip}")

# Define the paths for the old planck chains
base_planck_chain_dir = "./planck2018_chains/base/plikHM_TTTEEE_lowl_lowE_lensing/" 
base_planck_file_prefix = os.path.join(base_planck_chain_dir, "base_plikHM_TTTEEE_lowl_lowE_lensing")  # Assuming the first file is _1.txt
bao_chain_path = os.path.join(base_planck_chain_dir, "base_plikHM_TTTEEE_lowl_lowE_lensing_post_BAO")


# Helper function to transform raw Planck data into a structured numpy array
# Assumes the first two columns are weights and minuslogpost in raw .txt files
def transform_planck_raw_to_paramchain(data_array, names_list, indices_list):
    # If it's already a structured array (e.g., from getdist), return as is.
    if data_array.dtype.names is not None:
        return data_array

    n_rows = data_array.shape[0]
    if n_rows == 0: # Handle empty data array case
        return np.empty(0, dtype=[(name, 'f8') for name in names_list])

    # Create a structured dtype for the parameters we care about
    # The format 'f8' denotes float64
    dtype_fields = [(name, 'f8') for name in names_list]
    rec = np.empty(n_rows, dtype=dtype_fields)

    for i, param_name in enumerate(names_list):
        col_index = indices_list[i]
        if col_index >= data_array.shape[1]:
            print(f"Warning: Column index {col_index} for parameter '{param_name}' is out of bounds for data with {data_array.shape[1]} columns. Filling with NaN.")
            rec[param_name] = np.nan
            continue

        param_data = data_array[:, col_index]

        if param_name == 'h':
            # Convert H0 to h if values are in H0 scale (e.g., > 10, typically ~60-80)
            if np.mean(param_data) > 10: # Check if mean is in H0 range
                rec[param_name] = param_data / 100.0
            else:
                rec[param_name] = param_data
        else:
            rec[param_name] = param_data

    # Add a check for all-NaN columns before returning
    for name in names_list:
        if np.all(np.isnan(rec[name])):
            print(f"Warning: Parameter '{name}' has all NaN values after transformation. This may cause plotting issues.")

    return rec



# Desired cosmological parameters for plotting in a specific order
plotting_cosmo_params = ['h','omega_b','omega_cdm', 'tau_reio', 'ln_A_s_1e10','n_s']

# --- Dynamic determination of general_names and general_indices for Planck Base and Planck+BAO chains ---
paramnames_file_path = base_planck_file_prefix + '.paramnames'
# Temporarily store (processed_param_name, original_index) tuples
found_params_temp = []

print(f"\nAttempting to dynamically load parameter names and indices from: {paramnames_file_path}")
if os.path.exists(paramnames_file_path):
    with open(paramnames_file_path, 'r') as f:
        for i, line in enumerate(f):
            # Split by whitespace, max 1 split to separate name from label
            parts = line.strip().split(None, 1)
            if not parts:
                continue
            param_name_raw = parts[0]

            processed_param_name = param_name_raw # Start with raw name

            # Mapping common aliases to the desired plotting names
            if param_name_raw == 'H0*':
                processed_param_name = 'h'
            elif param_name_raw == 'omegabh2':
                processed_param_name = 'omega_b'
            elif param_name_raw == 'omegach2':
                processed_param_name = 'omega_cdm'
            elif param_name_raw == 'tau': # Sometimes just 'tau' for reio optical depth
                processed_param_name = 'tau_reio'
            elif param_name_raw == 'logA': # log(10^10 A_s)
                processed_param_name = 'ln_A_s_1e10'
            elif param_name_raw == 'ns':
                processed_param_name = 'n_s'

            # Check if this processed parameter is one of our target plotting parameters
            if processed_param_name in plotting_cosmo_params:
                # Add if not already found (to avoid duplicates from aliases if present)
                if processed_param_name not in [p[0] for p in found_params_temp]:
                    found_params_temp.append((processed_param_name, i))

    # Sort the dynamically found parameters to match the desired plotting order
    # The key=lambda x: plotting_cosmo_params.index(x[0]) is correct
    ordered_params_with_indices = sorted(
        found_params_temp,
        key=lambda x: plotting_cosmo_params.index(x[0])
    )
    general_names = [name for name, _ in ordered_params_with_indices]
    general_indices = [2+idx for _, idx in ordered_params_with_indices]

    if general_names:
        print(f"Successfully loaded {len(general_names)} cosmological parameters and their indices from .paramnames file for Planck Base and Planck+BAO.")
        print(f"General names: {general_names}")
        print(f"General indices: {general_indices}")
    else:
        print("Warning: No desired cosmological parameters found in .paramnames using flexible parsing. Falling back to hardcoded defaults.")
        # Fallback to hardcoded if no relevant params found
        general_names = plotting_cosmo_params
        general_indices = [2,3,4,5,6,7] # Assuming weight, minuslogpost then parameters
else:
    print(f"Warning: .paramnames file not found at {paramnames_file_path}. Falling back to hardcoded general_names and general_indices for Planck Base and Planck+BAO.")
    general_names = plotting_cosmo_params
    general_indices = [2,3,4,5,6,7] # Assuming weight, minuslogpost then parameters

# For 'My Chains', use my_chain_indices as previously corrected.
# This assumes it also has weight/minuslogpost, then parameters in the same order as general. The H0 to h conversion is handled in transform_planck_raw_to_paramchain.
my_chain_indices = [2,3,4,5,6,7]


if new_model: 
    new_chain_indices=[3,4,5,6,7,8]
    if new_prefix == prefix:  
        new_chain_indices = my_chain_indices


params = general_names # These are the parameter names for plotting

# Parameter ranges for the plotting (kept as hardcoded from original cell for now)
ranges = {
    'omega_b': [0.022, 0.023],
    'omega_cdm': [0.11, 0.125],
    'h': [0.65, 0.75],
    'tau_reio': [0.01, 0.13],
    'ln_A_s_1e10': [2.9, 3.2],
    'n_s': [0.95, 0.99],
}

def apply_skip_burnin(chain_array, skip):
    """
    Replicates GetDist's 'skip'/'ignore_rows' behavior for a single raw chain file.

    Parameters
    ----------
    chain_array : np.ndarray
        Raw 2D array loaded from a single chain file (rows = samples).
    skip : float
        If 0 <= skip < 1: treated as a FRACTION of rows to discard from the
        start of this file (GetDist's default 'ignore_rows' behavior).
        If skip >= 1: treated as an absolute NUMBER of rows to discard from
        the start of this file.

    Returns
    -------
    np.ndarray
        The chain array with burn-in rows removed.
    """
    if chain_array is None or chain_array.size == 0 or skip <= 0:
        return chain_array

    n_rows = chain_array.shape[0]

    if skip < 1:
        n_skip = int(np.floor(n_rows * skip))
    else:
        n_skip = int(skip)

    n_skip = min(n_skip, n_rows)  # safety: never skip more rows than exist

    return chain_array[n_skip:]

# Function to load and transform chains, now flexible for multi-file or single-file inputs
def load_and_transform_chain_flexible(file_path_or_prefix, is_multi_file, dot_or_dash, 
                                      chain_label, current_names, current_indices,skip=0.3):
    planck_chain_tot = None
    if is_multi_file:
        # Load multiple files (e.g., _1.txt, _2.txt, etc.)
        for i in range(1, 5): # Assuming chain files are _1.txt, _2.txt, _3.txt, _4.txt
            chain_path = f'{file_path_or_prefix}{dot_or_dash}{i}.txt'
            try:
                planck_chain_raw = np.loadtxt(chain_path)
                planck_chain_raw = apply_skip_burnin(planck_chain_raw, skip)
                if planck_chain_tot is None:
                    planck_chain_tot = planck_chain_raw
                else:
                    planck_chain_tot = np.vstack((planck_chain_tot, planck_chain_raw))
            except Exception as e:
                print(f"Could not load multi-file part \n{chain_path} \nfor \n'{chain_label}': {e}")
                continue
    else:
        # Load a single specified file
        try:
            planck_chain_raw = np.loadtxt(file_path_or_prefix)
            planck_chain_tot = planck_chain_raw
        except Exception as e:
            print(f"Could not load single file \n'{file_path_or_prefix}' \nfor \n'{chain_label}': {e}")

    if planck_chain_tot is not None and planck_chain_tot.size > 0:
        return transform_planck_raw_to_paramchain(planck_chain_tot, current_names, current_indices)
    else:
        print(f"No valid data loaded or empty data for '{chain_label}'.")
        return None

# Load and transform chains using the new flexible function
print(f"Loading Planck Base chains from \n{base_planck_file_prefix}...")
planck_chain_1 = load_and_transform_chain_flexible(base_planck_file_prefix, True, "_", "Planck Base", general_names, general_indices)

if new_model:
    print(f"Loading New chain from \n{new_chain_path}...")
    planck_chain_2 = load_and_transform_chain_flexible(new_chain_path, True, ".", "New Model", general_names, new_chain_indices,skip=new_skip)
else:
    print(f"Loading Planck + BAO chain from \n{bao_chain_path}...")
    planck_chain_2 = load_and_transform_chain_flexible(bao_chain_path, True, "_", "Planck + BAO", general_names, general_indices)

print(f"Loading chains from \n{my_chain_path}...")
planck_chain_3 = load_and_transform_chain_flexible(my_chain_path, True, ".", "My Chains", general_names, my_chain_indices,skip=skip)

# Prepare and plot the distributions
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['legend.shadow'] = False
matplotlib.rcParams['legend.frameon'] = False
plt.rcParams.update({"text.usetex": False}) # Set to False to avoid LaTeX errors

tri = TriangleChain(density_estimation_method='smoothing', params=params, ranges=ranges,
                    labels=[r"h", r"$\omega_b$", r"$\omega_{cdm}$", r"$\tau_{\rm reio}$", r"$\ln(10^{10}A_s)$", r"$n_s$" ])

if planck_chain_1 is not None:
    tri.contour_cl(planck_chain_1, color='red', label="Planck Base")
if planck_chain_2 is not None:
    if new_model:
        tri.contour_cl(planck_chain_2, color='blue', label="New Chains")
    else:
        tri.contour_cl(planck_chain_2, color='blue', label="Planck + BAO")
if planck_chain_3 is not None:
    tri.contour_cl(planck_chain_3, color='green', label="My Planck Chains")

plt.suptitle('Triangle Plots for Chain Comparison', y=1.02)
#plt.show()

# Create a unique filename for the plot
plot_filename = f"triangle_plot_comparison.png"
plot_path = os.path.join("./", plot_filename)

plt.savefig(plot_path, bbox_inches='tight', dpi=300)
print(f"\nTriangle plot generated and saved to: {plot_path}")
