"""File scanner: walk folders, unzip archives, filter supported formats."""
import os
import zipfile

SUPPORTED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}


def _is_junk(name: str) -> bool:
    """Skip OS cruft: macOS AppleDouble (._foo), __MACOSX/, .DS_Store, dotfiles."""
    base = os.path.basename(name.rstrip("/"))
    if "__MACOSX" in name.split("/"):
        return True
    return base.startswith(".")  # ._resourcefork, .DS_Store, and any dotfile


def is_supported(filename: str) -> bool:
    if _is_junk(filename):
        return False
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXT


def scan_folder(path: str) -> list[str]:
    """Return absolute paths of supported files under a folder (recursive)."""
    found = []
    for root, _dirs, files in os.walk(path):
        for f in files:
            if is_supported(f):
                found.append(os.path.join(root, f))
    return sorted(found)


def extract_zip(zip_path: str, dest_dir: str) -> list[str]:
    """Unzip into dest_dir, return supported file paths (skips OS cruft)."""
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if is_supported(member):
                z.extract(member, dest_dir)
    return scan_folder(dest_dir)
