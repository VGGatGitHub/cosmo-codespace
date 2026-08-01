#!/usr/bin/env bash
set -e

echo "=== Setting up Cosmo Environment ==="

# Update system packages
sudo apt-get update -y

# Install system dependencies
sudo apt-get install -y \
    openmpi-bin \
    openmpi-common \
    libopenmpi-dev \
    gfortran \
    pkg-config \
    build-essential \
    python3-dev

echo "=== Creating virtual environment ==="
python3 -m venv cosmo-env
source cosmo-env/bin/activate

echo "=== Upgrading pip ==="
python -m ensurepip --upgrade
pip install --upgrade pip

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Installing mpi4py ==="
pip install mpi4py

echo "=== Installing CLASS (via pip) ==="
pip install classy

echo "=== Installing Cobaya ==="
pip install cobaya

echo "=== Creating Planck likelihood directory ==="
mkdir -p cobaya_packages/data/planck_2018

echo "=== Exporting environment variables ==="
echo "export COBAYA_PACKAGES_PATH=/workspaces/cosmo-codespace/cobaya_packages" >> cosmo-env/bin/activate
echo "export CLIK_PATH=/workspaces/cosmo-codespace/cobaya_packages/data/planck_2018/baseline" >> cosmo-env/bin/activate

echo "=== Installing Planck likelihood ==="
cobaya-install planck_2018_highl_plik.TTTEEE -p /workspaces/cosmo-codespace/cobaya_packages

echo "=== Testing Planck likelihood ==="
cobaya-install --test planck_2018_highl_plik.TTTEEE -p /workspaces/cosmo-codespace/cobaya_packages

echo "=== Setup complete ==="
