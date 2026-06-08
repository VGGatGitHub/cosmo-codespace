import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits

planck_root = os.getenv("CLIK_PATH", "./cobaya_packages/data/planck_2018/baseline")
fits_path = os.path.join(planck_root, "plc_3.0/hi_l/plik/plik_lite_v22_TT.fits")

if os.path.isfile(fits_path):
    # Open FITS data if available
    with fits.open(fits_path) as hdul:
        ells = hdul["ELL"].data
        dl_tt = hdul["D_ELL"].data
        err_tt = hdul["ERROR"].data
else:
    # Fallback to Planck CLik data if .fits is not installed
    from cobaya.model import get_model

    clik_file = os.path.join(planck_root, "plc_3.0/hi_l/plik/plik_rd12_HM_v22_TT.clik")
    if not os.path.isdir(clik_file):
        raise FileNotFoundError(
            f"Neither FITS nor TT CLik data found. Expected one of:\n"
            f"  {fits_path}\n"
            f"  {clik_file}"
        )

    info = {
        "params": {
            "omega_b": 0.02237,
            "omega_cdm": 0.1200,
            "H0": 67.36,
            "tau_reio": 0.0544,
            "A_s": 2.10e-9,
            "n_s": 0.9649,
        },
        "theory": {
            "classy": {
                "extra_args": {
                    "output": "tCl pCl lCl"
                }
            }
        },
        "likelihood": {
            "planck_2018_highl_plik.TT": {
                "path": planck_root,
                "clik_file": clik_file,
            }
        }
    }

    model = get_model(info)
    like = model.likelihood["planck_2018_highl_plik.TT"]
    internal = like.clik_likelihood._internal

    bandpowers = np.array(internal.data_bandpowers)
    ells = np.array(internal.ell[: len(bandpowers)])

    spec_order = [spec.split()[0] for spec in internal.spec_order]
    bins_start = np.array(internal.bins_start_ix, dtype=int)
    bins_stop = np.array(internal.bins_stop_ix, dtype=int)

    tt_groups = []
    ell_groups = []
    for spec, start, stop in zip(spec_order, bins_start, bins_stop):
        if spec == "TT":
            tt_groups.append(bandpowers[start:stop])
            ell_groups.append(ells[start:stop])

    if not tt_groups:
        raise RuntimeError("No TT data groups found in Planck CLik likelihood.")

    dl_tt = np.concatenate(tt_groups)
    ells = np.concatenate(ell_groups)
    err_tt = np.full_like(dl_tt, np.nan)

plt.figure(figsize=(8,5))
plt.errorbar(ells, dl_tt, yerr=err_tt, fmt=".", label="Planck TT data")
plt.xlabel(r"$\ell$")
plt.ylabel(r"$D_\ell = \ell(\ell+1)C_\ell/2\pi$")
plt.title("Planck 2018 TT Experimental Data")
plt.legend()
plt.tight_layout()
plt.savefig("planck_data_direct_plot.png", dpi=200)
print("Saved plot to planck_data_direct_plot.png")
plt.show()
