import logging
import os
import shutil
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Configure Tesseract OCR path dynamically
def _configure_tesseract():
    custom_path = os.getenv("TESSERACT_PATH")
    if custom_path and Path(custom_path).exists():
        pytesseract.pytesseract.tesseract_cmd = custom_path
        return custom_path

    which_path = shutil.which("tesseract")
    if which_path:
        pytesseract.pytesseract.tesseract_cmd = which_path
        return which_path

    default_windows_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_windows_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(default_windows_path)
        return str(default_windows_path)

    return None

_configure_tesseract()


def load_resume(file_path: str) -> list[Document]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Resume file is empty (0 bytes): {path}")

    extension = path.suffix.lower()

    # --------------------------------
    # IMAGE FILE
    # --------------------------------
    if extension in [".png", ".jpg", ".jpeg"]:
        try:
            image = Image.open(path)
            text = pytesseract.image_to_string(image, lang="eng").strip()
        except Exception as e:
            raise ValueError(f"Failed to process image resume '{path}': {e}") from e

        if not text:
            raise ValueError(
                f"OCR produced no readable text from image resume: {path}"
            )

        return [
            Document(
                page_content=text,
                metadata={"source": str(path), "ocr": True},
            )
        ]

    # --------------------------------
    # PDF FILE
    # --------------------------------
    elif extension == ".pdf":
        try:
            pdf = pymupdf.open(str(path))
        except Exception as e:
            raise ValueError(f"Failed to open PDF resume '{path}': {e}") from e

        if len(pdf) == 0:
            raise ValueError(f"PDF resume contains 0 pages: {path}")

        documents = []

        for page_number, page in enumerate(pdf):
            # Extract digital text from PDF page
            text = page.get_text().strip()
            ocr_text = ""

            # If page text is very sparse (< 40 characters), attempt OCR for scanned page
            if len(text) < 40:
                try:
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                    image = Image.frombytes(
                        "RGB", [pix.width, pix.height], pix.samples
                    )
                    ocr_text = pytesseract.image_to_string(
                        image, lang="eng"
                    ).strip()
                except Exception as e:
                    logger.warning(
                        "OCR failed on page %d of '%s': %s",
                        page_number,
                        path,
                        e,
                    )

            # Use digital text if substantial; otherwise use OCR text if available
            if text and ocr_text:
                final_text = f"{text}\n{ocr_text}"
            elif text:
                final_text = text
            else:
                final_text = ocr_text

            if final_text:
                documents.append(
                    Document(
                        page_content=final_text,
                        metadata={
                            "source": str(path),
                            "page": page_number,
                            "ocr": bool(ocr_text and not text),
                        },
                    )
                )

        if not documents:
            raise ValueError(
                f"Could not extract any readable text from PDF resume: {path}"
            )

        return documents

    else:
        raise ValueError(
            f"Unsupported file type '{extension}'. Supported types: .pdf, .png, .jpg, .jpeg"
        )