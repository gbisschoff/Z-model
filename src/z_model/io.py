from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def zip_files(files: [Path], destination: Path) -> Path:
    """
    Zip a list of files

    :param files: a list of :class:`Path`s to zip
    :param destination: the destination zip file.

    """
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=9) as zip_file:
        for f in files:
            zip_file.write(f, f.name)

    return destination
