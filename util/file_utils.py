import hashlib

from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile


def calculate_file_hash(file: File) -> bytes:
    file.open('rb')
    file_hash = hashlib.blake2b()
    while chunk := file.read(2 ** 16):  # 65536 bytes
        file_hash.update(chunk)

    if isinstance(file, InMemoryUploadedFile):
        # Reset file seek; do not close, as in-memory files cannot (easily) be reopened
        file.open()
    else:
        file.close()
    return file_hash.digest()


def files_equal(file1: File, file2: File) -> bool:
    return calculate_file_hash(file1) == calculate_file_hash(file2)