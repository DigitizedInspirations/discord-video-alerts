import io
import ipaddress
import socket
import warnings
from .config import relative
from .http import request
from .model import AlertError, safe_url

MIMES = {"GIF": "image/gif", "PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}

def image_info(raw, require_animation=False):
    from PIL import Image, UnidentifiedImageError
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                fmt, size, frames = image.format, image.size, getattr(image, "n_frames", 1)
                if fmt not in MIMES or not all(1 <= side <= 8192 for side in size) or size[0]*size[1] > 25_000_000 or frames > 1000 or size[0]*size[1]*frames > 100_000_000:
                    raise ValueError()
                if fmt == "GIF" and (not raw.startswith((b"GIF87a", b"GIF89a")) or not raw.endswith(b";")):
                    raise ValueError()
                if require_animation and (fmt != "GIF" or frames < 2):
                    raise ValueError()
                for index in range(frames):
                    image.seek(index)
                    image.load()
                return {"format": fmt, "mime": MIMES[fmt], "dimensions": list(size), "frames": frames}
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, EOFError):
        raise AlertError("Invalid, oversized or non-animated media") from None

def attachment(root, cfg):
    if not cfg["enabled"]:
        return None
    try:
        path = relative(root, cfg["path"])
        if not path.is_file() or path.stat().st_size > cfg["max_bytes"]:
            raise AlertError("Attachment missing or exceeds configured upload limit")
        raw = path.read_bytes()
        info = image_info(raw, cfg["require_animation"])
        suffix = {"GIF": ".gif", "PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[info["format"]]
        if path.suffix.lower() not in ({".jpg", ".jpeg"} if info["format"] == "JPEG" else {suffix}):
            raise AlertError("Attachment extension does not match actual format")
        return {"name": "announcement" + suffix, "raw": raw, **info}
    except (AlertError, OSError):
        if cfg["fallback"] == "omit":
            return None
        raise AlertError("Attachment invalid; configured fallback skips announcement") from None

def avatar(value, fallback, transport=request):
    if value is None:
        return None
    try:
        u = safe_url(value)
        addresses = socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise AlertError("Avatar requires a public internet host")
        response = transport("GET", value, limit=2_000_000)
        if response.status != 200:
            raise AlertError("Avatar is not publicly reachable")
        info = image_info(response.body)
        mime = response.headers.get("Content-Type", "").split(";")[0].lower()
        if mime != info["mime"]:
            raise AlertError("Avatar MIME/type mismatch")
        return value
    except (AlertError, OSError):
        if fallback == "omit":
            return None
        raise AlertError("Avatar validation failed; configured fallback skips message") from None
