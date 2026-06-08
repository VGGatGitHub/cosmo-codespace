#!/usr/bin/env bash
set -e

echo "=== Installing Planck likelihood package with Cobaya ==="
mkdir -p ./cobaya_packages
# Install the recognized Planck likelihood component; Cobaya will pull required data
# into ./cobaya_packages/data/planck_2018 (if available for this component)
cobaya-install planck_2018_highl_plik.TTTEEE -p ./cobaya_packages

echo "=== Installing system dependencies for Planck clik ==="
sudo apt-get update
sudo apt-get install -y wget libfftw3-dev gfortran

DATA_ROOT="$(pwd)/cobaya_packages/data/planck_2018"
BASELINE_ROOT="$DATA_ROOT/baseline"

if [ -d "$BASELINE_ROOT/plc_3.0" ]; then
    CLIK_ROOT="$BASELINE_ROOT"
elif [ -d "$DATA_ROOT/plc_3.0" ]; then
    CLIK_ROOT="$DATA_ROOT"
else
    echo "❌ Expected Planck data not found in $DATA_ROOT"
    echo "Please verify that cobaya-install succeeded and that planck_2018 data were installed."
    exit 1
fi

# If clipy code was installed under ./cobaya_packages/code/planck/clipy, make
# it visible under the data root so Planck likelihood can load it from
# $CLIK_ROOT/clipy
CODE_CLIPY_DIR="$(pwd)/cobaya_packages/code/planck/clipy"
if [ ! -d "$CLIK_ROOT/clipy" ] && [ -d "$CODE_CLIPY_DIR" ]; then
    echo "Creating symlink for clipy from $CODE_CLIPY_DIR -> $CLIK_ROOT/clipy"
    ln -s "$CODE_CLIPY_DIR" "$CLIK_ROOT/clipy"
fi

# Create a combined CLIK root that contains both plc_3.0 (data) and clipy (code)
# Ensure the data root contains a visible 'clipy' module (symlink code->data if needed)
if [ -d "$CODE_CLIPY_DIR" ] && [ ! -e "$CLIK_ROOT/clipy" ]; then
    ln -s "$CODE_CLIPY_DIR" "$CLIK_ROOT/clipy"
fi

echo "=== Checking for clik shared libraries or .clik containers ==="
# Accept any of: compiled .so files, .clik container directories, or 'hascl' marker files
if find "$CLIK_ROOT/plc_3.0" -type f -name "*.so" -print -quit | grep -q . || \
   find "$CLIK_ROOT/plc_3.0" -type d -name "*.clik" -print -quit | grep -q . || \
   find "$CLIK_ROOT/plc_3.0" -type f -name "hascl" -print -quit | grep -q .; then
    echo "✔ clik libraries or containers found!"
    echo "Examples:"
    find "$CLIK_ROOT/plc_3.0" -maxdepth 4 \( -name "*.so" -o -name "*.clik" -o -name "hascl" \) -print | sed -n '1,20p'
else
    echo "❌ ERROR: clik shared libraries or .clik containers are missing."
    echo "This means the Cobaya Planck data installation failed or was incomplete."
    exit 1
fi

echo "=== Setting CLIK_PATH ==="
export CLIK_PATH="$CLIK_ROOT"
if ! grep -Fxq "export CLIK_PATH=\"$CLIK_ROOT\"" ~/.bashrc 2>/dev/null; then
    echo "export CLIK_PATH=\"$CLIK_ROOT\"" >> ~/.bashrc
fi

echo "=== Planck likelihood installation complete ==="
