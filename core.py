import os
import zipfile
import json
import classes
import shutil
import adapters
import sqlite3
import requests
import platform
from pathlib import Path

BASE_URL = "https://github.com/LDevs-Team/pak-pkgs/raw/main/"

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


def webDownloadPackage(package_name:str) -> str:
    with requests.get(f"{BASE_URL}{package_name}.zip") as r:
        if r.status_code != 200:
            raise ValueError('The specified package does not exist')
        with open(f"{package_name}.zip", "wb") as f:
            f.write(r.content)
    return f"{package_name}.zip"

def initDatabase() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_path = ''
    match platform.system():
        case 'Windows':
            backslash = '\\'
            db_path = f"{os.getenv('APPDATA').replace(backslash, '/')}/LDevs/Pak/"
        case 'Linux':
            db_path = f"{os.getenv('HOME')}/.config/LDevs/Pak/"
        case 'Darwin':
            db_path = f"{os.getenv('HOME')}/.config/LDevs/Pak"
        case _:
            db_path = "/"
    
    if os.path.exists(db_path) and not os.path.isdir(db_path):
        os.remove(db_path)
    if not os.path.exists(db_path):
        Path.mkdir(db_path, exist_ok=True)
    if os.path.exists(f"{db_path}/packages.db") and os.path.isdir(f"{db_path}/packages.db"):
        os.remove(f"{db_path}/packages.db")
    if not os.path.exists(f"{db_path}/packages.db"):
        f = open(f"{db_path}/packages.db", 'w')
        f.close()
    db = sqlite3.connect(f"{db_path}/packages.db")
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS PACKAGES (NAME TEXT, INSTALLPATH TEXT)")
    db.commit()
    return db, cursor
    
def queryDatabase(packageName:str) -> list[tuple[str, str]] | None:
    db, cursor = initDatabase()
    cursor.execute("SELECT * FROM PACKAGES WHERE NAME = ?", (packageName,))
    return cursor.fetchall()

def updatePackagesDatabase(packageName:str, installPath:str) -> None:
    db, cursor = initDatabase()
    cursor.execute("INSERT INTO PACKAGES (NAME, INSTALLPATH) VALUES (?, ?)", (packageName, installPath))
    db.commit()

def removeFromPackagesDatabase(packageName:str) -> None:
    db, cursor = initDatabase()
    cursor.execute("DELETE FROM PACKAGES WHERE NAME = (?)", (packageName,))
    db.commit()
    
def executeManifestKey(key: dict, name:str, packageName):
    match key['adapter']:
        case 'pak/adapter-ps1':
            if adapters.adapter_ps1(os.path.abspath(key['file']), key['needsReboot']):
                print("Success!")
                return
        case 'pak/adapter-batch':
            if adapters.adapter_batch(os.path.abspath(key['file']), key['needsReboot']):
                print("Success!")
                return                  
        case _:
            raise classes.BadPackage('Adapter for "install" is invalid')
    print("It looks like there was an error while installing the package. :(")
    return
        
def install(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        manifest = unpack(webDownloadPackage(package))
    
    if len(queryDatabase(manifest['name'])) > 0:
        print("Package is already installed.")
        return
    
    print(f"Starting installation of {manifest['name']}")
    install_key = manifest['installation']
    executeManifestKey(install_key, manifest['name'], package)
    updatePackagesDatabase(manifest['name'], package)

def uninstall(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        manifest = unpack(webDownloadPackage(package))
    
    if len(queryDatabase(manifest['name'])) == 0:
        print("Package is not installed.")
        return
    
    print(f"Starting uninstallation of {manifest['name']}")
    uninstall_key = manifest['uninstallation']
    executeManifestKey(uninstall_key, manifest['name'], package)
    removeFromPackagesDatabase(manifest['name'])
    
def upgrade(package: str):
    if os.path.exists(package):
        if os.path.isfile(package):
            package = os.path.abspath(package)
            manifest = unpack(package)
        else:
            raise ValueError('Specified file is not a package')
    else:
        manifest = unpack(webDownloadPackage(package))
    
    if len(queryDatabase(manifest['name'])) == 0:
        print("Package is not installed.")
        return
    
    print(f"Starting upgrade of {manifest['name']}")
    upgrade_key = manifest['update']
    executeManifestKey(upgrade_key, manifest['name'], package)