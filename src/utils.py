import os
import sys
from pathlib import Path
from typing import List
from .config import Config

def select_pdf_files_gui() -> List[str]:
    """
    Opens a native Windows file selection dialog allowing the user
    to select up to MAX_PDF_LIMIT PDF files.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        print(f"\n[File Selector] Opening file selection dialog (Select 1 to {Config.MAX_PDF_LIMIT} PDF files)...")
        file_paths = filedialog.askopenfilenames(
            title=f"Select up to {Config.MAX_PDF_LIMIT} Lecture PDF Files",
            filetypes=[("PDF Files", "*.pdf")]
        )
        root.destroy()

        selected = list(file_paths)
        return selected

    except Exception as e:
        print(f"[File Selector Warning] GUI dialog failed: {e}. Falling back to console input.")
        return []

def get_input_pdfs() -> List[str]:
    """
    Determines input PDF paths from CLI arguments, GUI file picker,
    or console prompt, enforcing the MAX_PDF_LIMIT.
    """
    # 1. Check CLI arguments
    if len(sys.argv) > 1:
        args_files = sys.argv[1:]
        resolved_files = []
        for f in args_files:
            clean_f = f.strip('"').strip("'")
            if not clean_f.lower().endswith(".pdf"):
                continue
            p = Path(clean_f)
            if p.exists():
                resolved_files.append(str(p.resolve()))
            elif (Path.cwd().parent / clean_f).exists():
                resolved_files.append(str((Path.cwd().parent / clean_f).resolve()))
        if resolved_files:
            if len(resolved_files) > Config.MAX_PDF_LIMIT:
                print(f"[Warning] More than {Config.MAX_PDF_LIMIT} PDFs supplied. Limiting to first {Config.MAX_PDF_LIMIT}.")
                resolved_files = resolved_files[:Config.MAX_PDF_LIMIT]
            return resolved_files

    # 2. Try GUI File Selector
    selected = select_pdf_files_gui()
    if selected:
        if len(selected) > Config.MAX_PDF_LIMIT:
            print(f"[Warning] Selected {len(selected)} files. Limiting to first {Config.MAX_PDF_LIMIT}.")
            selected = selected[:Config.MAX_PDF_LIMIT]
        return selected

    # 3. Interactive Console Prompt
    print(f"\nPlease enter paths to your PDF files (up to {Config.MAX_PDF_LIMIT}, separated by commas):")
    raw_input = input("PDF Paths > ").strip()
    if not raw_input:
        return []

    entered = [p.strip().strip('"').strip("'") for p in raw_input.split(",") if p.strip()]
    valid_pdfs = [p for p in entered if p.lower().endswith(".pdf") and os.path.exists(p)]
    
    if len(valid_pdfs) > Config.MAX_PDF_LIMIT:
        print(f"[Warning] Limiting to first {Config.MAX_PDF_LIMIT} files.")
        valid_pdfs = valid_pdfs[:Config.MAX_PDF_LIMIT]

    return valid_pdfs
