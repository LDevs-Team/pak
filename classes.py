class BadPackage(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__("File is not a valid package. Error: " + " ".join(args))