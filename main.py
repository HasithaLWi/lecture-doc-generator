import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import Config
from src.extractor import SmartExtractor
from src.synthesizer import AISynthesizer
from src.doc_builder import DocumentBuilder
from src.utils import get_input_pdfs

def run_pipeline(pdf_paths: list = None, custom_output_name: str = None):
    """Executes the complete end-to-end PDF to Word Document pipeline."""
    Config.display_summary()

    # Step 1: Obtain PDF files
    if not pdf_paths:
        pdf_paths = get_input_pdfs()

    if not pdf_paths:
        print("\n[Error] No valid PDF files selected. Exiting.")
        return

    print(f"\n[Pipeline] Selected {len(pdf_paths)} PDF file(s) for processing:")
    for idx, p in enumerate(pdf_paths, start=1):
        print(f"  {idx}. {os.path.basename(p)}")

    # Step 2: Extraction Phase (Hybrid Digital + Local OCR)
    extractor = SmartExtractor()
    extraction_results = extractor.extract(pdf_paths)

    # Step 3: Synthesis Phase (Gemini API or Local Fallback)
    synthesizer = AISynthesizer()
    synthesized_markdown = synthesizer.synthesize(extraction_results)

    # Step 4: Document Generation Phase (.docx and .doc)
    doc_builder = DocumentBuilder()
    
    if not custom_output_name:
        first_stem = Path(pdf_paths[0]).stem
        custom_output_name = f"Combined_Lecture_Notes_{first_stem}"

    output_files = doc_builder.build_document(
        markdown_text=synthesized_markdown,
        base_filename=custom_output_name
    )

    print("\n" + "=" * 60)
    print(f" PIPELINE COMPLETED SUCCESSFULLY! [{Config.VERSION}]")
    print(f" Developed by {Config.AUTHOR} (GitHub: @HasithaLWi)")
    print("=" * 60)
    print(f"Generated Files:")
    print(f"  • Word Document (.docx): {output_files['docx_path']}")
    print(f"  • Word Document (.doc) : {output_files['doc_path']}")
    print("=" * 60)

    return output_files

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--version", "-v", "version", "--about", "--author", "-a"]:
        print("=" * 60)
        print(f"Lecture Document Generator {Config.VERSION}")
        print(f"Author : {Config.AUTHOR}")
        print(f"GitHub : {Config.GITHUB}")
        print("=" * 60)
        sys.exit(0)

    run_pipeline()
