import io

import pytest

from resumeiq_api.privacy import mask_pii
from resumeiq_api.uploads import MAX_UPLOAD_BYTES, UploadError, read_resume

RESUME = (
    "Sam Rivera\nsam.rivera@example.com · +1 (780) 555-0199 · linkedin.com/in/samrivera\n\nEXPERIENCE\n"
    "• Built a FastAPI service that serves a churn model to the billing team every night.\n"
    "• Wrote SQL in PostgreSQL to assemble weekly training tables for three product lines.\n"
    "• Presented model results to finance managers in plain language each quarter.\n"
)


def _docx_bytes(lines: list[str]) -> bytes:
    from docx import Document

    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _pdf_bytes(text: str) -> bytes:
    # A minimal text PDF, written by hand so the test needs no PDF writer library.
    lines = text.splitlines()
    stream = (
        "BT /F1 10 Tf 40 780 Td 12 TL "
        + " ".join(f"({line.replace('(', '[').replace(')', ']')}) Tj T*" for line in lines)
        + " ET"
    )
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return out.encode("latin-1")


def test_text_upload_is_masked_and_bullets_normalised():
    text = read_resume("resume.txt", RESUME.encode())
    assert "example.com" not in text and "555-0199" not in text and "linkedin" not in text
    assert "- Built a FastAPI service" in text


def test_docx_upload():
    text = read_resume("resume.docx", _docx_bytes(RESUME.splitlines()))
    assert "Wrote SQL in PostgreSQL" in text
    assert "sam.rivera" not in text


def test_pdf_upload():
    text = read_resume("resume.pdf", _pdf_bytes(RESUME.replace("•", "-")))
    assert "Wrote SQL in PostgreSQL" in text


@pytest.mark.parametrize(
    ("name", "data", "message"),
    [
        ("resume.exe", b"MZ", "PDF, DOCX or TXT"),
        ("resume.pdf", b"not a pdf", "not a valid PDF"),
        ("resume.docx", b"not a zip", "not a valid DOCX"),
        ("resume.txt", b"too short", "Very little text"),
        ("resume.txt", b"x" * (MAX_UPLOAD_BYTES + 1), "2 MB"),
    ],
)
def test_bad_uploads_are_rejected_with_a_clear_message(name, data, message):
    with pytest.raises(UploadError, match=message):
        read_resume(name, data)


def test_mask_pii_keeps_ordinary_numbers():
    assert mask_pii("Served 14 stores in 2024 · call 780-555-0199") == "Served 14 stores in 2024 · call [phone hidden]"
