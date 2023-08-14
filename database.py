import platform, sqlite3, os
from pathlib import Path

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
        Path.mkdir(db_path, exist_ok=True, parents=True)
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