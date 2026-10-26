import mimetypes
import os

from fastapi import UploadFile


def readPensumUpload(file: UploadFile) -> tuple[str, str, bytes, str]:
    """Shared validation for free-event and official parameter documents."""
    if not file or not file.filename:
        raise ValueError("Debe adjuntar un archivo de pensum.")
    allowedExtensions = {
        ".pdf", ".doc", ".docm", ".docx", ".odt", ".rtf", ".txt", ".csv",
        ".ods", ".xls", ".xlsb", ".xlsm", ".xlsx", ".odp", ".ppt", ".pptm",
        ".pptx", ".png", ".jpg", ".jpeg",
    }
    originalFileName = file.filename.replace("\\", "/").rsplit("/", 1)[-1]
    extension = os.path.splitext(originalFileName)[1].lower()
    if extension not in allowedExtensions:
        raise ValueError(
            "Tipo de archivo no permitido. Adjunte PDF, imagen o un "
            "documento compatible con OnlyOffice."
        )
    if len(originalFileName) > 255:
        raise ValueError("El nombre del archivo no puede superar 255 caracteres.")
    fileContent = file.file.read()
    if not fileContent:
        raise ValueError("El archivo de pensum está vacío.")
    mimeType = file.content_type or mimetypes.guess_type(originalFileName)[0] or "application/octet-stream"
    if len(mimeType) > 150:
        raise ValueError("El tipo de archivo indicado no es válido.")
    return originalFileName, extension, fileContent, mimeType
