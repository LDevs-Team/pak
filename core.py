import os
import zipfile
import json
import classes
import shutil
import adapters
import sqlite3
import requests
import validators
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

def init_pkgs():
    manifests_path = ''
    match platform.system():
        case 'Windows':
            backslash = '\\'
            manifests_path = f"{os.getenv('APPDATA').replace(backslash, '/')}/LDevs/Pak/packages"
        case 'Linux':
            manifests_path = f"{os.getenv('HOME')}/.config/LDevs/Pak/packages"
        case 'Darwin':
            manifests_path = f"{os.getenv('HOME')}/.config/LDevs/Pak/packages"
        case _:
            manifests_path = "/"
    
    if os.path.exists(manifests_path) and not os.path.isdir(manifests_path):
        os.remove(manifests_path)
    if not os.path.exists(manifests_path):
        Path.mkdir(manifests_path, exist_ok=True, parents=True)
    return manifests_path
def unpack(filePath: str) -> dict|classes.BadPackage:
    """returns the manifest from a zip file"""
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


def webDownload(url:str, filename:str) -> str:
    init_temp()
    with requests.get(url) as r:
        if r.status_code != 200:
            raise ValueError('The specified package does not exist')
        with open(f"Temp/{filename}", "wb") as f:
            f.write(r.content)
            f.close()
    return f"Temp/{filename}"
    
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
        return webDownload(f"{BASE_URL}{package}.zip", f"{package}.zip")
    except ValueError:
        return webDownload(f"{BASE_URL}{package}.json", f"{package}.json")
    except:
        return ValueError('The specified package does not exist')
    

def install(package: str):
    manifests_path = init_pkgs()
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
            shutil.copy(package, manifests_path)
            packageFile = package
        else:
            raise ValueError('Specified file is not a package')
    elif validators.url(package):
        packageFile = webDownload(package, urlparse(package).path.split("/")[-1])
        shutil.copy(packageFile, manifests_path)
        if packageFile.endswith("zip"):
            manifest = unpack(packageFile)
        elif packageFile.endswith('json'):
            manifest = json.load(open(packageFile, "r"))
    else:
        packageFile = downloadPackageFromRepo(package)
        if packageFile.endswith("zip"):
            manifest = unpack(packageFile)
        elif packageFile.endswith('json'):
            manifest = json.load(open(packageFile, "r"))
        os.chdir("..")
        shutil.copy(packageFile, manifests_path)
        os.chdir("Temp")
        
    if len(queryDatabase(manifest['name'])) > 0:
        print("Package is already installed.")
        return
    print(f"Starting installation of {manifest['name']}")
    install_key = manifest['installation']
    executeManifestKey(install_key, "install")
    updatePackagesDatabase(manifest['name'], package, manifests_path+"/"+os.path.basename(os.path.realpath(packageFile)))

def uninstall(package: str):
    db, cursor = initDatabase()
    result = queryDatabase(package)
    if len(result) < 1:
        raise ValueError("Package is not installed")
    package = result[0]
    if package[2].endswith("zip"):
        manifest = unpack(package[2])   
    elif package[2].endswith("json"):
        f = open(package[2], "r")
        manifest = json.load(f) 
        f.close()    
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