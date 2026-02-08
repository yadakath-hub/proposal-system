"""
PDF converter — DOCX → PDF via LibreOffice headless, plus merge / watermark.
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path

import fitz  # PyMuPDF


async def docx_to_pdf(docx_bytes: bytes) -> bytes | None:
    """Convert DOCX bytes to PDF bytes using LibreOffice headless.
    Returns None if LibreOffice is not available.
    """
    lo_path = shutil.which("libreoffice") or shutil.which("soffice")
    if lo_path is None:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, "input.docx")
        with open(docx_path, "wb") as f:
            f.write(docx_bytes)

        proc = await asyncio.create_subprocess_exec(
            lo_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", tmpdir,
            docx_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        pdf_path = os.path.join(tmpdir, "input.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
    return None


def merge_pdfs(pdf_bytes_list: list[bytes]) -> bytes:
    """Merge multiple PDFs into one."""
    writer = fitz.open()
    for pdf_bytes in pdf_bytes_list:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        writer.insert_pdf(doc)
        doc.close()
    out = writer.tobytes()
    writer.close()
    return out


def add_watermark(pdf_bytes: bytes, watermark_text: str) -> bytes:
    """Add diagonal watermark text to every page."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        rect = page.rect
        # Diagonal text across the page
        point = fitz.Point(rect.width / 4, rect.height / 2)
        page.insert_text(
            point,
            watermark_text,
            fontsize=48,
            color=(0.85, 0.85, 0.85),
            rotate=45,
        )
    out = doc.tobytes()
    doc.close()
    return out


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count
