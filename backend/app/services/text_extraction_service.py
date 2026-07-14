# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
Text extraction service for DocuSage documents.

Extracts plain text from supported file formats and enforces the raw extraction
size limit before summarization.
"""

import logging
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from ..core.config import app_settings
from ..core.exceptions import TextExtractionError

logger = logging.getLogger("services.text_extraction")


def _enforce_extraction_limit(text: str, source_label: str) -> str:
    """
    Truncate extracted text to the configured raw extraction byte limit.

    Args:
        text: Extracted plain text.
        source_label: File identifier used in logs.

    Returns:
        str: Text within MAX_EXTRACTED_TEXT_BYTES.
    """
    encoded = text.encode("utf-8")
    if len(encoded) <= app_settings.MAX_EXTRACTED_TEXT_BYTES:
        logger.debug(
            "Extracted text within limit for %s: %s bytes",
            source_label,
            len(encoded),
        )
        return text

    truncated_bytes = encoded[: app_settings.MAX_EXTRACTED_TEXT_BYTES]
    truncated_text = truncated_bytes.decode("utf-8", errors="ignore")
    logger.warning(
        "Extracted text truncated for %s: original=%s bytes, limit=%s bytes",
        source_label,
        len(encoded),
        app_settings.MAX_EXTRACTED_TEXT_BYTES,
    )
    return truncated_text


def _extract_from_pdf(file_path: Path) -> str:
    """
    Extract text from a PDF document.

    Args:
        file_path: Path to the PDF file.

    Returns:
        str: Extracted plain text.

    Raises:
        TextExtractionError: If PDF parsing fails.
    """
    logger.info("Extracting text from PDF: %s", file_path)
    try:
        reader = PdfReader(str(file_path))
        pages_text = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
            logger.debug("PDF page %s extracted (%s chars)", page_number, len(page_text))

        combined = "\n".join(pages_text).strip()
        if not combined:
            raise TextExtractionError("No readable text could be extracted from the PDF.")
        return combined
    except TextExtractionError:
        raise
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", file_path, exc)
        raise TextExtractionError(f"PDF extraction failed: {exc}") from exc


def _extract_from_docx(file_path: Path) -> str:
    """
    Extract text from a DOCX document.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        str: Extracted plain text.

    Raises:
        TextExtractionError: If DOCX parsing fails.
    """
    logger.info("Extracting text from DOCX: %s", file_path)
    try:
        document = DocxDocument(str(file_path))
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        combined = "\n".join(paragraphs).strip()
        if not combined:
            raise TextExtractionError("No readable text could be extracted from the DOCX file.")
        logger.debug("DOCX extraction complete for %s (%s chars)", file_path, len(combined))
        return combined
    except TextExtractionError:
        raise
    except Exception as exc:
        logger.error("DOCX extraction failed for %s: %s", file_path, exc)
        raise TextExtractionError(f"DOCX extraction failed: {exc}") from exc


def _extract_from_plain_text(file_path: Path) -> str:
    """
    Extract text from a plain-text based file.

    Args:
        file_path: Path to the text file.

    Returns:
        str: File contents as plain text.

    Raises:
        TextExtractionError: If the file cannot be decoded.
    """
    logger.info("Reading plain text file: %s", file_path)
    try:
        raw_bytes = file_path.read_bytes()
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                text = raw_bytes.decode(encoding).strip()
                if text:
                    logger.debug(
                        "Plain text decoded with %s for %s (%s chars)",
                        encoding,
                        file_path,
                        len(text),
                    )
                    return text
            except UnicodeDecodeError:
                logger.debug("Decode failed with %s for %s", encoding, file_path)
                continue
        raise TextExtractionError("Unable to decode text file with supported encodings.")
    except TextExtractionError:
        raise
    except Exception as exc:
        logger.error("Plain text extraction failed for %s: %s", file_path, exc)
        raise TextExtractionError(f"Plain text extraction failed: {exc}") from exc


def extract_text_from_file(file_path: Path, mime_type: str, original_filename: str) -> str:
    """
    Extract plain text from a supported document file.

    Args:
        file_path: Filesystem path to the uploaded document.
        mime_type: Reported MIME type of the document.
        original_filename: Original client filename.

    Returns:
        str: Extracted text within the raw extraction byte limit.

    Raises:
        TextExtractionError: If extraction fails or no text is found.
    """
    extension = Path(original_filename).suffix.lower()
    logger.info(
        "Starting text extraction: file=%s, mime=%s, extension=%s",
        file_path,
        mime_type,
        extension,
    )

    if extension == ".pdf" or mime_type == "application/pdf":
        extracted = _extract_from_pdf(file_path)
    elif extension == ".docx" or mime_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        extracted = _extract_from_docx(file_path)
    else:
        extracted = _extract_from_plain_text(file_path)

    return _enforce_extraction_limit(extracted, original_filename)
