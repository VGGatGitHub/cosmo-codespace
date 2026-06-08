from cobaya.model import get_model
import numpy as np

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
        "planck_2018_highl_plik.TTTEEE": {"path": None}
    }
}

print("=== Building Cobaya model ===")
model = get_model(info)

print("=== Checking likelihood instance ===")
like = model.likelihood["planck_2018_highl_plik.TTTEEE"]

# Check if clik backend exists
if not hasattr(like, "clik_likelihood"):
    print("❌ No clik_likelihood attribute — fallback likelihood is being used")
    exit()

print("✔ clik_likelihood attribute found")

internal = getattr(like.clik_likelihood, "_internal", None)
if internal is None:
    print("❌ No _internal object — clik backend not loaded")
    exit()

print("✔ _internal object found")

# Try reading data
try:
    obs = np.array(internal.data_bandpowers)
    invcov = np.array(internal.siginv)
    print("✔ Successfully accessed data_bandpowers and siginv")
    print("Number of data points:", len(obs))
except Exception as e:
    print("❌ Failed to access clik internal data")
    print(e)

