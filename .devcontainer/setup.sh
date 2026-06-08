#!/usr/bin/env bash
set -e

# Install Python packages
pip install --upgrade pip
pip install numpy scipy matplotlib cython
pip install cobaya classy

# Clone and compile CLASS
cd /workspaces/$CODESPACE_NAME
if [ ! -d "class" ]; then
    git clone https://github.com/lesgourg/class.git
fi
cd class
make clean
make -j4

echo "CLASS compiled successfully."

# Optional: Planck likelihoods
if [ -d "/workspaces/$CODESPACE_NAME/planck_data" ]; then
    export CLIK_PATH="/workspaces/$CODESPACE_NAME/planck_data"
elif [ -d "/workspaces/$CODESPACE_NAME/cobaya_packages/data/planck_2018/baseline" ]; then
    export CLIK_PATH="/workspaces/$CODESPACE_NAME/cobaya_packages/data/planck_2018/baseline"
fi

echo "Setup complete."
