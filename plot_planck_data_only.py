#VGG: these plots are no good and need fixing!

import os
import numpy as np
import matplotlib.pyplot as plt
from cobaya.model import get_model

clik_path = os.getenv("CLIK_PATH", "./cobaya_packages/data/planck_2018/baseline")
clik_file = os.path.join(clik_path, "plc_3.0/hi_l/plik/plik_rd12_HM_v22b_TTTEEE.clik")

# Load Planck likelihood with a minimal CLASS theory provider
info = {
    "params": {
        "omega_b": 0.02237,
        "omega_cdm": 0.1200,
        "H0": 67.36,
        "tau_reio": 0.0544,
        "A_s": 2.10e-9,
        "n_s": 0.9649
    },
    "theory": {
        "classy": {
            "extra_args": {
                "output": "tCl pCl lCl"
            }
        }
    },
    "likelihood": {
        "planck_2018_highl_plik.TTTEEE": {
            "path": clik_path,
            "clik_file": clik_file
        }
    }
}

model = get_model(info)

# Extract the likelihood object and the internal clik data
like = model.likelihood["planck_2018_highl_plik.TTTEEE"]
internal = like.clik_likelihood._internal
bandpowers = np.array(internal.data_bandpowers)
ells = np.array(internal.ell[: len(bandpowers)])

# Group data by spectrum type using the Planck spec_order and group indices
spec_order = [spec.split()[0] for spec in internal.spec_order]
bins_start = np.array(internal.bins_start_ix, dtype=int)
bins_stop = np.array(internal.bins_stop_ix, dtype=int)

spectra = {"TT": [], "TE": [], "EE": []}
ell_groups = {"TT": [], "TE": [], "EE": []}
for spec, start, stop in zip(spec_order, bins_start, bins_stop):
    xs = ells[start:stop]
    ys = bandpowers[start:stop]
    if spec in spectra:
        spectra[spec].append(ys)
        ell_groups[spec].append(xs)

# Concatenate the separate frequency-combination groups into full TT/TE/EE series
ells_tt = np.concatenate(ell_groups["TT"])
tt = np.concatenate(spectra["TT"])
ells_te = np.concatenate(ell_groups["TE"])
te = np.concatenate(spectra["TE"])
ells_ee = np.concatenate(ell_groups["EE"])
ee = np.concatenate(spectra["EE"])

# Plot
fig, axs = plt.subplots(3, 1, figsize=(8, 12))

axs[0].plot(ells_tt, tt, ".", label="Planck TT data")
axs[0].set_title("Planck TT Experimental Data")
axs[0].set_ylabel(r"$D_\ell$")

axs[1].plot(ells_te, te, ".", label="Planck TE data")
axs[1].set_title("Planck TE Experimental Data")
axs[1].set_ylabel(r"$D_\ell$")

axs[2].plot(ells_ee, ee, ".", label="Planck EE data")
axs[2].set_title("Planck EE Experimental Data")
axs[2].set_xlabel(r"$\ell$")
axs[2].set_ylabel(r"$D_\ell$")

plt.tight_layout()
plt.savefig("planck_data_plot.png", dpi=200)
print("Saved plot to planck_data_plot.png")
plt.show()