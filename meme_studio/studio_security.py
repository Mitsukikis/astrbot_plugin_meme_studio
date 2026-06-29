import base64
import binascii
import hmac
import secrets
from dataclasses import dataclass
from typing import Dict, List
from urllib.parse import parse_qs


ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DATA_URL_MEDIA_EXTENSIONS = {
    "image/gif": {"gif"},
    "image/jpeg": {"jpg", "jpeg"},
    "image/jpg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
}
DEFAULT_MAX_UPLOAD_FILES = 32
DEFAULT_MAX_UPLOAD_FILE_BYTES = 20 * 1024 * 1024
WINDOWS_RESERVED_NAME_CHARS = set('<>:"|?*')


@dataclass(frozen=True)
class StudioAuthConfig:
    token: str


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def is_public_bind_host(host: str) -> bool:
    normalized = host.strip().lower()
    return normalized in {"0.0.0.0", "::"} or normalized not in {"", "127.0.0.1", "::1", "localhost"}


def extract_request_token(authorization: str, query: str) -> str:
    value = authorization.strip()
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    values = parse_qs(query).get("token", [])
    return values[0] if values else ""


def token_matches(config: StudioAuthConfig, provided: str) -> bool:
    return bool(provided) and hmac.compare_digest(config.token, provided)


def safe_upload_name(name: object) -> str:
    normalized = str(name).strip().replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1]
    if not filename or filename in {".", ".."}:
        raise ValueError("upload file name is empty")
    if any(ord(char) < 32 or char in WINDOWS_RESERVED_NAME_CHARS for char in filename):
        raise ValueError("upload file name contains invalid characters")

    stem, separator, extension = filename.rpartition(".")
    if not separator or not stem or extension.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("upload file extension is not allowed")
    return filename


def decode_uploads(
    files: object,
    max_files: int = DEFAULT_MAX_UPLOAD_FILES,
    max_file_bytes: int = DEFAULT_MAX_UPLOAD_FILE_BYTES,
) -> List[Dict[str, object]]:
    if not isinstance(files, list):
        raise ValueError("upload files must be a list")
    if len(files) > max_files:
        raise ValueError("too many upload files")

    decoded = []
    for file_info in files:
        if not isinstance(file_info, dict):
            raise ValueError("upload file entry must be an object")
        name = safe_upload_name(file_info.get("name", ""))
        extension = name.rsplit(".", 1)[1].lower()
        data = _base64_payload(file_info.get("data", ""), extension)
        try:
            file_bytes = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("invalid base64 upload data") from None
        if len(file_bytes) > max_file_bytes:
            raise ValueError("upload file too large")
        decoded.append({"name": name, "data": file_bytes})
    return decoded


def _base64_payload(data: object, extension: str) -> str:
    if not isinstance(data, str):
        raise ValueError("upload data must be base64 text")
    value = data.strip()
    if value.lower().startswith("data:"):
        header, separator, payload = value.partition(",")
        if not separator or ";base64" not in header.lower():
            raise ValueError("upload data URL must contain base64 data")
        media_type = header[5:].split(";", 1)[0].lower()
        if media_type:
            allowed_extensions = DATA_URL_MEDIA_EXTENSIONS.get(media_type)
            if not allowed_extensions:
                raise ValueError("upload data URL media type is not allowed")
            if extension not in allowed_extensions:
                raise ValueError("upload data URL media type does not match file extension")
        return payload
    return value
