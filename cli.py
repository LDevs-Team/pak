import sys
import core

METHOD = sys.argv[1]
PACKAGE = sys.argv[2]

match METHOD.lower():
    case "install":
        core.install(PACKAGE)
    case _:
        raise NotImplementedError("Other functionality is still not implemented")