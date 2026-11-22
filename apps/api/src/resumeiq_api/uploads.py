"""Read an uploaded resume into plain text, in memory only.

Nothing here writes to disk or logs content. The text is masked for contact
details before anything else sees it. Supported: PDF (text-based, not scanned),
DOCX, TXT and Markdown. Parsing approach ported from the v0.9 resume_parser.
"""

from __future__ import annotations

import io
import re
import zipfile

from .privacy import mask_pii

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_PDF_PAGES = 6
MAX_TEXT_CHARS = 20_000

_BULLET_CHARS = re.compile(r"^\s*[•●▪◦‣∙·]\s*", re.M)


class UploadError(ValueError):
    """A problem the user can fix: wrong type, too large, unreadable."""


def read_resume(filename: str, data: bytes) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadError("Files are limited to 2 MB.")
    name = filename.lower()
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise UploadError("That file is not a valid PDF.")
        text = _pdf_text(data)
    elif name.endswith(".docx"):
        if not zipfile.is_zipfile(io.BytesIO(data)):
            raise UploadError("That file is not a valid DOCX.")
        text = _docx_text(data)
    elif name.endswith((".txt", ".md")):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise UploadError("Text files must be UTF-8.") from error
    else:
        raise UploadError("Upload a PDF, DOCX or TXT file.")

    text = _BULLET_CHARS.sub("- ", text.replace("\r\n", "\n"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text.split()) < 30:
        raise UploadError("Very little text was found. Scanned PDFs are not supported; try a DOCX or a text-based PDF.")
    return mask_pii(text[:MAX_TEXT_CHARS])


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise UploadError("Password-protected PDFs are not supported.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise UploadError(f"Resumes are limited to {MAX_PDF_PAGES} pages.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except UploadError:
        raise
    except Exception as error:  # malformed files raise many different errors
        raise UploadError("The PDF could not be read.") from error


def _docx_text(data: bytes) -> str:
    from docx import Document

    try:
        doc = Document(io.BytesIO(data))
    except Exception as error:
        raise UploadError("The DOCX could not be read.") from error
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower() if para.style is not None else ""
        lines.append(f"- {text}" if "list" in style else text)
    for table in doc.tables:  # many resume templates put content in tables
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append("; ".join(dict.fromkeys(cells)))
    return "\n".join(lines)
