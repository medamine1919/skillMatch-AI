from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from src.utils import clean_text


def extract_text_from_image(file_path: str | Path, lang: str = "eng+fra") -> str:
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang=lang)
    return clean_text(text)
