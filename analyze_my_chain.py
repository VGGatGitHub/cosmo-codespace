import numpy as np
import matplotlib.pyplot as plt
from cobaya.output import load_samples
from getdist import plots, MCSamples

# ---------------------------------------------------------
# 1. Load the chain
# ---------------------------------------------------------
prefix = "mpi_chains/planck_tttee"
print("reading:",prefix)
try:
  getdist_chains = load_samples(prefix, combined=True, to_getdist=True, skip=0)
  r_minus_1_overall0=getdist_chains.getGelmanRubin()
  print(f"skip=0, R-1={r_minus_1_overall0}")
  for nskip in [.1,.2,.25,.3,.35,.4]:
    getdist_chains = load_samples(prefix, combined=True, to_getdist=True, skip=nskip)
    r_minus_1_overall=getdist_chains.getGelmanRubin()
    print(f"skip={nskip}, R-1={r_minus_1_overall}")
    if r_minus_1_overall0 > r_minus_1_overall: skip=nskip; r_minus_1_overall0=r_minus_1_overall;
  print(f"Overall Gelman-Rubin R-1 (worst parameter): {r_minus_1_overall0:.4f}, skip={skip}")
except Exception as e:
  print(f"WARNING: R-1 value was not computed! {e}")
  skip=0

chains = load_samples(prefix, combined=True, to_getdist=False, skip=skip)

param_names = list(chains.columns)

print("\n=== Loaded Chain Information ===")
print(f"Total samples: {chains.data.shape[0]}")
print(f"Total parameters: {len(param_names)}")


# ---------------------------------------------------------
# 2. Cosmological parameters (using ln_A_s_1e10 explicitly)
# ---------------------------------------------------------
cosmo_params = [
    "H0",
    "omega_b",
    "omega_cdm",
    "tau_reio",
    "n_s",
    "ln_A_s_1e10",
]

# Verify they exist
cosmo_params_present = [p for p in cosmo_params if p in param_names]

# If ln_A_s_1e10 exists in the raw chain, keep it even if some loader conversion drops it
for p in cosmo_params:
    if p not in cosmo_params_present:
        print(f"\nNote: {p} found in chain but not in initial parameter list - derived? Adding it!")
        cosmo_params_present.append(p)

extra_params = [p for p in param_names if p not in cosmo_params_present]

print("\n=== Cosmological Parameters Found ===")
for p in cosmo_params_present:
    print(" ", p)

print("\n=== Nuisance Parameters (not shown) ===")
print(f"Count: {len(extra_params)}")
print("Example:", extra_params[:5], "...")

# ---------------------------------------------------------
# 3. Means and standard deviations
# ---------------------------------------------------------
print("\n=== Cosmological Parameter Means and Standard Deviations ===")
for name in cosmo_params_present:
    mean = chains.data[name].mean()
    std = chains.data[name].std()
    print(f"{name:<12}  mean = {mean: 8.6f}   std = {std: 4.2g}")

# ---------------------------------------------------------
# 4. Best-fit values
# ---------------------------------------------------------
best_idx = int(chains.data["minuslogpost"].idxmax()) #VGG:it was idxmin but it should be idxmax
best_sample = chains.data.iloc[best_idx]

print("\n=== Best-fit Cosmological Parameters ===")
for name in cosmo_params_present:
    bf = best_sample[name]
    unc = chains.data[name].std()
    print(f"{name:<12}  best = {bf: 8.6g}   ±{unc: 4.2g}")

# ---------------------------------------------------------
# 5. χ² breakdown
# ---------------------------------------------------------
print("\n=== Likelihood χ² Breakdown ===")
# The getdist `MCSamples` object does not expose per-likelihood loglikes_by_name.
# The chain contains chi2 columns named like 'chi2__<likename>' — extract those.
chi2_names = [n for n in param_names if n.startswith('chi2__')]

# Identify Planck segment names (exclude aggregated 'chi2__CMB' if present)
planck_seg_names = [n for n in chi2_names if 'planck_2018' in n]

# Compute sum of Planck segments from the best-fit sample
sum_planck = 0.0
for name in planck_seg_names:
    sum_planck += float(best_sample[name])

total_chi2 = 0.0
for name in chi2_names:
    # avoid printing 'chi2__CMB' twice (we already printed reported vs sum)
    if name == 'chi2__CMB':
        continue
    chi2 = float(best_sample[name])
    total_chi2 += chi2
    like_label = name.replace('chi2__', '')
    ndat = "N/A"
    print(f"{like_label:40s}  χ² = {chi2: .3f}   N_data = {ndat}")

print(f"{'Total (sum segments):':40s}  χ² = {total_chi2: .3f}")

# Report CMB aggregate if available and compare to sum of segments
if 'chi2__CMB' in param_names:
    cmb_val = float(best_sample['chi2__CMB'])
    diff = cmb_val - sum_planck
    print(f"\n{'CMB':5s}  χ² (reported) = {cmb_val: .3f}   χ² (sum segments) = {sum_planck: .3f}   Δ = {diff: .3f}")

# ---------------------------------------------------------
# 6. Covariance and correlation matrices (cosmology only)
# ---------------------------------------------------------
print("\n=== Cosmological Parameter Covariance Matrix ===")

cov_cosmo = chains.data[cosmo_params_present].cov().values

# Print header with parameter names
header = ' '.join(f"{p:>8s}" for p in cosmo_params_present)
print(f"{'':5s} {header}")

# Print covariance with 8.2e formatting and row labels
for name, row in zip(cosmo_params_present, cov_cosmo):
    row_str = ' '.join(f"{v:8.2e}" for v in row)
    print(f"{name:12s} {row_str}")

print("\n=== Cosmological Parameter Correlation Matrix ===")
stds = np.sqrt(np.diag(cov_cosmo))
corr_cosmo = cov_cosmo / np.outer(stds, stds)

# Print header for correlation matrix
print(f"{'':5s} {header}")
# Print correlation matrix with 5.2f formatting and row labels
for name, row in zip(cosmo_params_present, corr_cosmo):
    row_str = ' '.join(f"{v:5.2f}" for v in row)
    print(f"{name:12s} {row_str}")

# ---------------------------------------------------------
# 7. Triangle plot
# ---------------------------------------------------------
print("\nGenerating triangle plot for cosmological parameters...")

samples_array = chains.data[cosmo_params_present].values

latex_labels = {
    "omega_b": r"\omega_b",
    "omega_cdm": r"\omega_{\rm cdm}",
    "H0": r"H_0",
    "tau_reio": r"\tau_{\rm reio}",
    "n_s": r"n_s",
    "ln_A_s_1e10": r"\ln(10^{10}A_s)",
}

samples = MCSamples(
    samples=samples_array,
    names=cosmo_params_present,
    labels=[latex_labels.get(p, p) for p in cosmo_params_present]
)

g = plots.get_subplot_plotter()
g.triangle_plot(samples, filled=True)

plot_path = prefix+"_triangle.png"
plt.tight_layout()
plt.savefig(plot_path, dpi=200)
print(f"\nTriangle plot generated and saved to: {plot_path}")
