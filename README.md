# 📚 Lecture Document Generator ➡️ 📝

> **Transform university lecture slide PDFs (including image-based Canva & PowerPoint decks) into structured, textbook-grade Microsoft Word study guides (`.docx` & `.doc`).**

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
├── requirements.txt          # Package dependencies
├── README.md                 # Complete documentation
├── main.py                   # Package entry point
├── run.bat                   # Windows 1-click launcher (auto-invokes local venv)
├── run.py                    # Root Python runner
│
├── src/                      # Core Package
│   ├── __init__.py
│   ├── config.py             # Environment config loader (.env)
│   ├── extractor.py          # Hybrid native text + local OCR extraction
│   ├── synthesizer.py        # Gemini AI synthesis & error correction
│   ├── doc_builder.py        # Word document styling engine (.docx & .doc)
│   └── utils.py              # GUI file selector dialog & CLI path resolver
│
└── output/                   # Directory where generated Word documents are saved
```

---

## ⚙️ Configuration (`.env`)

Create or edit your `.env` file in the `lecture_doc_generator` directory:

```ini
# ==============================================================================
# Lecture Document Generator - Configuration
# ==============================================================================

# 1. Google Gemini API Key (Get a free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# 2. Gemini Model (Recommended: gemini-3.5-flash or gemini-3.6-flash)
GEMINI_MODEL=gemini-3.5-flash

# 3. Maximum number of PDF inputs allowed per run (Default: 5)
MAX_PDF_LIMIT=5

# 4. OCR resolution scale (Default: 2 for crisp 2x resolution)
OCR_SCALE=2

# 5. Output directory for generated Word files
OUTPUT_DIR=output
```

---

## 🚀 How to Run

### Method 1: Windows One-Click (`run.bat`) — Easiest
Double-click **`run.bat`**. It automatically detects the self-contained virtual environment and launches the file picker dialog.

### Method 2: Interactive GUI File Picker
Run the script without arguments:
```bash
python run.py
```
A native Windows file selector dialog will appear, allowing you to select 1 to 5 lecture PDF files with your mouse.

### Method 3: Command-Line Arguments (CLI)
Pass up to 5 PDF files directly via terminal:
```bash
python run.py "path/to/lecture1.pdf" "path/to/lecture2.pdf"
```

### Method 4: Direct Package Execution
```bash
cd lecture_doc_generator
.\venv\Scripts\python.exe main.py
```

---

## 📄 Output Files

Generated documents are saved automatically in the `output/` directory:
* `output/Combined_Lecture_Notes_<Topic>.docx` (Modern Microsoft Word)
* `output/Combined_Lecture_Notes_<Topic>.doc` (Legacy Word Compatibility)

---

## 🛠️ Tech Stack & Dependencies

* **[PyMuPDF](https://pymupdf.readthedocs.io/):** High-speed PDF text and pixmap rasterization.
* **[winocr](https://github.com/winocr):** Hardware-accelerated local Windows OCR engine.
* **[Pillow (PIL)](https://python-pillow.org/):** Image processing and memory buffer conversion.
* **[google-genai](https://github.com/googleapis/python-genai):** Official Google Gemini Python SDK.
* **[python-docx](https://python-docx.readthedocs.io/):** Advanced Word document generation and styling.
* **[python-dotenv](https://github.com/theskumar/python-dotenv):** Secure environment variable management.

---

## 👤 Author & Maintainer

* **Author:** Hasitha Wijesinghe
* **Email:** [hasithawijesinghe2020@gmail.com](mailto:hasithawijesinghe2020@gmail.com)
* **GitHub:** [@HasithaLWi](https://github.com/HasithaLWi)
* **Repository:** [HasithaLWi/lecture-doc-generator](https://github.com/HasithaLWi/lecture-doc-generator)

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 **Hasitha Wijesinghe**. All rights reserved.


