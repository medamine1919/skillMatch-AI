from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document

from src.utils import clean_text


def extract_text_from_pdf(file_path: str | Path) -> str:
    doc = fitz.open(str(file_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return clean_text("\n".join(pages))


def extract_text_from_docx(file_path: str | Path) -> str:
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return clean_text("\n".join(paragraphs))


def extract_text(file_path: str | Path) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)

    raise ValueError(f"Unsupported file extension for text extraction: {ext}")
