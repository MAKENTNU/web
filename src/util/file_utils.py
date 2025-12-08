import hashlib
from pathlib import PurePosixPath

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile


def calculate_file_hash(file: File) -> bytes:
    file.open("rb")
    file_hash = hashlib.blake2b()
    while chunk := file.read(2**16):  # 65536 bytes
        file_hash.update(chunk)

    if isinstance(file, UploadedFile):
        # Reset file seek; do not close, as uploaded (temporary) files are deleted when closed
        file.seek(0)
    else:
        file.close()
    return file_hash.digest()


def file_contents_equal(file1: File, file2: File) -> bool:
    return calculate_file_hash(file1) == calculate_file_hash(file2)


def filenames_equal(file1: File, file2: File) -> bool:
    return PurePosixPath(file1.name).name == PurePosixPath(file2.name).name
