import os
import sys
from typing import List


class InstallError(Exception):
    """Error when installing macros."""


def get_macro_directory():
    if sys.platform.startswith("win"):
        return os.path.join(
            os.environ["APPDATA"], "LibreOffice", "4", "user", "Scripts", "python"
        )
    elif sys.platform.startswith("darwin"):
        return os.path.join(
            os.environ["HOME"],
            "Library",
            "Application Support",
            "LibreOffice",
            "4",
            "user",
            "Scripts",
            "python",
        )
    elif sys.platform.startswith("linux"):
        return os.path.join(
            os.environ["HOME"],
            ".config",
            "libreoffice",
            "4",
            "user",
            "Scripts",
            "python",
        )
    raise InstallError(
        f"Unsupported platform: {sys.platform}. Only Linux, macOS and Windows are supported."
    )


def create_macro_directory():
    macro_directory = get_macro_directory()
    if not os.path.exists(macro_directory):
        os.makedirs(macro_directory)


def link_macros(file_names: List[str]):
    create_macro_directory()
    macro_dir = get_macro_directory()
    for file in file_names:
        path = os.path.join(os.getcwd(), file)
        os.symlink(path, os.path.join(macro_dir, file))


files = ["acquisitions.py", "set_simulation_date.py"]

link_macros(files)
