import argparse
import glob
import os
import re
import sys

import numpy as np
from cobaya.output import load_samples as cobaya_load_samples
from getdist import loadMCSamples, plots, MCSamples


def find_chain_roots_in_directory(directory):
    roots = set()
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith('.txt'):
                m = re.match(r'(.+)_\d+\.txt$', fname)
                if m:
                    roots.add(os.path.join(root, m.group(1)))
                else:
                    roots.add(os.path.join(root, fname[:-4]))
    return sorted(roots)


def infer_chain_root(path):
    if os.path.isdir(path):
        roots = find_chain_roots_in_directory(path)
        if not roots:
            raise FileNotFoundError(
                f"No chain roots found in directory '{path}'. Expected files like '*_1.txt'."
            )
        if len(roots) == 1:
            return roots[0]
        raise ValueError(
            f"Multiple chain roots found in '{path}':\n" + '\n'.join(roots[:20]) +
            ("\n..." if len(roots) > 20 else "") +
            "\nSpecify a more specific chain root path."
        )

    if os.path.isfile(path):
        if path.endswith('.txt'):
            m = re.match(r'(.+)_\d+\.txt$', os.path.basename(path))
            return os.path.join(os.path.dirname(path), m.group(1)) if m else path[:-4]
        if path.endswith('.paramnames'):
            return path[:-len('.paramnames')]
        if path.endswith('.updated.yaml') or path.endswith('.yaml'):
            return path

    if os.path.exists(path + '.paramnames') or os.path.exists(path + '_1.txt'):
        return path
    if os.path.exists(path + '.updated.yaml'):
        return path

    raise FileNotFoundError(
        f"Could not infer a chain root from path '{path}'."
    )


def load_chain(chain_root):
    if (
        chain_root.endswith('.yaml')
        or chain_root.endswith('.updated.yaml')
        or os.path.exists(chain_root + '.updated.yaml')
    ):
        return cobaya_load_samples(chain_root, combined=True, to_getdist=True)
    if os.path.exists(chain_root + '.paramnames') and glob.glob(chain_root + '_*.txt'):
        return loadMCSamples(chain_root)
    raise FileNotFoundError(
        f"Cannot load chain root '{chain_root}'.\n"
        f"Expected either a Cobaya output prefix with '.updated.yaml' or a GetDist raw chain root with '.paramnames' and '_N.txt' files."
    )


def get_cosmo_params(param_names):
    param_groups = [
        ("omega_b", ["omega_b", "omegabh2"]),
        ("omega_cdm", ["omega_cdm", "omegach2"]),
        ("H0", ["H0"]),
        ("tau_reio", ["tau_reio", "tau"]),
        ("n_s", ["n_s", "ns"]),
        ("ln_A_s_1e10", ["ln_A_s_1e10", "logA"]),
    ]
    found = []
    display_names = {}
    for canonical, names in param_groups:
        for name in names:
            if name in param_names:
                found.append(name)
                display_names[name] = canonical
                break
    return found, display_names


def format_param(name, display_names):
    return display_names.get(name, name)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a Planck chain using either Cobaya output or raw GetDist chains."
    )
    parser.add_argument(
        "--chain-root",
        default= #"my_chains/planck_tttee", 
        "planck2018_chains/base/plikHM_TTTEEE",
        help=(
            "Path to a chain root, chain directory, or Cobaya output prefix. "
            "For raw GetDist chains this can be a directory containing '*_1.txt' files, "
            "or the root name without extension (e.g. 'planck2018_chains/base/plikHM_TTTEEE/base_plikHM_TTTEEE')."
        ),
    )
    args = parser.parse_args()

    try:
        chain_root = infer_chain_root(args.chain_root)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n... Loading chain from: {chain_root} ...")
    samples = load_chain(chain_root)
    param_names = samples.getParamNames().list()

    print("\n=== Loaded Chain Information ===")
    print(f"Total samples: {samples.numrows}")
    print(f"Total parameters: {len(param_names)}")

    cosmo_params_present, display_names = get_cosmo_params(param_names)
    extra_params = [p for p in param_names if p not in cosmo_params_present]

    print("\n=== Cosmological Parameters Found ===")
    for p in cosmo_params_present:
        print(" ", format_param(p, display_names))

    print("\n=== Nuisance Parameters (not shown) ===")
    print(f"Count: {len(extra_params)}")
    print("Example:", extra_params[:5], "...")

    print("\n=== Cosmological Parameter Means and Standard Deviations ===")
    for name in cosmo_params_present:
        mean = samples.mean(name)
        std = samples.std(name)
        print(f"{format_param(name, display_names):20s}  mean = {mean: .6g}   std = {std: .6g}")

    if hasattr(samples, "loglikes") and len(samples.loglikes) == samples.numrows:
        best_idx = int(np.argmax(samples.loglikes))
    else:
        print("\n~~~~>Warning: problem with samples.loglikes! Setting best_idx = 0!")
        best_idx = 0
    best_sample = samples.samples[best_idx]

    print("\n=== Best-fit Cosmological Parameters ===")
    for name in cosmo_params_present:
        idx = param_names.index(name)
        print(f"{format_param(name, display_names):20s}  best = {best_sample[idx]: .6g}")

    chi2_names = [n for n in param_names if n.startswith('chi2__')]
    if chi2_names:
        print("\n=== Likelihood χ² Breakdown ===")
        planck_seg_names = [n for n in chi2_names if 'planck_2018' in n]
        sum_planck = 0.0
        for name in planck_seg_names:
            idx = param_names.index(name)
            sum_planck += float(best_sample[idx])
        if 'chi2__CMB' in param_names:
            cmb_idx = param_names.index('chi2__CMB')
            cmb_val = float(best_sample[cmb_idx])
            diff = cmb_val - sum_planck
            print(f"{'CMB':40s}  χ² (reported) = {cmb_val: .3f}   χ² (sum segments) = {sum_planck: .3f}   Δ = {diff: .3f}")
        else:
            print(f"{'CMB (sum segments)':40s}  χ² (sum segments) = {sum_planck: .3f}")
        total_chi2 = 0.0
        for name in chi2_names:
            if name == 'chi2__CMB':
                idx = param_names.index(name)
                chi2 = float(best_sample[idx])
                total_chi2 += chi2
                continue
            idx = param_names.index(name)
            chi2 = float(best_sample[idx])
            total_chi2 += chi2
            like_label = name.replace('chi2__', '')
            ndat = "N/A"
            print(f"{like_label:40s}  χ² = {chi2: .3f}   N_data = {ndat}")
        print(f"\nTotal χ² = {total_chi2: .3f}")
    else:
        print("\nNo per-likelihood χ² columns found in this chain.")

    if not cosmo_params_present:
        print("\nNo recognizable cosmological parameters found. Exiting.")
        sys.exit(1)

    print("\n=== Cosmological Parameter Covariance Matrix ===")
    cov_mat = samples.getCovMat()
    cov_param_names = getattr(cov_mat, 'paramNames', None)
    if cov_param_names is None:
        print("Could not retrieve covariance parameter names. Skipping covariance matrix.")
    else:
        cov_full = cov_mat.matrix
        cov_idxs = [cov_param_names.index(p) for p in cosmo_params_present if p in cov_param_names]
        if len(cov_idxs) != len(cosmo_params_present):
            missing = [p for p in cosmo_params_present if p not in cov_param_names]
            print(f"Warning: the following cosmological parameters are not in the covariance matrix: {missing}")
        if cov_idxs:
            cov_cosmo = cov_full[np.ix_(cov_idxs, cov_idxs)]
            for row in cov_cosmo:
                print(' '.join(f"{v:8.2e}" for v in row))

            print("\n=== Cosmological Parameter Correlation Matrix ===")
            stds = np.sqrt(np.diag(cov_cosmo))
            corr_cosmo = cov_cosmo / np.outer(stds, stds)
            for row in corr_cosmo:
                print(' '.join(f"{v:5.2f}" for v in row))
        else:
            print("No cosmological parameters available in the covariance matrix.")

    print("\nGenerating triangle plot for cosmological parameters...")
    samples_array = np.array([
        samples.samples[:, param_names.index(p)]
        for p in cosmo_params_present
    ]).T
    plot_labels = [format_param(p, display_names).replace('_', r'\_') for p in cosmo_params_present]
    plot_samples = MCSamples(
        samples=samples_array,
        names=cosmo_params_present,
        labels=plot_labels,
    )
    g = plots.get_subplot_plotter()
    g.triangle_plot(plot_samples, filled=True)

    plot_basename = os.path.splitext(os.path.basename(chain_root))[0]
    plot_filename = f"{plot_basename}_triangle.png"
    g.export(plot_filename)
    print(f"\nTriangle plot generated and saved to: {plot_filename}")
    print(f"Plot full path: {os.path.abspath(plot_filename)}")


if __name__ == '__main__':
    main()
