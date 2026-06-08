#!/usr/bin/env bash
set -e

echo "=== Checking CLIK_PATH ==="
if [ -z "$CLIK_PATH" ]; then
    echo "❌ CLIK_PATH is NOT set"
else
    echo "✔ CLIK_PATH is set to: $CLIK_PATH"
fi

# Try to detect the actual Planck CLIK root.
PLANCK_ROOT=""
try_paths=(
    "$CLIK_PATH"
    "$CLIK_PATH/baseline"
    "./cobaya_packages/data/planck_2018/baseline"
    "./cobaya_packages/data/planck_2018"
    "./planck_data"
)

for p in "${try_paths[@]}"; do
    if [ -n "$p" ] && [ -d "$p/plc_3.0" ]; then
        PLANCK_ROOT="$p"
        break
    fi
 done

if [ -z "$PLANCK_ROOT" ]; then
    echo
    echo "❌ Could not locate a valid Planck CLIK root. Tried the following paths:"
    for p in "${try_paths[@]}"; do
        [ -n "$p" ] && echo "  - $p"
    done
    exit 1
fi

if [ -n "$CLIK_PATH" ] && [ "$PLANCK_ROOT" != "$CLIK_PATH" ]; then
    echo "⚠ CLIK_PATH does not point to the actual Planck root. Using detected root: $PLANCK_ROOT"
else
    echo "✔ Using Planck root: $PLANCK_ROOT"
fi

echo
echo "=== Checking Planck folder structure ==="
if [ ! -d "$PLANCK_ROOT/plc_3.0" ]; then
    echo "❌ Missing plc_3.0 folder inside Planck root"
    exit 1
else
    echo "✔ Found plc_3.0"
fi

echo
echo "=== Checking required subfolders ==="
for d in hi_l low_l lensing cosmomc; do
    if [ ! -d "$PLANCK_ROOT/plc_3.0/$d" ]; then
        echo "❌ Missing: $d"
        exit 1
    else
        echo "✔ Found: $d"
    fi
done

echo
echo "=== Checking clik shared libraries or clipy package ==="
CLIK_LIB=$(ls "$PLANCK_ROOT/plc_3.0/cosmomc" 2>/dev/null | grep -E "clik|\.so" || true)
CLIPY_PATHS=(
    "$PLANCK_ROOT/clipy"
    "./cobaya_packages/code/planck/clipy"
)

if [ -n "$CLIK_LIB" ]; then
    echo "✔ Found clik libraries:"
    echo "$CLIK_LIB"
elif [ -d "${CLIPY_PATHS[0]}" ] || [ -d "${CLIPY_PATHS[1]}" ]; then
    echo "✔ No cosmomc .so libraries found, but clipy is installed at one of the expected locations."
    echo "  clipy path:"
    [ -d "${CLIPY_PATHS[0]}" ] && echo "    - ${CLIPY_PATHS[0]}"
    [ -d "${CLIPY_PATHS[1]}" ] && echo "    - ${CLIPY_PATHS[1]}"
else
    echo "❌ No clik shared libraries found in cosmomc/ and no clipy package found"
    exit 1
fi

echo
echo "=== Checking if Cobaya can import Planck likelihood ==="
python3 - << 'EOF'
try:
    from cobaya.likelihoods.planck_2018_highl_plik.TTTEEE import TTTEEE
    print("✔ Cobaya successfully imported planck_2018_highl_plik.TTTEEE")
except Exception:
    try:
        from cobaya.likelihoods.planck_2018_lowl.TT import TT
        print("✔ Cobaya successfully imported planck_2018_lowl.TT")
    except Exception as e:
        print("❌ Cobaya failed to import any Planck likelihood module")
        print(e)
        exit(1)
EOF

echo
echo "=== All checks passed ==="
