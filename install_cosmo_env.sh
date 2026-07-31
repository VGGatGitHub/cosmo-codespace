#!/usr/bin/env bash
set -e

echo "=== Setting up Cosmo Environment ==="

# Update system packages
sudo apt-get update -y

# Install full OpenMPI stack available on Ubuntu 26.04
sudo apt-get install -y \
    openmpi-bin \
    openmpi-common \
    libopenmpi-dev \
    gfortran \
    pkg-config \
    build-essential \
    python3-dev

echo "=== Creating Python environment ==="
python3 -m venv cosmo-env
source cosmo-env/bin/activate

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Reinstalling mpi4py against correct MPI ==="
pip install --force-reinstall mpi4py

echo "=== Installing CLASS ==="
pip install classy

echo "=== Installing Cobaya ==="
pip install cobaya

echo "=== Creating Planck likelihood directory ==="
mkdir -p cobaya_packages/data/planck_2018

echo "=== Cosmo environment setup complete ==="
echo "Activate with: source cosmo-env/bin/activate"
