# 📚 Lecture Document Generator `v2.0` ➡️ 📝

[![GitHub Release](https://img.shields.io/github/v/release/HasithaLWi/lecture-doc-generator?color=0E8388&label=Latest%20Release%20(v2.1)&logo=windows)](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows)](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)

> **Transform university lecture slide PDFs (including image-based Canva & PowerPoint decks) into structured, textbook-grade Microsoft Word study guides (`.docx` & `.doc`).**

---

## 📥 Instant Download (Standalone Windows App)

No Python, command line, or environment setup needed! You can download and run the pre-built desktop application directly:

[![Download Release](https://img.shields.io/badge/Download-LectureDocGenerator.exe%20(v2.1)-0E8388?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)

1. **[Download `LectureDocGenerator.exe` from Releases](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)**.
2. **Double-click `LectureDocGenerator.exe`** to launch the Desktop Studio.
3. In the **⚙️ Settings & API** tab, paste your [Google Gemini API Key](https://aistudio.google.com/) and click **Save Settings to .env**.
4. In the **📂 Process Queue** tab, click **➕ Add PDF Files** (1 to 5 slide decks) and click **🚀 Start Generation**!

---

## 🌟 Key Features

### 🔍 1. Smart Hybrid Extractor (85%+ Token Savings)
* **Native Digital + Local High-Res OCR:** Automatically detects whether slide pages contain digital text or raster images. Image-heavy slides are processed locally via Windows Native OCR (`winocr`) at 2x resolution (`OCR_SCALE=2`).
* **Cost & Token Efficient:** Processing slide images on your computer locally eliminates expensive image-token uploads to Gemini, saving 80%–90% on API costs.
* **Intelligent Noise Filtering:** Strips repetitive lecturer credentials, watermarks, and footer noise (`BSc (Hons)`, `Maheesha Fernando`, etc.) while preserving 100% of slide titles, bullet points, and code snippets.

### 🧠 2. Deep AI Synthesis (Google Gemini)
* **Powered by Google Gemini:** Fully optimized for `gemini-3.5-flash`, `gemini-3.6-flash`, or `gemini-flash-latest` via the modern `google-genai` SDK.
* **Intelligent OCR Typo Rectification:** Automatically detects and repairs slide OCR artifacts (e.g., `print(ten(sports))` → `print(len(sports))`, `my _ list` → `my_list`, `[O]` → `[0]`).
* **Unabridged Depth:** Expands brief bullet points into comprehensive explanations, memory model breakdowns (e.g., mutability vs. immutability, `id()` checks), and practical analogies.
* **Offline Fallback:** If no API key is provided, the tool automatically activates its built-in rule-based organizer to format clean lecture notes without crashing.

### 🎨 3. Publication-Grade Word Document Styling
* **IDE-Style Code Blocks:** Dual-layer code cards with a dark slate header bar (`[PYTHON]`), crisp `#F8FAFC` editor background, Consolas monospace font (9.5pt), muted comments (`#64748B`), and a prominent **Teal accent bar** (`#0E8388`).
* **Color-Coded Callout Cards (Admonitions):** Multi-line styled alert boxes with dedicated pastel backgrounds and thick left borders:
  * 💡 **Pro Tip** (`#F0FDF4` bg, Emerald `#16A34A` border)
  * ⚠️ **Important Note** (`#FFFBEB` bg, Amber `#D97706` border)
  * 📌 **Key Takeaway** (`#EFF6FF` bg, Royal Blue `#2563EB` border)
  * 🎯 **Exam & Practice Concept** (`#FAF5FF` bg, Purple `#7C3AED` border)
* **Professional Tables:** Deep Navy (`#0F2C59`) header row with white bold text, alternating zebra rows (`#FFFFFF` and `#F8FAFC`), subtle borders (`#E2E8F0`), and generous cell padding.
* **Zero Markdown Artifacts:** Full native rendering of bold `**text**` and inline code `` `code` `` across all paragraphs, headings, bullet points, and table cells.

---

## 🏗️ Project Architecture

```
lecture_doc_generator/
│
├── .env.example              # Configuration template
├── .env                      # Active environment variables (API Key, Model, Limits)
├── .gitignore                # Excludes venv, .env, outputs, and cache
├── requirements.txt          # Package dependencies (includes CustomTkinter)
├── README.md                 # Complete documentation
├── gui.py                    # Modern Desktop GUI Studio runner
├── main.py                   # CLI entry point & pipeline coordinator
├── run.bat                   # Windows 1-click launcher (launches GUI by default)
├── run.py                    # Root Python runner
│
├── src/                      # Core Package
│   ├── __init__.py
│   ├── config.py             # Environment config loader (.env & dynamic updates)
│   ├── gui_app.py            # CustomTkinter Desktop Studio implementation
│   ├── extractor.py          # Hybrid native text + local OCR extraction
│   ├── synthesizer.py        # Gemini AI synthesis & error correction
│   ├── doc_builder.py        # Word document styling engine (.docx & .doc)
│   └── utils.py              # CLI/GUI input resolvers & file pickers
│
└── output/                   # Directory where generated Word documents are saved
```

---

## ⚙️ Configuration (`.env`)

Create or edit your `.env` file in the `lecture_doc_generator` directory (or use the built-in Settings panel in the Desktop GUI):

```ini
# ==============================================================================
# Lecture Document Generator - Configuration
# ==============================================================================

# 1. Google Gemini API Key (Get a free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# 2. Gemini Model 
GEMINI_MODEL=gemini-3.1-flash-lite

# 3. Maximum number of PDF inputs allowed per run (Default: 5)
MAX_PDF_LIMIT=5

# 4. OCR resolution scale (Default: 2 for crisp 2x resolution)
OCR_SCALE=2

# 5. Word Document Header Title (Customizable course or study guide title)
COURSE_HEADER=Comprehensive Lecture Study Guide  |  ITS 2122 – Python for Data Science & AI

# 6. Output directory for generated Word files
OUTPUT_DIR=output
```

---

## 🚀 How to Run

### run to Add virtual environment setup
```bash
python -m venv venv
```

### Method 1: Standalone Windows App (`.exe`) — Recommended
1. Download **[`LectureDocGenerator.exe`](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)** from the [Releases page](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest).
2. Double-click the file to start. No Python installation required!

### Method 2: One-Click Script Launcher (`run.bat`)
Double-click **`run.bat`** in the repository root.
* Automatically creates a virtual environment (`venv`) if missing.
* Automatically installs any missing packages from `requirements.txt`.
* Launches the Desktop GUI Studio.

### Method 3: Via Python Terminal
```bash
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Desktop GUI
python gui.py

# (Or run in CLI mode)
python main.py "path/to/lecture1.pdf" "path/to/lecture2.pdf"
```

### Method 4: Recompile Standalone `.exe`
To rebuild the single-file executable from source:
```bash
.\build.bat
# or
python build_exe.py
```
The output file will be generated in `dist/LectureDocGenerator.exe`.

---

## 📄 Output Files

Generated documents are saved automatically in the `output/` directory:
* `output/Combined_Lecture_Notes_<Topic>.docx` (Modern Microsoft Word)
* `output/Combined_Lecture_Notes_<Topic>.doc` (Legacy Word Compatibility)

---

## 🛠️ Tech Stack & Dependencies

* **[CustomTkinter](https://customtkinter.tomschimansky.com/):** Modern dark/light responsive desktop graphical interface.
* **[PyMuPDF](https://pymupdf.readthedocs.io/):** High-speed PDF text and pixmap rasterization.
* **[winocr](https://github.com/winocr):** Hardware-accelerated local Windows OCR engine.
* **[Pillow (PIL)](https://python-pillow.org/):** Image processing and memory buffer conversion.
* **[google-genai](https://github.com/googleapis/python-genai):** Official Google Gemini Python SDK.
* **[python-docx](https://python-docx.readthedocs.io/):** Advanced Word document generation and styling.
* **[python-dotenv](https://github.com/theskumar/python-dotenv):** Secure environment variable management.
* **[PyInstaller](https://pyinstaller.org/):** Standalone single-file Windows executable packaging.

---

## 👤 Author & Maintainer

* **Author:** Hasitha Wijesinghe
* **Email:** [hasithawijesinghe2020@gmail.com](mailto:hasithawijesinghe2020@gmail.com)
* **GitHub:** [@HasithaLWi](https://github.com/HasithaLWi)
* **Repository:** [HasithaLWi/lecture-doc-generator](https://github.com/HasithaLWi/lecture-doc-generator)
* **Releases:** [Latest Release (v2.1)](https://github.com/HasithaLWi/lecture-doc-generator/releases/latest)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 **Hasitha Wijesinghe**. All rights reserved.
