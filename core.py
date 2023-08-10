import os
import zipfile
import json
import classes
import shutil
import adapters

BASE_URL = ""

def unpack(filePath: str) -> dict:
    if os.path.exists('Temp'):
        shutil.rmtree('Temp')
    os.mkdir("Temp")
    try:
        with zipfile.ZipFile(filePath) as zip:
            zip.extractall('Temp')
    except zipfile.BadZipFile:
        raise classes.BadPackage("Package is not a zipfile")
    
    os.chdir("Temp")
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
            return manifest
    except OSError:
        raise classes.BadPackage("Package has no manifest.json file")


def install(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            manifest = unpack(package)
            print(f"Starting installation of {manifest['name']}")
            install_key = manifest['installation']
            match install_key['adapter']:
                case 'pak/adapter-ps1':
                    if adapters.adapter_ps1(os.path.abspath(install_key['file']), install_key['needsReboot']):
                        print("Package installed successfully!")
                        return
                case 'pak/adapter-batch':
                    if adapters.adapter_batch(os.path.abspath(install_key['file']), install_key['needsReboot']):
                        print("Package installed successfully!")
                        return                  
                case _:
                    raise classes.BadPackage('Adapter for "install" is invalid')
            print("It looks like there was an error while installing the package. :(")
            return
        raise ValueError('Specified file is not a package')
    
    raise NotImplementedError("Web download is not implemented")