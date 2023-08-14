import os
import zipfile
import json
import classes
import shutil
import adapters
import sqlite3
import requests
import platform
import typing
from urllib.parse import urlparse
from pathlib import Path
from database import initDatabase, queryDatabase, updatePackagesDatabase, removeFromPackagesDatabase

BASE_URL = "https://github.com/LDevs-Team/pak-pkgs/raw/main/"

def init_temp():
    if os.path.exists('Temp'):
        shutil.rmtree('Temp')
    os.mkdir("Temp")

def unpack(filePath: str) -> dict|classes.BadPackage:
    init_temp()
    try:
        with zipfile.ZipFile(filePath) as zip:
            zip.extractall('Temp')
    except zipfile.BadZipFile:
        raise classes.BadPackage("Package is not a zipfile")
    
    os.chdir("Temp")
    try:
        with open('manifest.json', 'r') as f:
            manifest:dict = json.load(f)
            return manifest
    except OSError:
        raise classes.BadPackage("Package has no manifest.json file")


def webDownloadPackage(package_name:str, extension:typing.Literal['zip', 'json']) -> str:
    init_temp()
    with requests.get(f"{BASE_URL}{package_name}.{extension}") as r:
        if r.status_code != 200:
            raise ValueError('The specified package does not exist')
        with open(f"Temp/{package_name}.{extension}", "wb") as f:
            f.write(r.content)
    return f"Temp/{package_name}.{extension}"


    
def executeManifestKey(key: dict, operationType:str):
    init_temp()
    fileToExecute = key['file']
    if key['file'].startswith('url:'):
        req = requests.get(key['file'].removeprefix('url:'))
        f = open("Temp/" + os.path.basename(urlparse(key["file"]).path), 'wb')
        f.write(req.content)
        f.close()
        fileToExecute = "Temp/" + os.path.basename(urlparse(key["file"]).path)
    if not os.path.exists(fileToExecute):
        return classes.MissingFileError(fileToExecute)
    match key['adapter']:
        case 'pak/adapter-ps1':
            if adapters.adapter_ps1(os.path.abspath(fileToExecute), key['needsReboot']):
                print("Success!")
                return
        case 'pak/adapter-batch':
            if adapters.adapter_batch(os.path.abspath(fileToExecute), key['needsReboot']):
                print("Success!")
                return                  
        case _:
            raise classes.BadPackage('Adapter for "install" is invalid. Got {}'.format(key['adapter']))
    raise classes.PackageUpdateError(operationType)

def downloadPackageFromRepo(package):
    try:
        return webDownloadPackage(package, 'zip')
    except ValueError:
        return webDownloadPackage(package, 'json')
    except:
        return ValueError('The specified package does not exist')
    

def install(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        packageFile = downloadPackageFromRepo(package)
        if packageFile.endswith("zip"):
            manifest = unpack(packageFile)
        elif packageFile.endswith('json'):
            manifest = json.load(open(packageFile, "r"))
    
    if len(queryDatabase(manifest['name'])) > 0:
        print("Package is already installed.")
        return
    
    print(f"Starting installation of {manifest['name']}")
    install_key = manifest['installation']
    executeManifestKey(install_key, "install")
    updatePackagesDatabase(manifest['name'], package)

def uninstall(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        packageFile = downloadPackageFromRepo(package)
        if packageFile.endswith("zip"):
            manifest = unpack(packageFile)
        elif packageFile.endswith('json'):
            manifest = json.load(open(packageFile, "r"))
    
    if len(queryDatabase(manifest['name'])) == 0:
        print("Package is not installed.")
        return
    
    print(f"Starting uninstallation of {manifest['name']}")
    uninstall_key = manifest['uninstallation']
    executeManifestKey(uninstall_key, "uninstall")
    removeFromPackagesDatabase(manifest['name'])
    
def upgrade(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        packageFile = downloadPackageFromRepo(package)
        if packageFile.endswith("zip"):
            manifest = unpack(packageFile)
        elif packageFile.endswith('json'):
            manifest = json.load(open(packageFile, "r"))
    
    if len(queryDatabase(manifest['name'])) == 0:
        print("Package is not installed.")
        return
    
    print(f"Starting upgrade of {manifest['name']}")
    upgrade_key = manifest['update']
    executeManifestKey(upgrade_key, "upgrade")