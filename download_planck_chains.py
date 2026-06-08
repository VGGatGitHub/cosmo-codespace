import os
import urllib.request
import zipfile

# URL of the official Planck 2018 MCMC chains (plikHM bundle)
url = "https://pla.esac.esa.int/pla-sl/data-action?COSMOLOGY.FILE_ID=COM_CosmoParams_base-plikHM_R3.01.zip"

# Output paths
zip_path = "COM_CosmoParams_base-plikHM_R3.01.zip"
extract_dir = "planck2018_chains"

print("Downloading Planck 2018 MCMC chains...")
urllib.request.urlretrieve(url, zip_path)
print("Download complete.")

print("Unzipping...")
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_dir)
print("Unzip complete.")

print("\nContents extracted to:", extract_dir)
print("Look for the folder:")
print("   base_plikHM_TTTEEE_lowl_lowE_lensing")
