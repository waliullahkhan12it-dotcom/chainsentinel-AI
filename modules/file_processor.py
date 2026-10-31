"""
ChainSentinel AI
Universal File Investigation Engine

Supported formats:
PDF, DOCX, TXT, RTF, CSV, XLSX, XLS, JSON, XML,
LOG, SYSLOG, SOL, PCAP, PCAPNG, PNG, JPG, JPEG, ZIP.

Security:
- SHA-256 evidence hashing
- File size restrictions
- File signature checks
- Safe ZIP inspection
- ZIP path traversal protection
- Archive expansion limits
- No execution of uploaded files
- XML entity protection
"""

import csv
import hashlib
import io
import json
import logging
import os
import re
import zipfile
from pathlib import PurePosixPath
from datetime import datetime
from collections import Counter

import pandas as pd

logger = logging.getLogger("chainsentinel.file_processor")

# =========================================================
# SECURITY LIMITS
# =========================================================

MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_TEXT_CHARS = 200_000
MAX_ZIP_FILES = 25
MAX_ZIP_TOTAL_SIZE = 20 * 1024 * 1024
MAX_ARCHIVE_DEPTH = 2
MAX_PCAP_PACKETS = 5000

SUPPORTED_EXTENSIONS = {
    "pdf", "docx", "txt", "rtf", "csv",
    "xlsx", "xls", "json", "xml",
    "log", "syslog", "sol",
    "pcap", "pcapng",
    "png", "jpg", "jpeg", "zip"
}

# =========================================================
# BASIC UTILITIES
# =========================================================

def calculate_sha256(data):
    """Calculate SHA-256 hash of file bytes."""
    return hashlib.sha256(data).hexdigest()


def get_extension(filename):
    """Return lowercase file extension."""
    return os.path.splitext(filename)[1].lower().lstrip(".")


def detect_signature(data):
    """
    Identify common binary file signatures.
    Text formats are identified separately.
    """

    if data.startswith(b"%PDF-"):
        return "pdf"

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    if data.startswith(b"PK\x03\x04"):
        return "zip"

    if data.startswith(b"II*\x00") or data.startswith(b"MM\x00*"):
        return "tiff"

    if data.startswith(b"\xd4\xc3\xb2\xa1") or \
       data.startswith(b"\xa1\xb2\xc3\xd4") or \
       data.startswith(b"\x4d\x3c\xb2\xa1") or \
       data.startswith(b"\xa1\xb2\x3c\x4d"):
        return "pcap"

    if data.startswith(b"\x0a\x0d\x0d\x0a"):
        return "pcapng"

    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"

    if data.startswith(b"BM"):
        return "bmp"

    return "text_or_unknown"


def validate_file(filename, data):
    """Validate file extension, size and binary signature."""

    if not filename or not isinstance(filename, str):
        raise ValueError("Invalid filename.")

    if not isinstance(data, bytes):
        raise ValueError("File content must be bytes.")

    if len(data) == 0:
        raise ValueError("The uploaded file is empty.")

    if len(data) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 50 MB upload limit.")

    extension = get_extension(filename)

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported format: .{extension or 'unknown'}"
        )

    signature = detect_signature(data)

    # Validate binary formats.
    expected_signatures = {
        "pdf": ["pdf"],
        "png": ["png"],
        "jpg": ["jpeg"],
        "jpeg": ["jpeg"],
        "zip": ["zip"],
        "pcap": ["pcap"],
        "pcapng": ["pcapng"]
    }

    if extension in expected_signatures:
        if signature not in expected_signatures[extension]:
            raise ValueError(
                f"File signature does not match .{extension} format."
            )

    # DOCX and XLSX are ZIP-based containers.
    if extension in {"docx", "xlsx", "xls"}:
        if extension in {"docx", "xlsx"} and signature != "zip":
            raise ValueError(
                f"The .{extension} file is not a valid ZIP-based document."
            )

    # Reject obvious binary data masquerading as text.
    text_extensions = {
        "txt", "rtf", "csv", "json", "xml",
        "log", "syslog", "sol"
    }

    if extension in text_extensions and signature != "text_or_unknown":
        raise ValueError(
            "Binary file detected. Its content does not match the text format."
        )

    return {
        "extension": extension,
        "signature": signature,
        "size_bytes": len(data),
        "sha256": calculate_sha256(data)
    }


def safe_decode(data):
    """Decode text without crashing on unusual characters."""
    return data.decode("utf-8-sig", errors="replace")


def trim_text(text):
    """Limit extracted text to a safe processing size."""
    return str(text)[:MAX_TEXT_CHARS]


# =========================================================
# TEXT EXTRACTION
# =========================================================

def extract_text(data):
    return trim_text(safe_decode(data))


def extract_rtf(data):
    """Basic RTF text extraction without executing content."""
    text = safe_decode(data)

    text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)
    text = re.sub(r"[{}]", " ", text)

    return trim_text(text)


# =========================================================
# PDF EXTRACTION
# =========================================================

def extract_pdf(data):
    try:
        import fitz

        document = fitz.open(stream=data, filetype="pdf")
        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return trim_text("\n".join(pages))

    except Exception as exc:
        raise ValueError(f"PDF extraction failed: {exc}") from exc


# =========================================================
# WORD DOCUMENT EXTRACTION
# =========================================================

def extract_docx(data):
    try:
        from docx import Document

        document = Document(io.BytesIO(data))

        paragraphs = [
            paragraph.text for paragraph in document.paragraphs
        ]

        for table in document.tables:
            for row in table.rows:
                paragraphs.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        return trim_text("\n".join(paragraphs))

    except Exception as exc:
        raise ValueError(f"DOCX extraction failed: {exc}") from exc


# =========================================================
# EXCEL EXTRACTION
# =========================================================

def extract_excel(data, extension):
    try:
        engine = "openpyxl" if extension == "xlsx" else "xlrd"

        sheets = pd.read_excel(
            io.BytesIO(data),
            sheet_name=None,
            engine=engine
        )

        results = []

        for sheet_name, frame in sheets.items():
            results.append(f"SHEET: {sheet_name}")
            results.append(frame.head(1000).to_string(index=False))

        return trim_text("\n".join(results))

    except Exception as exc:
        raise ValueError(f"Excel extraction failed: {exc}") from exc


# =========================================================
# CSV EXTRACTION
# =========================================================

def extract_csv(data):
    try:
        frame = pd.read_csv(
            io.BytesIO(data),
            encoding="utf-8-sig",
            on_bad_lines="warn",
            nrows=10000
        )

        if frame.empty:
            raise ValueError("CSV contains no data rows.")

        return trim_text(frame.head(1000).to_string(index=False))

    except Exception as exc:
        raise ValueError(f"CSV extraction failed: {exc}") from exc


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(data):
    try:
        obj = json.loads(safe_decode(data))

        return trim_text(
            json.dumps(obj, indent=2, ensure_ascii=False)
        )

    except Exception as exc:
        raise ValueError(f"JSON parsing failed: {exc}") from exc


# =========================================================
# XML EXTRACTION
# =========================================================

def extract_xml(data):
    try:
        from defusedxml import ElementTree

        root = ElementTree.fromstring(data)

        lines = []

        def walk(element, depth=0):
            if depth > 30:
                return

            tag = str(element.tag)
            text = (element.text or "").strip()

            if text:
                lines.append(f"{tag}: {text}")

            for child in list(element):
                walk(child, depth + 1)

        walk(root)

        return trim_text("\n".join(lines))

    except Exception as exc:
        raise ValueError(f"Safe XML parsing failed: {exc}") from exc


# =========================================================
# IMAGE OCR
# =========================================================

def extract_image(data):
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(data))
        image.verify()

        image = Image.open(io.BytesIO(data))
        image = image.convert("RGB")

        text = pytesseract.image_to_string(image)

        if not text.strip():
            return (
                "Image successfully opened, but OCR did not identify readable text."
            )

        return trim_text(text)

    except ImportError:
        return (
            "Image identified successfully. OCR libraries are not installed."
        )

    except Exception as exc:
        return f"Image OCR could not be completed: {exc}"


# =========================================================
# PCAP / PCAPNG NETWORK CAPTURE
# =========================================================

def extract_pcap(data):
    try:
        from scapy.utils import PcapReader

        packets = []

        with PcapReader(io.BytesIO(data)) as reader:
            for index, packet in enumerate(reader):
                if index >= MAX_PCAP_PACKETS:
                    break

                packets.append({
                    "packet": index + 1,
                    "source": packet.sprintf("%IP.src%"),
                    "destination": packet.sprintf("%IP.dst%"),
                    "protocol": packet.name,
                    "length": len(packet)
                })

        if not packets:
            return "Network capture contains no readable packets."

        return trim_text(
            pd.DataFrame(packets).to_string(index=False)
        )

    except ImportError:
        return "Scapy is not installed. Network capture analysis unavailable."

    except Exception as exc:
        raise ValueError(
            f"Network capture parsing failed: {exc}"
        ) from exc


# =========================================================
# ZIP SAFETY
# =========================================================

def is_safe_archive_path(name):
    """Reject absolute paths and directory traversal."""
    path = PurePosixPath(name)

    if path.is_absolute():
        return False

    if ".." in path.parts:
        return False

    if "\\" in name:
        return False

    if "\x00" in name:
        return False

    return True


def inspect_zip(data, depth=0, counter=None):
    """
    Inspect archive contents in memory.
    Never extract files to disk or execute them.
    """

    if counter is None:
        counter = {"files": 0, "total_size": 0}

    if depth > MAX_ARCHIVE_DEPTH:
        raise ValueError("Maximum archive nesting depth exceeded.")

    results = []

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:

            for info in archive.infolist():

                if info.is_dir():
                    continue

                counter["files"] += 1

                if counter["files"] > MAX_ZIP_FILES:
                    raise ValueError("ZIP contains too many files.")

                if not is_safe_archive_path(info.filename):
                    raise ValueError(
                        "Unsafe ZIP path detected. Archive rejected."
                    )

                if info.flag_bits & 0x1:
                    raise ValueError(
                        "Encrypted ZIP files are not supported."
                    )

                if info.file_size > MAX_ZIP_TOTAL_SIZE:
                    raise ValueError(
                        "A ZIP member exceeds the extraction size limit."
                    )

                counter["total_size"] += info.file_size

                if counter["total_size"] > MAX_ZIP_TOTAL_SIZE:
                    raise ValueError(
                        "ZIP expanded contents exceed 20 MB."
                    )

                if info.file_size > 0 and info.file_size / max(
                    info.compress_size, 1
                ) > 100:
                    raise ValueError(
                        "Suspicious compression ratio detected."
                    )

                member_data = archive.read(info)

                extension = get_extension(info.filename)

                results.append(
                    f"\n--- ARCHIVE MEMBER: {info.filename} ---"
                )

                if extension == "zip":
                    nested = inspect_zip(
                        member_data,
                        depth=depth + 1,
                        counter=counter
                    )
                    results.append(nested)

                elif extension in SUPPORTED_EXTENSIONS - {"zip"}:
                    try:
                        extracted = extract_content(
                            info.filename,
                            member_data,
                            archive_depth=depth + 1
                        )
                        results.append(extracted["text"])

                    except Exception as exc:
                        results.append(
                            f"Member could not be analysed: {exc}"
                        )

                else:
                    results.append("Unsupported archive member skipped.")

        return trim_text("\n".join(results))

    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid or corrupted ZIP archive.") from exc


# =========================================================
# FILE ROUTER
# =========================================================

def extract_content(filename, data, archive_depth=0):
    """Route each supported file to its own extraction pipeline."""

    extension = get_extension(filename)

    if extension == "pdf":
        text = extract_pdf(data)

    elif extension == "docx":
        text = extract_docx(data)

    elif extension == "csv":
        text = extract_csv(data)

    elif extension in {"xlsx", "xls"}:
        text = extract_excel(data, extension)

    elif extension == "json":
        text = extract_json(data)

    elif extension == "xml":
        text = extract_xml(data)

    elif extension == "rtf":
        text = extract_rtf(data)

    elif extension in {"txt", "log", "syslog", "sol"}:
        text = extract_text(data)

    elif extension in {"png", "jpg", "jpeg"}:
        text = extract_image(data)

    elif extension in {"pcap", "pcapng"}:
        text = extract_pcap(data)

    elif extension == "zip":
        if archive_depth > MAX_ARCHIVE_DEPTH:
            raise ValueError("Archive nesting limit exceeded.")

        text = inspect_zip(data, depth=archive_depth)

    else:
        raise ValueError(f"No parser available for .{extension}.")

    return {
        "filename": filename,
        "format": extension.upper(),
        "text": trim_text(text),
        "characters_extracted": len(text)
    }


# =========================================================
# BASIC SECURITY INDICATORS
# =========================================================

def find_indicators(text):
    """
    Identify potentially relevant indicators.
    These are leads for investigation, not proof of compromise.
    """

    patterns = {
        "Ethereum addresses": r"\b0x[a-fA-F0-9]{40}\b",
        "Transaction hashes": r"\b0x[a-fA-F0-9]{64}\b",
        "IPv4 addresses": (
            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ),
        "Email addresses": (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "URLs": r"https?://[^\s<>\"']+"
    }

    findings = {}

    for label, pattern in patterns.items():
        matches = re.findall(pattern, text)
        findings[label] = list(dict.fromkeys(matches))[:100]

    suspicious_terms = [
        "private key",
        "seed phrase",
        "unauthorized",
        "malware",
        "phishing",
        "exploit",
        "suspicious",
        "ransomware",
        "unauthorized transfer"
    ]

    lowered = text.lower()

    findings["Security keywords"] = [
        term for term in suspicious_terms if term in lowered
    ]

    return findings


# =========================================================
# MAIN PUBLIC FUNCTION
# =========================================================

def analyze_uploaded_file(uploaded_file):
    """
    Main function for Streamlit.

    Usage:
        result = analyze_uploaded_file(uploaded_file)

    Returns metadata, extracted content and indicators.
    """

    filename = uploaded_file.name
    data = uploaded_file.getvalue()

    metadata = validate_file(filename, data)

    extracted = extract_content(filename, data)

    indicators = find_indicators(extracted["text"])

    return {
        "success": True,
        "filename": filename,
        "format": extracted["format"],
        "size_bytes": metadata["size_bytes"],
        "sha256": metadata["sha256"],
        "signature": metadata["signature"],
        "extracted_text": extracted["text"],
        "characters_extracted": extracted["characters_extracted"],
        "indicators": indicators,
        "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        "warning": (
            "Extracted indicators are investigation leads, not "
            "confirmed malicious activity."
        )
    }
