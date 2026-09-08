import asyncio
import io
import os
from pathlib import Path
from typing import List, Dict, Any
import pymupdf  # PyMuPDF
from PIL import Image
import winocr

from .config import Config

class SmartExtractor:
    """
    Extracts text from PDFs using a smart hybrid approach:
    1. Direct native digital text extraction if available and complete.
    2. Fallback to local high-resolution Windows OCR for raster/Canva slide pages.
    """

    def __init__(self, scale: float = None):
        self.scale = scale or Config.OCR_SCALE

    async def _ocr_pixmap(self, pix) -> str:
        """Converts PyMuPDF pixmap to PIL Image and runs Windows native OCR."""
        # Use in-memory PNG bytes for guaranteed color/stride/alpha compatibility
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_result = await winocr.recognize_pil(img, "en")
        
        # Windows OCR returns individual OcrLine objects in .lines.
        # Joining with newlines preserves distinct slide bullet points and code lines.
        if hasattr(ocr_result, "lines") and ocr_result.lines:
            valid_lines = [line.text.strip() for line in ocr_result.lines if line.text.strip()]
            return "\n".join(valid_lines)
        return ocr_result.text

    def _filter_repetitive_lines(self, raw_lines: List[str]) -> List[str]:
        """Filters out watermarks, lecturer credentials, and common footer noise."""
        clean = []
        noise_phrases = [
            "bsc (hons)",
            "msc applied",
            "maheesha fernando",
            "university of",
            "reading",
        ]
        for line in raw_lines:
            s = line.strip()
            if not s:
                continue
            
            s_lower = s.lower()
            # If line contains lecturer watermark or credential footer
            if any(term in s_lower for term in noise_phrases):
                continue
            
            # Skip isolated bullet or separator artifacts
            if s in ["|", "I", "•", "—", "-", "_", "~"]:
                continue

            clean.append(s)
        return clean

    async def extract_single_pdf(self, pdf_path: str, callback=None, doc_idx: int = 1, total_docs: int = 1) -> Dict[str, Any]:
        """Extracts all content from a single PDF file."""
        p_path = Path(pdf_path)
        if not p_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        msg = f"[Extractor] Processing: {p_path.name} (File {doc_idx}/{total_docs})"
        print(f"\n{msg}")
        if callback:
            callback(msg, 0.05 + (doc_idx - 1) / total_docs * 0.3)

        doc = pymupdf.open(str(p_path))
        num_pages = len(doc)
        pages_data = []

        for page_idx in range(num_pages):
            page = doc[page_idx]
            native_text = page.get_text("text").strip()
            
            # Check native digital text
            native_lines = [l.strip() for l in native_text.split("\n") if l.strip()]
            filtered_native = self._filter_repetitive_lines(native_lines)
            
            # If native text is minimal (< 120 chars or < 3 lines), run OCR
            if len(" ".join(filtered_native)) < 120 or len(filtered_native) < 3:
                mat = pymupdf.Matrix(self.scale, self.scale)
                pix = page.get_pixmap(matrix=mat)
                ocr_text = await self._ocr_pixmap(pix)
                ocr_lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]
                filtered_ocr = self._filter_repetitive_lines(ocr_lines)
                
                # If OCR discovered more actual content, use OCR
                if len(" ".join(filtered_ocr)) > len(" ".join(filtered_native)):
                    filtered = filtered_ocr
                    method = "Local OCR"
                else:
                    filtered = filtered_native
                    method = "Native Digital"
            else:
                filtered = filtered_native
                method = "Native Digital"

            page_content = "\n".join(filtered)
            pages_data.append({
                "page_number": page_idx + 1,
                "extraction_method": method,
                "text": page_content
            })
            page_status = f"  • {p_path.name} Page {page_idx + 1:02d}/{num_pages:02d} ({method}): {len(filtered)} lines"
            print(page_status)
            if callback:
                doc_progress = (page_idx + 1) / num_pages
                overall_progress = 0.05 + (((doc_idx - 1) + doc_progress) / total_docs) * 0.3
                callback(page_status, overall_progress)

        doc.close()
        return {
            "file_name": p_path.name,
            "file_path": str(p_path),
            "total_pages": num_pages,
            "pages": pages_data
        }

    async def extract_multiple_pdfs(self, pdf_paths: List[str], callback=None) -> List[Dict[str, Any]]:
        """Extracts content from up to MAX_PDF_LIMIT files."""
        if len(pdf_paths) > Config.MAX_PDF_LIMIT:
            raise ValueError(f"Input exceeds maximum allowed PDF limit ({Config.MAX_PDF_LIMIT} files). Provided: {len(pdf_paths)}")

        results = []
        total_docs = len(pdf_paths)
        for idx, path in enumerate(pdf_paths, start=1):
            data = await self.extract_single_pdf(path, callback=callback, doc_idx=idx, total_docs=total_docs)
            results.append(data)
        return results

    def extract(self, pdf_paths: List[str], callback=None) -> List[Dict[str, Any]]:
        """Synchronous wrapper for convenience."""
        return asyncio.run(self.extract_multiple_pdfs(pdf_paths, callback=callback))

