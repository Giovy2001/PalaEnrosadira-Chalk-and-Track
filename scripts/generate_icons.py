"""Genera le icone PWA e del profilo a partire dalla palette utente.

Le icone sono asset statici: rigenerarli dopo una modifica ai colori in
``static/css/palette.css`` eseguendo ``python scripts/generate_icons.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

# Stesso ordine di --user-color-1 .. --user-color-8 in palette.css.
USER_COLORS = (
    "#3A86FF",
    "#6C5CE7",
    "#00A8A8",
    "#2D6A4F",
    "#C77DFF",
    "#FF6F91",
    "#8D99AE",
    "#E9C46A",
)

ICON_DIR = Path(__file__).resolve().parents[1] / "static" / "icons"
PROFILE_DIR = ICON_DIR / "profile"
APP_NAME = "Chalk & Track - PalaEnrosadira"
BACKGROUND = "#0C0E10"


def _profile_icon(color: str, size: int = 512) -> Image.Image:
    """Icona circolare con un segno a gesso stilizzato."""

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    padding = int(size * 0.08)
    draw.ellipse(
        (padding, padding, size - padding, size - padding),
        fill=color,
    )
    draw.line(
        [
            (size * 0.30, size * 0.66),
            (size * 0.50, size * 0.34),
            (size * 0.70, size * 0.66),
        ],
        fill=(255, 255, 255, 255),
        width=max(4, int(size * 0.055)),
        joint="curve",
    )
    return image


def _manifest(color: str, icon_id: int | None) -> dict:
    icons = (
        [
            {
                "src": f"/static/icons/profile/Icon_{icon_id}.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            }
        ]
        if icon_id is not None
        else [
            {
                "src": "/static/icons/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/icons/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ]
    )
    return {
        "name": APP_NAME,
        "short_name": "Chalk & Track",
        "description": "Traccia e condividi i blocchi di arrampicata della palestra.",
        "lang": "it",
        "start_url": "/",
        "scope": "/",
        "icons": icons,
        "theme_color": color,
        "background_color": BACKGROUND,
        "display": "standalone",
    }


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    base_icon = _profile_icon(USER_COLORS[0])

    for icon_id, color in enumerate(USER_COLORS):
        icon = base_icon if icon_id == 0 else _profile_icon(color)
        icon.save(PROFILE_DIR / f"Icon_{icon_id}.png")
        _write_json(
            ICON_DIR / f"site-color-{icon_id}.webmanifest",
            _manifest(color, icon_id),
        )

    for filename, size in (
        ("apple-touch-icon.png", 180),
        ("favicon-32x32.png", 32),
        ("favicon-16x16.png", 16),
        ("android-chrome-192x192.png", 192),
        ("android-chrome-512x512.png", 512),
    ):
        base_icon.resize((size, size), Image.LANCZOS).save(ICON_DIR / filename)

    _write_json(ICON_DIR / "site.webmanifest", _manifest("#F47321", None))
    print(f"Icone generate in {ICON_DIR}")


if __name__ == "__main__":
    main()
