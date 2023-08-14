import typing

class BadPackage(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("File is not a valid package. Error: " + " ".join(args))

class MissingFileError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("File {} does not exist.".format(" ".join(args)))

class PackageUpdateError(Exception):
    def __init__(self, updateType:typing.Literal['upgrade', 'install', 'uninstall']) -> None:
        super().__init__(f"Operation {updateType} failed.")