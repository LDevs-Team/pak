from typing import Dict, Union
from . import classes
import os
import zipfile
import json
import shutil
from . import adapters
import requests
import validators
import platform
import typing
from urllib.parse import urlparse
from pathlib import Path
from . import database 

BadPackage = classes.BadPackage

queryDatabase, updatePackagesDatabase, removeFromPackagesDatabase = database.queryDatabase, database.updatePackagesDatabase, database.removeFromPackagesDatabase

BASE_URL = "https://github.com/LDevs-Team/pak-pkgs/raw/main/"

def init_temp():
    """
    Initializes a temporary directory.

    This function checks if the 'Temp' directory exists. If it does, the directory is removed using the 'shutil.rmtree()' function. Then, a new 'Temp' directory is created using the 'os.mkdir()' function.

    Parameters:
        - None

    Returns:
        - None
    """
    if os.path.exists('Temp'):
        shutil.rmtree('Temp')
    os.mkdir("Temp")

def init_pkgs():
    """
    Initializes the packages by determining the appropriate path for the manifests file based on the current platform.

    Returns:
        str: The path to the manifests file.
    """
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

def unpack(file_path: str) -> Union[Dict, BadPackage]:
    """
    Unpacks a zip file and returns the manifest as a dictionary.
    
    Args:
        file_path (str): The path to the zip file.
    
    Returns:
        Union[Dict, BadPackage]: The manifest dictionary if it exists, 
                                otherwise raises a BadPackage exception.
    """
    try:
        with zipfile.ZipFile(file_path) as zip_file:
            zip_file.extractall('Temp')
    except zipfile.BadZipFile:
        raise BadPackage("Package is not a zipfile")
    
    os.chdir("Temp")
    try:
        with open('manifest.json', 'r') as manifest_file:
            manifest = json.load(manifest_file)
            return manifest
    except OSError:
        raise BadPackage("Package has no manifest.json file")


def webDownload(url:str, filename:str) -> str:
    """
    Downloads a file from the specified URL and saves it to the specified filename.

    Parameters:
    - url (str): The URL of the file to be downloaded.
    - filename (str): The name of the file to be saved.

    Returns:
    - str: The path of the downloaded file.

    Raises:
    - ValueError: If the specified package does not exist.
    """
    init_temp()
    with requests.get(url) as r:
        if r.status_code != 200:
            raise ValueError('The specified package does not exist')
        with open(f"Temp/{filename}", "wb") as f:
            f.write(r.content)
            f.close()
    return f"Temp/{filename}"
    
def executeManifestKey(key: dict, operationType:str):
    """
    Executes a manifest key based on the given parameters.

    Parameters:
    - key (dict): A dictionary representing the manifest key.
    - operationType (str): The type of operation to be performed.

    Returns:
    - None: If the adapter is successfully executed.
    - MissingFileError: If the file specified in the manifest key does not exist.
    - BadPackage: If the adapter for the "install" operation is invalid.
    - PackageUpdateError: If there is an error during the package update operation.
    """
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
    """
    Downloads a package from the repository.

    Parameters:
        package (str): The name of the package to download.

    Returns:
        str: The path to the downloaded package.

    Raises:
        ValueError: If the specified package does not exist.
    """
    try:
        return webDownload(f"{BASE_URL}{package}.zip", f"{package}.zip")
    except ValueError:
        return webDownload(f"{BASE_URL}{package}.json", f"{package}.json")
    except:
        return ValueError('The specified package does not exist')
    

def install(package: str):
    """
    Installs a package.

    Args:
        package (str): The name or path of the package to install.

    Raises:
        ValueError: If the specified file is not a package.

    Returns:
        None
    """
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
    """
    Uninstalls a package.

    Parameters:
        package (str): The name of the package to uninstall.

    Raises:
        ValueError: If the package is not installed.

    Returns:
        None
    """
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
    """
    Upgrade a package.

    Parameters:
        package (str): The name or path of the package to upgrade.

    Returns:
        None
    """
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