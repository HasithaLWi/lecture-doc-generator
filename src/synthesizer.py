import os
from typing import List, Dict, Any
from .config import Config

class AISynthesizer:
    """
    Transforms raw extracted PDF/OCR slide text into structured,
    comprehensive, and pedagogically sound lecture notes using Google Gemini.
    """

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model_name or Config.GEMINI_MODEL
        self.client = None

        if self.api_key and len(self.api_key) > 10:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Synthesizer Warning] Failed to initialize google-genai: {e}")

    def synthesize(self, extraction_results: List[Dict[str, Any]], custom_prompt_instructions: str = "") -> str:
        """
        Synthesizes the extracted content into complete master lecture notes.
        Processes each document with high depth to prevent token budget truncation,
        then stitches them into a unified master study guide.
        """
        if not self.client:
            print("\n[Synthesizer] No Gemini API key detected. Using built-in rule-based organizer...")
            return self._fallback_organizer(extraction_results)

        total_docs = len(extraction_results)
        print(f"\n[Synthesizer] Synthesizing {total_docs} document(s) using Gemini ({self.model_name})...")

        synthesized_chapters = []
        for idx, doc in enumerate(extraction_results, start=1):
            # Assemble slides text for this document
            doc_lines = []
            for p in doc["pages"]:
                if p["text"].strip():
                    doc_lines.append(f"--- [Slide {p['page_number']:02d}] ---\n{p['text']}\n")
            doc_raw_text = "\n".join(doc_lines)

            if not doc_raw_text.strip():
                print(f"  • Doc {idx}/{total_docs}: '{doc['file_name']}' has no extracted content. Skipping.")
                continue

            print(f"  • Doc {idx}/{total_docs}: Synthesizing '{doc['file_name']}' ({len(doc_raw_text)} chars)...")
            chapter_md = self._call_gemini_for_document(
                doc_name=doc["file_name"],
                doc_index=idx,
                total_docs=total_docs,
                raw_text=doc_raw_text,
                custom_instructions=custom_prompt_instructions
            )
            synthesized_chapters.append(chapter_md)

        # Assemble into Master Document
        master_doc = "\n\n---\n\n".join(synthesized_chapters)
        print("[Synthesizer] Synthesis complete! All lecture materials unified.")
        return master_doc

    def _call_gemini_for_document(self, doc_name: str, doc_index: int, total_docs: int, raw_text: str, custom_instructions: str) -> str:
        """Calls Google Gemini API for an individual document for maximum fidelity and completeness."""
        system_instruction = (
            "You are an expert university Computer Science professor and technical curriculum author. "
            "You are creating a comprehensive, textbook-grade lecture notes chapter based on raw lecture slides (including local OCR output).\n\n"
            "MANDATORY REQUIREMENTS FOR HIGHEST ACCURACY:\n"
            "1. NO INFORMATION LOSS: Retain every single topic, subtopic, rule, method, operator, and code pattern from the slides. Never summarize or omit code examples.\n"
            "2. INTELLIGENT OCR ERROR CORRECTION: Fix slide OCR mistakes and formatting artifacts:\n"
            "   - Fix variable names and identifiers (e.g. 'my _ list' -> 'my_list', 'tuple _ 1' -> 'tuple_1', 'set 1' -> 'set_1').\n"
            "   - Fix function calls (e.g. 'print (ten (sports))' -> 'print(len(sports))', 'print (id (my _ list))' -> 'print(id(my_list))').\n"
            "   - Fix indices (e.g. '[O]' -> '[0]').\n"
            "   - Fix assignments (e.g. 'my_list - 10' -> 'my_list[0] = 10', 'my list ' -> 'my_list =').\n"
            "3. EXPAND AND EXPLAIN: Explain WHY code works, memory models (e.g., mutability vs immutability, id() checks), time complexities, and best practices.\n"
            "4. BEAUTIFUL CODE BLOCKS: Format ALL code in ```python blocks with realistic comments, step-by-step traces, and '# Output: ...' comments.\n"
            "5. COMPARISON TABLES: Build comprehensive Markdown tables comparing operations, complexities, syntax, and properties (e.g., Lists vs Tuples vs Sets vs Dictionaries).\n"
            "6. PEDAGOGICAL CALLOUTS: Include '> [!NOTE]', '> [!TIP]', and '> [!IMPORTANT]' boxes for crucial exam tips and common pitfalls.\n"
            "7. STRUCTURE: Begin with '# Chapter " + str(doc_index) + ": <Topic Title>', followed by structured '## Section', '### Subsection', bullet points, code blocks, and tables."
        )

        prompt = f"""{system_instruction}

{custom_instructions}

SOURCE FILE: {doc_name} (Document {doc_index} of {total_docs})

==================================================
RAW EXTRACTED SLIDE CONTENT:
==================================================
{raw_text}
"""
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.2
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"[Synthesizer Error] Gemini API call failed for {doc_name}: {e}")
            print("[Synthesizer] Falling back to structured local notes for this document...")
            return self._local_markdown_fallback(doc_name, raw_text)

    def _fallback_organizer(self, extraction_results: List[Dict[str, Any]]) -> str:
        """Local fallback organizer when no Gemini API key is configured."""
        md_lines = [
            "# Combined Master Lecture Notes",
            "\n*Generated via Lecture Document Generator (Local Extraction Mode)*\n"
        ]

        for doc_idx, doc in enumerate(extraction_results, start=1):
            md_lines.append(f"\n# Chapter {doc_idx}: {doc['file_name'].replace('.pdf', '')}\n")
            for page in doc["pages"]:
                if not page["text"].strip():
                    continue
                lines = page["text"].split("\n")
                first_line = lines[0] if lines else f"Page {page['page_number']}"
                md_lines.append(f"\n## Slide {page['page_number']:02d}: {first_line}\n")
                for line in lines[1:]:
                    if any(line.startswith(kw) for kw in ["def ", "class ", "print(", "import ", "for ", "while "]):
                        md_lines.append(f"```python\n{line}\n```")
                    else:
                        md_lines.append(f"- {line}")

        return "\n".join(md_lines)

    def _local_markdown_fallback(self, doc_name: str, raw_text: str) -> str:
        return f"# Lecture Notes: {doc_name}\n\n{raw_text}"
