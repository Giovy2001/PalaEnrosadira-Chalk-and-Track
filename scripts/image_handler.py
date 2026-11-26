"""Gestione delle immagini delle route: filesystem locale o Vercel Blob."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import settings
import vercel_blob
from PIL import Image, ImageOps

upload_function_name: str = ""


def init_glob_database() -> None:
    global upload_function_name
    upload_function_name = "blob"


def init_local_database() -> None:
    global upload_function_name
    upload_function_name = "local"


def _require_backend() -> str:
    if upload_function_name not in UPLOAD_FUNCTIONS:
        raise RuntimeError("ImageHandler non inizializzato o backend sconosciuto")
    return upload_function_name


def _safe_name(image_full_name: str) -> str:
    name = Path(str(image_full_name or "image")).stem
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return name[:60] or "image"


def put(image_full_name: str, image_data: bytes) -> str:
    """Processa e salva un'immagine, restituendone URL/percorso."""

    _require_backend()
    if not image_data:
        raise ValueError("File immagine vuoto")

    image_name = _safe_name(image_full_name)
    try:
        img = Image.open(BytesIO(image_data))
        img.load()
    except Exception as exc:
        raise ValueError("Il file caricato non è un'immagine valida") from exc

    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    cropped_img = crop(img)
    max_width = 1080
    width, height = cropped_img.size
    if width > max_width:
        new_height = max(1, int((max_width / width) * height))
        cropped_img = cropped_img.resize((max_width, new_height), Image.LANCZOS)

    return UPLOAD_FUNCTIONS[upload_function_name](image_name, cropped_img)


def list() -> list[str]:
    """Elenca tutti gli URL/percorsi delle immagini salvate."""

    backend = _require_backend()
    if backend == "blob":
        urls: list[str] = []
        cursor = None
        # Limite di sicurezza per evitare loop infiniti in caso di API anomalo.
        for _ in range(100):
            options = {"limit": 1000}
            if cursor:
                options["cursor"] = cursor
            response = vercel_blob.list(options)
            urls.extend(item["url"] for item in response.get("blobs", []))
            cursor = response.get("cursor")
            if not cursor:
                break
        return urls

    return [
        path.as_posix()
        for path in Path(settings.LOCAL_IMAGES_DIR).glob("*")
        if path.is_file()
    ]


def delete(image_url: str) -> None:
    """Elimina un'immagine dal backend configurato."""

    backend = _require_backend()
    if not image_url:
        return
    if backend == "blob":
        vercel_blob.delete(image_url)
        return

    path = Path(str(image_url).replace("\\", "/"))
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    if path.is_file():
        path.unlink()


def local_commit(image_name: str, img: Image.Image) -> str:
    """Salva l'immagine su disco e restituisce il percorso relativo."""

    images_dir = Path(settings.LOCAL_IMAGES_DIR)
    images_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{image_name}_{uuid4()}.jpg"
    path = images_dir / filename
    img.save(path, format="JPEG", quality=85, optimize=True)
    return f"static/local_database/Images/{filename}"


def blob_commit(image_name: str, img: Image.Image) -> str:
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    response = vercel_blob.put(
        f"{image_name}.jpg", buffer.getvalue(), {"addRandomSuffix": "true"}
    )
    return response["url"]


def crop(img: Image.Image) -> Image.Image:
    """Ritaglia al centro con proporzione 7:10 (width:height)."""

    width, height = img.size
    target_ratio = 7 / 10
    current_ratio = width / height
    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        new_height = height
    else:
        new_width = width
        new_height = int(width / target_ratio)

    left = (width - new_width) // 2
    top = (height - new_height) // 2
    return img.crop((left, top, left + new_width, top + new_height))


UPLOAD_FUNCTIONS: dict = {"blob": blob_commit, "local": local_commit}
