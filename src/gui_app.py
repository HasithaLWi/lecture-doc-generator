import os
import sys
import threading
import webbrowser
from pathlib import Path
from typing import List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pymupdf

from .config import Config
from .extractor import SmartExtractor
from .synthesizer import AISynthesizer
from .doc_builder import DocumentBuilder

# Configure CustomTkinter default theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TextRedirector:
    """Redirects stdout/stderr writes to both the console and a GUI callback."""
    def __init__(self, original_stream, write_callback):
        self.original_stream = original_stream
        self.write_callback = write_callback

    def write(self, text: str):
        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()
        if self.write_callback:
            self.write_callback(text)

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()

class LectureDocGeneratorGUI(ctk.CTk):
    """
    Modern Desktop Studio for Lecture Document Generator.
    Built with CustomTkinter for high-DPI scaling, dark/light modes,
    and responsive, non-blocking background task execution.
    """

    COLOR_TEAL = "#0E8388"
    COLOR_TEAL_HOVER = "#0B666A"
    COLOR_NAVY = "#0F2C59"
    COLOR_CARD_DARK = "#1E293B"
    COLOR_BG_DARK = "#0F172A"
    COLOR_BORDER = "#334155"
    COLOR_SUCCESS = "#10B981"
    COLOR_ERROR = "#EF4444"
    COLOR_WARNING = "#F59E0B"

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title(f"Lecture Document Generator {Config.VERSION} — Desktop Studio")
        self.geometry("1100x780")
        self.minsize(980, 680)

        # State Variables
        self.selected_pdfs: List[str] = []
        self.is_processing = False
        self.last_generated_docx: Optional[str] = None
        self.last_generated_doc: Optional[str] = None
        self.show_api_key = False

        # Build UI
        self._setup_layout()
        self._setup_stdout_redirect()

    def _setup_stdout_redirect(self):
        """Tees sys.stdout so that print statements also stream into the GUI console."""
        self.orig_stdout = sys.stdout
        sys.stdout = TextRedirector(self.orig_stdout, self._append_log_threadsafe)

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Top Header Banner
        self._build_header()

        # 2. Main Body (2 Columns)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 15))
        self.main_frame.grid_columnconfigure(0, weight=4)  # Left column: Files & Settings
        self.main_frame.grid_columnconfigure(1, weight=5)  # Right column: Logs & Action
        self.main_frame.grid_rowconfigure(0, weight=1)

        self._build_left_column()
        self._build_right_column()

    # -------------------------------------------------------------------------
    # Header Section
    # -------------------------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color=self.COLOR_CARD_DARK)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        # Left: App Title & Subtitle
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        title_lbl = ctk.CTkLabel(
            title_box,
            text="📚 Lecture Document Generator",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            title_box,
            text=f"AI-Powered Textbook-Grade Word Study Guides  •  {Config.VERSION}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8"
        )
        subtitle_lbl.pack(anchor="w")

        # Right: Author Badge, GitHub Button & Theme Switch
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right", padx=20, pady=10)

        author_lbl = ctk.CTkLabel(
            actions_box,
            text=f"By {Config.AUTHOR}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#38BDF8"
        )
        author_lbl.pack(side="left", padx=(0, 12))

        gh_btn = ctk.CTkButton(
            actions_box,
            text="GitHub",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: webbrowser.open(Config.GITHUB)
        )
        gh_btn.pack(side="left", padx=(0, 12))

        self.theme_switch = ctk.CTkSwitch(
            actions_box,
            text="Dark Mode",
            font=ctk.CTkFont(size=11),
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="left")

    def _toggle_theme(self):
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    # -------------------------------------------------------------------------
    # Left Column: Tabs (Input PDFs & Settings)
    # -------------------------------------------------------------------------
    def _build_left_column(self):
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=12, fg_color=self.COLOR_CARD_DARK)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.tab_files = self.tabview.add("📑 Lecture PDFs")
        self.tab_settings = self.tabview.add("⚙️ Settings & API")

        self._build_files_tab()
        self._build_settings_tab()

    def _build_files_tab(self):
        parent = self.tab_files

        # Top Control Bar
        ctrl_bar = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl_bar.pack(fill="x", padx=10, pady=(10, 5))

        self.add_btn = ctk.CTkButton(
            ctrl_bar,
            text="➕ Add PDF Files",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_TEAL,
            hover_color=self.COLOR_TEAL_HOVER,
            command=self._choose_pdfs
        )
        self.add_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            ctrl_bar,
            text="🗑️ Clear All",
            font=ctk.CTkFont(size=12),
            fg_color="#475569",
            hover_color="#64748B",
            width=80,
            command=self._clear_pdfs
        )
        self.clear_btn.pack(side="left")

        self.file_count_lbl = ctk.CTkLabel(
            ctrl_bar,
            text=f"0 / {Config.MAX_PDF_LIMIT} files",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94A3B8"
        )
        self.file_count_lbl.pack(side="right")

        # Scrollable List for Selected PDFs
        self.files_scroll_frame = ctk.CTkScrollableFrame(
            parent,
            corner_radius=8,
            fg_color="#0F172A",
            border_width=1,
            border_color=self.COLOR_BORDER
        )
        self.files_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder label when no files selected
        self.no_files_lbl = ctk.CTkLabel(
            self.files_scroll_frame,
            text="No PDF files selected.\n\nClick '➕ Add PDF Files' to select 1 to 5 lecture slide PDFs.",
            font=ctk.CTkFont(size=13),
            text_color="#64748B",
            justify="center"
        )
        self.no_files_lbl.pack(expand=True, pady=60)

    def _build_settings_tab(self):
        parent = self.tab_settings

        scroll_settings = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_settings.pack(fill="both", expand=True, padx=5, pady=5)

        # 1. Gemini API Key
        lbl_api = ctk.CTkLabel(scroll_settings, text="Google Gemini API Key:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_api.pack(anchor="w", padx=5, pady=(5, 2))

        api_frame = ctk.CTkFrame(scroll_settings, fg_color="transparent")
        api_frame.pack(fill="x", padx=5, pady=(0, 10))

        self.api_key_entry = ctk.CTkEntry(
            api_frame,
            placeholder_text="Enter AI Studio API Key (AIzaSy...)",
            show="•",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        if Config.GEMINI_API_KEY:
            self.api_key_entry.insert(0, Config.GEMINI_API_KEY)

        self.api_toggle_btn = ctk.CTkButton(
            api_frame,
            text="👁️",
            width=36,
            fg_color="#334155",
            hover_color="#475569",
            command=self._toggle_api_visibility
        )
        self.api_toggle_btn.pack(side="right")

        # 2. Gemini Model Selection
        lbl_model = ctk.CTkLabel(scroll_settings, text="Gemini AI Model:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_model.pack(anchor="w", padx=5, pady=(5, 2))

        models = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-flash-latest"
        ]
        self.model_combo = ctk.CTkOptionMenu(
            scroll_settings,
            values=models,
            font=ctk.CTkFont(size=12)
        )
        self.model_combo.pack(fill="x", padx=5, pady=(0, 10))
        if Config.GEMINI_MODEL in models:
            self.model_combo.set(Config.GEMINI_MODEL)
        else:
            self.model_combo.set("gemini-2.0-flash")

        # 3. OCR Resolution Scale
        ocr_head = ctk.CTkFrame(scroll_settings, fg_color="transparent")
        ocr_head.pack(fill="x", padx=5, pady=(5, 2))
        lbl_ocr = ctk.CTkLabel(ocr_head, text="Windows OCR Resolution Scale:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_ocr.pack(side="left")

        self.ocr_val_lbl = ctk.CTkLabel(
            ocr_head,
            text=f"{Config.OCR_SCALE:.1f}x",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.ocr_val_lbl.pack(side="right")

        self.ocr_slider = ctk.CTkSlider(
            scroll_settings,
            from_=1.0,
            to=3.0,
            number_of_steps=20,
            command=lambda val: self.ocr_val_lbl.configure(text=f"{val:.1f}x")
        )
        self.ocr_slider.set(Config.OCR_SCALE)
        self.ocr_slider.pack(fill="x", padx=5, pady=(0, 10))

        # 4. Course Header (Solves hardcoded header problem)
        lbl_course = ctk.CTkLabel(scroll_settings, text="Word Document Header Title:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_course.pack(anchor="w", padx=5, pady=(5, 2))

        self.course_entry = ctk.CTkEntry(scroll_settings, font=ctk.CTkFont(size=11))
        self.course_entry.insert(0, Config.COURSE_HEADER)
        self.course_entry.pack(fill="x", padx=5, pady=(0, 10))

        # 5. Custom Output File Name
        lbl_outname = ctk.CTkLabel(scroll_settings, text="Custom Output Name (Optional):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_outname.pack(anchor="w", padx=5, pady=(5, 2))

        self.output_name_entry = ctk.CTkEntry(
            scroll_settings,
            placeholder_text="e.g. Python_Data_Structures_Guide",
            font=ctk.CTkFont(size=11)
        )
        self.output_name_entry.pack(fill="x", padx=5, pady=(0, 10))

        # 6. Output Directory
        lbl_outdir = ctk.CTkLabel(scroll_settings, text="Output Directory:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_outdir.pack(anchor="w", padx=5, pady=(5, 2))

        dir_frame = ctk.CTkFrame(scroll_settings, fg_color="transparent")
        dir_frame.pack(fill="x", padx=5, pady=(0, 15))

        self.out_dir_entry = ctk.CTkEntry(dir_frame, font=ctk.CTkFont(size=11))
        self.out_dir_entry.insert(0, str(Config.OUTPUT_DIR))
        self.out_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_dir_btn = ctk.CTkButton(
            dir_frame,
            text="📁",
            width=36,
            fg_color="#334155",
            hover_color="#475569",
            command=self._choose_output_dir
        )
        browse_dir_btn.pack(side="right")

        # Save Settings to .env Button
        save_btn = ctk.CTkButton(
            scroll_settings,
            text="💾 Save Settings to .env",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0F766E",
            hover_color="#115E59",
            command=self._save_settings
        )
        save_btn.pack(fill="x", padx=5, pady=(5, 10))

    def _toggle_api_visibility(self):
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.api_key_entry.configure(show="")
            self.api_toggle_btn.configure(text="🔒")
        else:
            self.api_key_entry.configure(show="•")
            self.api_toggle_btn.configure(text="👁️")

    def _choose_output_dir(self):
        folder = filedialog.askdirectory(initialdir=str(Config.OUTPUT_DIR), title="Select Output Directory")
        if folder:
            self.out_dir_entry.delete(0, "end")
            self.out_dir_entry.insert(0, folder)

    def _save_settings(self):
        api_key = self.api_key_entry.get().strip()
        model = self.model_combo.get().strip()
        ocr_val = round(self.ocr_slider.get(), 1)
        course_h = self.course_entry.get().strip()
        out_dir = self.out_dir_entry.get().strip()

        updates = {
            "GEMINI_API_KEY": api_key,
            "GEMINI_MODEL": model,
            "OCR_SCALE": str(ocr_val),
            "COURSE_HEADER": course_h,
            "OUTPUT_DIR": out_dir
        }
        try:
            Config.save_to_env(updates)
            messagebox.showinfo("Settings Saved", "Preferences have been successfully saved to your .env file!")
            self._append_log("[GUI] Settings saved to .env and active configuration reloaded.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")

    # -------------------------------------------------------------------------
    # PDF Files List Operations
    # -------------------------------------------------------------------------
    def _choose_pdfs(self):
        if len(self.selected_pdfs) >= Config.MAX_PDF_LIMIT:
            messagebox.showwarning(
                "Limit Reached",
                f"You have already selected the maximum limit of {Config.MAX_PDF_LIMIT} PDF files."
            )
            return

        files = filedialog.askopenfilenames(
            title=f"Select up to {Config.MAX_PDF_LIMIT} Lecture PDF Files",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if not files:
            return

        added_count = 0
        for f in files:
            norm = str(Path(f).resolve())
            if norm not in self.selected_pdfs:
                if len(self.selected_pdfs) < Config.MAX_PDF_LIMIT:
                    self.selected_pdfs.append(norm)
                    added_count += 1
                else:
                    messagebox.showinfo(
                        "Max Limit Reached",
                        f"Limited to first {Config.MAX_PDF_LIMIT} files."
                    )
                    break

        if added_count > 0:
            self._refresh_file_list()

    def _clear_pdfs(self):
        self.selected_pdfs.clear()
        self._refresh_file_list()

    def _remove_pdf(self, path: str):
        if path in self.selected_pdfs:
            self.selected_pdfs.remove(path)
            self._refresh_file_list()

    def _move_pdf_up(self, index: int):
        if index > 0:
            self.selected_pdfs[index], self.selected_pdfs[index - 1] = (
                self.selected_pdfs[index - 1],
                self.selected_pdfs[index],
            )
            self._refresh_file_list()

    def _move_pdf_down(self, index: int):
        if index < len(self.selected_pdfs) - 1:
            self.selected_pdfs[index], self.selected_pdfs[index + 1] = (
                self.selected_pdfs[index + 1],
                self.selected_pdfs[index],
            )
            self._refresh_file_list()

    def _refresh_file_list(self):
        # Clear existing widgets
        for widget in self.files_scroll_frame.winfo_children():
            widget.destroy()

        count = len(self.selected_pdfs)
        self.file_count_lbl.configure(text=f"{count} / {Config.MAX_PDF_LIMIT} files")

        if not self.selected_pdfs:
            self.no_files_lbl = ctk.CTkLabel(
                self.files_scroll_frame,
                text="No PDF files selected.\n\nClick '➕ Add PDF Files' to select 1 to 5 lecture slide PDFs.",
                font=ctk.CTkFont(size=13),
                text_color="#64748B",
                justify="center"
            )
            self.no_files_lbl.pack(expand=True, pady=60)
            return

        for idx, pdf_path in enumerate(self.selected_pdfs):
            p = Path(pdf_path)
            size_mb = p.stat().st_size / (1024 * 1024) if p.exists() else 0

            # Quick page count
            pages_str = "? pages"
            try:
                doc = pymupdf.open(str(p))
                pages_str = f"{len(doc)} pages"
                doc.close()
            except Exception:
                pass

            # Card Container
            card = ctk.CTkFrame(
                self.files_scroll_frame,
                fg_color="#1E293B",
                corner_radius=8,
                border_width=1,
                border_color=self.COLOR_BORDER
            )
            card.pack(fill="x", pady=4, padx=2)

            # Sequence Badge
            seq_lbl = ctk.CTkLabel(
                card,
                text=f"#{idx + 1}",
                width=30,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#38BDF8"
            )
            seq_lbl.pack(side="left", padx=(8, 4))

            # File Info (Name + Meta)
            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, padx=4, pady=6)

            name_lbl = ctk.CTkLabel(
                info_box,
                text=p.name,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            name_lbl.pack(anchor="w")

            meta_lbl = ctk.CTkLabel(
                info_box,
                text=f"{pages_str}  •  {size_mb:.2f} MB",
                font=ctk.CTkFont(size=10),
                text_color="#94A3B8",
                anchor="w"
            )
            meta_lbl.pack(anchor="w")

            # Action Buttons: Up, Down, Delete
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=6)

            if idx > 0:
                up_btn = ctk.CTkButton(
                    btn_box,
                    text="▲",
                    width=26,
                    height=24,
                    font=ctk.CTkFont(size=10),
                    fg_color="#334155",
                    hover_color="#475569",
                    command=lambda i=idx: self._move_pdf_up(i)
                )
                up_btn.pack(side="left", padx=1)

            if idx < count - 1:
                down_btn = ctk.CTkButton(
                    btn_box,
                    text="▼",
                    width=26,
                    height=24,
                    font=ctk.CTkFont(size=10),
                    fg_color="#334155",
                    hover_color="#475569",
                    command=lambda i=idx: self._move_pdf_down(i)
                )
                down_btn.pack(side="left", padx=1)

            del_btn = ctk.CTkButton(
                btn_box,
                text="✕",
                width=26,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color="#7F1D1D",
                hover_color="#991B1B",
                command=lambda p_str=pdf_path: self._remove_pdf(p_str)
            )
            del_btn.pack(side="left", padx=(1, 4))

    # -------------------------------------------------------------------------
    # Right Column: Action, Progress, and Live Console
    # -------------------------------------------------------------------------
    def _build_right_column(self):
        col_frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_CARD_DARK)
        col_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        col_frame.grid_columnconfigure(0, weight=1)
        col_frame.grid_rowconfigure(2, weight=1)

        # 1. Action Card
        act_card = ctk.CTkFrame(col_frame, fg_color="transparent")
        act_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        act_card.grid_columnconfigure(0, weight=1)

        self.generate_btn = ctk.CTkButton(
            act_card,
            text="🚀 Generate Study Guide (.docx)",
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.COLOR_TEAL,
            hover_color=self.COLOR_TEAL_HOVER,
            command=self._start_generation
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew")

        # 2. Progress Card
        prog_card = ctk.CTkFrame(col_frame, fg_color="#0F172A", corner_radius=8, border_width=1, border_color=self.COLOR_BORDER)
        prog_card.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        prog_card.grid_columnconfigure(0, weight=1)

        prog_head = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_head.pack(fill="x", padx=10, pady=(8, 2))

        self.status_lbl = ctk.CTkLabel(
            prog_head,
            text="Ready to process",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC",
            anchor="w"
        )
        self.status_lbl.pack(side="left")

        self.pct_lbl = ctk.CTkLabel(
            prog_head,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        )
        self.pct_lbl.pack(side="right")

        self.prog_bar = ctk.CTkProgressBar(
            prog_card,
            height=10,
            progress_color=self.COLOR_TEAL,
            fg_color="#334155"
        )
        self.prog_bar.set(0.0)
        self.prog_bar.pack(fill="x", padx=10, pady=(2, 10))

        # 3. Live Activity Console Card
        console_card = ctk.CTkFrame(col_frame, fg_color="transparent")
        console_card.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 10))
        console_card.grid_columnconfigure(0, weight=1)
        console_card.grid_rowconfigure(1, weight=1)

        con_header = ctk.CTkFrame(console_card, fg_color="transparent")
        con_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        lbl_console = ctk.CTkLabel(
            con_header,
            text="📜 Live Activity Console",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94A3B8"
        )
        lbl_console.pack(side="left")

        clear_con_btn = ctk.CTkButton(
            con_header,
            text="Clear",
            width=50,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_console
        )
        clear_con_btn.pack(side="right")

        self.console_text = ctk.CTkTextbox(
            console_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#0F172A",
            text_color="#E2E8F0",
            border_width=1,
            border_color=self.COLOR_BORDER,
            corner_radius=8,
            wrap="word"
        )
        self.console_text.grid(row=1, column=0, sticky="nsew")

        # 4. Result Action Card
        self.result_card = ctk.CTkFrame(col_frame, fg_color="transparent")
        self.result_card.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.result_card.grid_columnconfigure(0, weight=1)
        self.result_card.grid_columnconfigure(1, weight=1)

        self.open_doc_btn = ctk.CTkButton(
            self.result_card,
            text="📄 Open in Word (.docx)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            state="disabled",
            command=self._open_word_doc
        )
        self.open_doc_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.open_dir_btn = ctk.CTkButton(
            self.result_card,
            text="📁 Open Output Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569",
            hover_color="#64748B",
            state="disabled",
            command=self._open_output_folder
        )
        self.open_dir_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _clear_console(self):
        self.console_text.delete("1.0", "end")

    def _append_log(self, text: str):
        if not text.endswith("\n"):
            text += "\n"
        self.console_text.insert("end", text)
        self.console_text.see("end")

    def _append_log_threadsafe(self, text: str):
        self.after(0, lambda: self._append_log(text))

    def _update_progress(self, status: str, pct: float):
        def _apply():
            self.status_lbl.configure(text=status)
            self.pct_lbl.configure(text=f"{int(pct * 100)}%")
            self.prog_bar.set(pct)
            self._append_log(f"[{int(pct * 100):02d}%] {status}")
        self.after(0, _apply)

    # -------------------------------------------------------------------------
    # Pipeline Execution Thread
    # -------------------------------------------------------------------------
    def _start_generation(self):
        if self.is_processing:
            return

        if not self.selected_pdfs:
            messagebox.showwarning("No Files", "Please add at least one PDF file before generating.")
            return

        # Disable interactive buttons during processing
        self.is_processing = True
        self.generate_btn.configure(text="⏳ Processing Study Guide...", state="disabled", fg_color="#334155")
        self.add_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.open_doc_btn.configure(state="disabled")
        self.open_dir_btn.configure(state="disabled")
        self.prog_bar.set(0.0)
        self.pct_lbl.configure(text="0%")
        self.status_lbl.configure(text="Starting pipeline...")

        # Read config inputs
        api_key = self.api_key_entry.get().strip()
        model_name = self.model_combo.get().strip()
        ocr_scale = round(self.ocr_slider.get(), 1)
        course_header = self.course_entry.get().strip() or Config.COURSE_HEADER
        custom_name = self.output_name_entry.get().strip() or None
        output_dir_str = self.out_dir_entry.get().strip()
        output_dir = Path(output_dir_str) if output_dir_str else Config.OUTPUT_DIR

        # Launch Worker Thread
        thread = threading.Thread(
            target=self._run_pipeline_worker,
            args=(self.selected_pdfs.copy(), api_key, model_name, ocr_scale, course_header, custom_name, output_dir),
            daemon=True
        )
        thread.start()

    def _run_pipeline_worker(self, pdf_paths, api_key, model_name, ocr_scale, course_header, custom_name, output_dir):
        try:
            self._update_progress("Initializing configuration...", 0.03)

            # Step 1: Extraction Phase
            extractor = SmartExtractor(scale=ocr_scale)
            extraction_results = extractor.extract(
                pdf_paths,
                callback=lambda msg, pct: self._update_progress(msg, pct)
            )

            # Step 2: Synthesis Phase
            synthesizer = AISynthesizer(api_key=api_key, model_name=model_name)
            synthesized_markdown = synthesizer.synthesize(
                extraction_results,
                callback=lambda msg, pct: self._update_progress(msg, pct)
            )

            # Step 3: Document Generation Phase
            doc_builder = DocumentBuilder(output_dir=output_dir)
            if not custom_name:
                first_stem = Path(pdf_paths[0]).stem
                custom_name = f"Combined_Lecture_Notes_{first_stem}"

            output_files = doc_builder.build_document(
                markdown_text=synthesized_markdown,
                base_filename=custom_name,
                course_header=course_header,
                callback=lambda msg, pct: self._update_progress(msg, pct)
            )

            self.last_generated_docx = output_files["docx_path"]
            self.last_generated_doc = output_files["doc_path"]

            self.after(0, self._on_generation_success)

        except Exception as e:
            self.after(0, lambda: self._on_generation_error(str(e)))

    def _on_generation_success(self):
        self.is_processing = False
        self.generate_btn.configure(
            text="🚀 Generate Study Guide (.docx)",
            state="normal",
            fg_color=self.COLOR_TEAL
        )
        self.add_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")
        self.open_doc_btn.configure(state="normal")
        self.open_dir_btn.configure(state="normal")

        self.status_lbl.configure(text="Study Guide Generated Successfully!")
        self.pct_lbl.configure(text="100%")
        self.prog_bar.set(1.0)

        docx_name = os.path.basename(self.last_generated_docx) if self.last_generated_docx else "Document"
        messagebox.showinfo(
            "Success!",
            f"Study guide generated successfully!\n\nSaved as:\n{docx_name}\n\nClick 'Open in Word' to review your document."
        )

    def _on_generation_error(self, err_msg: str):
        self.is_processing = False
        self.generate_btn.configure(
            text="🚀 Generate Study Guide (.docx)",
            state="normal",
            fg_color=self.COLOR_TEAL
        )
        self.add_btn.configure(state="normal")
        self.clear_btn.configure(state="normal")

        self.status_lbl.configure(text=f"Error occurred: {err_msg[:40]}...")
        self._append_log(f"\n[ERROR] {err_msg}")
        messagebox.showerror("Pipeline Error", f"An error occurred during generation:\n\n{err_msg}")

    # -------------------------------------------------------------------------
    # Result Actions
    # -------------------------------------------------------------------------
    def _open_word_doc(self):
        if self.last_generated_docx and os.path.exists(self.last_generated_docx):
            try:
                os.startfile(self.last_generated_docx)
            except Exception as e:
                messagebox.showerror("Open Error", f"Could not open file: {e}")
        else:
            messagebox.showwarning("File Missing", "Generated Word document could not be found.")

    def _open_output_folder(self):
        out_dir = self.out_dir_entry.get().strip() or str(Config.OUTPUT_DIR)
        if os.path.exists(out_dir):
            try:
                os.startfile(out_dir)
            except Exception as e:
                messagebox.showerror("Folder Error", f"Could not open directory: {e}")
        else:
            messagebox.showwarning("Directory Missing", f"Directory does not exist: {out_dir}")

def launch_gui():
    """Entry point for the GUI application."""
    app = LectureDocGeneratorGUI()
    app.mainloop()

if __name__ == "__main__":
    launch_gui()
