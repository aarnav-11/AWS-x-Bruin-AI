from __future__ import annotations

from typing import Optional

import pdfplumber


def read_pdf_text(path: str, max_pages: Optional[int] = None) -> str:
    try:
        text_parts = []
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for p in pages:
                text_parts.append(p.extract_text() or "")
        return "\n".join(text_parts).strip()
    except Exception as e:
        return f"PDF_READ_ERROR: {e}"

