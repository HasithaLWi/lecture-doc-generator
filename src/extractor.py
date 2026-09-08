import asyncio
import concurrent.futures
import io
import os
from pathlib import Path
from typing import List, Dict, Any
import pymupdf  # PyMuPDF
from PIL import Image

try:
    import winocr
    HAS_WINOCR = True
except ImportError:
    winocr = None
    HAS_WINOCR = False

from .config import Config

def _run_async_safely(coro):
    """Safely runs an async coroutine even if an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)

class SmartExtractor:
    """
    Extracts text from PDFs using a smart hybrid approach:
    1. Direct native digital text extraction if available and complete.
    2. Fallback to local high-resolution Windows OCR for raster/Canva slide pages.
    3. Intelligent hybrid merging when slides contain both native text and embedded graphics.
    """

    def __init__(self, scale: float = None):
        self.scale = scale or Config.OCR_SCALE

    async def _ocr_pixmap(self, pix) -> str:
        """Converts PyMuPDF pixmap to PIL Image and runs Windows native OCR with robust fallback."""
        if not HAS_WINOCR:
            return ""
        try:
            png_bytes = pix.tobytes("png")
            with Image.open(io.BytesIO(png_bytes)) as img:
                ocr_result = await winocr.recognize_pil(img, "en")
                
                # Check WinRT OcrResult object or dictionary
                if hasattr(ocr_result, "lines") and ocr_result.lines:
                    valid_lines = []
                    for line in ocr_result.lines:
                        l_text = getattr(line, "text", "") if hasattr(line, "text") else str(line.get("text", "") if isinstance(line, dict) else "")
                        if l_text and l_text.strip():
                            valid_lines.append(l_text.strip())
                    if valid_lines:
                        return "\n".join(valid_lines)
                elif isinstance(ocr_result, dict) and "lines" in ocr_result:
                    valid_lines = [l["text"].strip() for l in ocr_result["lines"] if isinstance(l, dict) and l.get("text", "").strip()]
                    if valid_lines:
                        return "\n".join(valid_lines)
                
                if hasattr(ocr_result, "text"):
                    return ocr_result.text or ""
                elif isinstance(ocr_result, dict):
                    return ocr_result.get("text", "") or ""
                return str(ocr_result) if ocr_result else ""
        except Exception as e:
            print(f"[Extractor Warning] OCR failed on page: {e}")
            return ""

    def _filter_repetitive_lines(self, raw_lines: List[str]) -> List[str]:
        """Filters out watermarks, lecturer credentials, and common footer noise while preserving lecture content."""
        clean = []
        noise_phrases = [
            "bsc (hons)",
            "msc applied",
            "maheesha fernando",
            "university of reading",
        ]
        # Isolated bullet symbols to remove
        separator_symbols = {"|", "•", "—", "-", "_", "~", "·", "▪", "▫", "►", "❖", "★"}

        for line in raw_lines:
            s = line.strip()
            if not s:
                continue
            
            s_lower = s.lower()
            # If line contains lecturer watermark or credential footer
            if any(term in s_lower for term in noise_phrases):
                continue
            
            # Skip isolated bullet or separator artifacts (do not strip alphanumeric like 'I')
            if s in separator_symbols:
                continue

            clean.append(s)
        return clean

    def _merge_native_and_ocr(self, native_lines: List[str], ocr_lines: List[str]) -> List[str]:
        """Merges native digital text with OCR text to prevent any information loss."""
        if not ocr_lines:
            return native_lines
        if not native_lines:
            return ocr_lines

        merged = list(native_lines)
        native_lower = [line.lower() for line in native_lines]

        for o_line in ocr_lines:
            o_lower = o_line.lower()
            # Check if this OCR line is already represented in native text
            is_duplicate = False
            for n_low in native_lower:
                if o_lower == n_low or (len(o_lower) > 6 and o_lower in n_low) or (len(n_low) > 6 and n_low in o_lower):
                    is_duplicate = True
                    break
            if not is_duplicate:
                merged.append(o_line)
                native_lower.append(o_lower)

        return merged

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
            
            has_images = len(page.get_images()) > 0
            is_sparse_native = len(" ".join(filtered_native)) < 120 or len(filtered_native) < 3

            # Run OCR if native text is sparse or if page contains embedded graphics
            if is_sparse_native or has_images:
                mat = pymupdf.Matrix(self.scale, self.scale)
                pix = page.get_pixmap(matrix=mat)
                ocr_text = await self._ocr_pixmap(pix)
                ocr_lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]
                filtered_ocr = self._filter_repetitive_lines(ocr_lines)
                
                if is_sparse_native:
                    if len(" ".join(filtered_ocr)) > len(" ".join(filtered_native)):
                        filtered = self._merge_native_and_ocr(filtered_native, filtered_ocr)
                        method = "Local OCR"
                    else:
                        filtered = filtered_native
                        method = "Native Digital"
                else:
                    # Native text was substantial, but page has graphics/code screenshots
                    if filtered_ocr:
                        filtered = self._merge_native_and_ocr(filtered_native, filtered_ocr)
                        method = "Hybrid (Digital + OCR)"
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
        """Synchronous wrapper for convenience with safe async event loop handling."""
        return _run_async_safely(self.extract_multiple_pdfs(pdf_paths, callback=callback))

