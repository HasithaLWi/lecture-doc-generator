import os
import re
from typing import List, Dict, Any
from .config import Config

class AISynthesizer:
    """
    Transforms raw extracted PDF/OCR slide text into structured,
    comprehensive, and pedagogically sound lecture notes using Google Gemini.
    """

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = (api_key or Config.GEMINI_API_KEY or "").strip().strip("'\"")
        self.model_name = (model_name or Config.GEMINI_MODEL or "gemini-2.0-flash").strip()
        self.client = None

        if self.api_key and len(self.api_key) > 10:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Synthesizer Warning] Failed to initialize google-genai client: {e}")

    def synthesize(self, extraction_results: List[Dict[str, Any]], custom_prompt_instructions: str = "", callback=None) -> str:
        """
        Synthesizes the extracted content into complete master lecture notes.
        Processes each document with high depth to prevent token budget truncation,
        then stitches them into a unified master study guide.
        """
        if not extraction_results:
            empty_msg = "# Combined Master Lecture Notes\n\n*No lecture slide content was provided for synthesis.*"
            if callback:
                callback("[Synthesizer] No content to synthesize.", 1.0)
            return empty_msg

        if not self.client:
            msg = "[Synthesizer] No Gemini API key detected. Using built-in rule-based organizer..."
            print(f"\n{msg}")
            if callback:
                callback(msg, 0.5)
            result = self._fallback_organizer(extraction_results)
            if callback:
                callback("[Synthesizer] Offline organization complete.", 0.75)
            return result

        total_docs = len(extraction_results)
        msg_start = f"[Synthesizer] Synthesizing {total_docs} document(s) using Gemini ({self.model_name})..."
        print(f"\n{msg_start}")
        if callback:
            callback(msg_start, 0.35)

        synthesized_chapters = []
        for idx, doc in enumerate(extraction_results, start=1):
            # Assemble slides text for this document
            doc_lines = []
            for p in doc.get("pages", []):
                text = p.get("text", "").strip()
                if text:
                    doc_lines.append(f"--- [Slide {p['page_number']:02d}] ---\n{text}\n")
            doc_raw_text = "\n".join(doc_lines)

            if not doc_raw_text.strip():
                skip_msg = f"  • Doc {idx}/{total_docs}: '{doc.get('file_name', 'Unknown')}' has no extracted content. Skipping."
                print(skip_msg)
                if callback:
                    callback(skip_msg, 0.35 + (idx / total_docs) * 0.4)
                continue

            doc_status = f"  • Doc {idx}/{total_docs}: Synthesizing '{doc.get('file_name', 'Document')}' ({len(doc_raw_text)} chars)..."
            print(doc_status)
            if callback:
                callback(doc_status, 0.35 + ((idx - 0.5) / total_docs) * 0.4)

            chapter_md = self._call_gemini_for_document(
                doc_name=doc.get("file_name", f"Document_{idx}"),
                doc_index=idx,
                total_docs=total_docs,
                raw_text=doc_raw_text,
                custom_instructions=custom_prompt_instructions
            )

            # Ensure chapter_md is a valid string before adding
            if isinstance(chapter_md, str) and chapter_md.strip():
                synthesized_chapters.append(chapter_md.strip())
            else:
                fallback_md = self._local_markdown_fallback(doc.get("file_name", f"Doc_{idx}"), doc_raw_text)
                synthesized_chapters.append(fallback_md)

            if callback:
                callback(f"  ✓ Finished synthesizing '{doc.get('file_name', '')}'", 0.35 + (idx / total_docs) * 0.4)

        if not synthesized_chapters:
            return self._fallback_organizer(extraction_results)

        # Assemble into Master Document
        master_doc = "\n\n---\n\n".join(synthesized_chapters)
        done_msg = "[Synthesizer] Synthesis complete! All lecture materials unified."
        print(done_msg)
        if callback:
            callback(done_msg, 0.75)
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
            "3. EXPAND AND EXPLAIN: Explain WHY code works, technical concepts, underlying architecture, time complexities, and best practices.\n"
            "4. BEAUTIFUL CODE & DIAGRAM BLOCKS: Format code snippets in appropriate fenced code blocks with the exact language identifier (e.g., ```python, ```java, ```c, ```cpp, ```sql, ```bash, ```html, ```json). For architecture flows, network models, ASCII diagrams, packet structures, or conceptual illustrations, use ```text or ```diagram (or plain ```) so they are clearly distinguished from executable programming code.\n"
            "5. COMPARISON TABLES: Build comprehensive Markdown tables comparing operations, complexities, syntax, and properties (e.g., Lists vs Tuples vs Sets vs Dictionaries).\n"
            "6. PEDAGOGICAL CALLOUTS: Include '> [!NOTE]', '> [!TIP]', and '> [!IMPORTANT]' boxes for crucial exam tips and common pitfalls.\n"
            "7. STRUCTURE: Begin with '# Chapter " + str(doc_index) + ": <Topic Title>', followed by structured '## Section', '### Subsection', bullet points, code blocks, and tables.\n"
            "8. DO NOT wrap the whole chapter in an outer ```markdown code fence. Output pure markdown directly."
        )

        user_prompt = f"""SOURCE FILE: {doc_name} (Document {doc_index} of {total_docs})

{custom_instructions}

==================================================
RAW EXTRACTED SLIDE CONTENT:
==================================================
{raw_text}
"""
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=8192
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )

            raw_response_text = getattr(response, "text", None)
            if not raw_response_text or not raw_response_text.strip():
                raise ValueError("Gemini returned an empty response or candidate content was blocked.")

            clean_text = raw_response_text.strip()
            # Strip accidental outer markdown code block wrapping
            if clean_text.startswith("```markdown"):
                clean_text = clean_text[len("```markdown"):].strip()
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3].strip()
            elif clean_text.startswith("```md"):
                clean_text = clean_text[len("```md"):].strip()
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3].strip()

            return clean_text

        except Exception as e:
            print(f"[Synthesizer Error] Gemini API call failed for {doc_name}: {e}")
            print("[Synthesizer] Falling back to structured local notes for this document...")
            return self._local_markdown_fallback(doc_name, raw_text)

    def _fallback_organizer(self, extraction_results: List[Dict[str, Any]]) -> str:
        """Local fallback organizer when no Gemini API key is configured with grouped code blocks."""
        md_lines = [
            "# Combined Master Lecture Notes",
            "\n*Generated via Lecture Document Generator (Local Extraction Mode)*\n"
        ]

        code_keywords = ("def ", "class ", "print(", "import ", "from ", "for ", "while ", "if ", "elif ", "else:", "try:", "except ", "with ", "return ", "lambda ")

        for doc_idx, doc in enumerate(extraction_results, start=1):
            clean_title = doc.get("file_name", f"Document {doc_idx}").replace(".pdf", "")
            md_lines.append(f"\n# Chapter {doc_idx}: {clean_title}\n")

            for page in doc.get("pages", []):
                text = page.get("text", "").strip()
                if not text:
                    continue

                lines = [l.rstrip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                first_line = lines[0]
                md_lines.append(f"\n## Slide {page['page_number']:02d}: {first_line}\n")

                in_code = False
                code_buf = []

                for line in lines[1:]:
                    s = line.strip()
                    is_code_line = (
                        any(s.startswith(kw) for kw in code_keywords)
                        or (line.startswith("    ") or line.startswith("\t"))
                        or ("=" in s and not s.startswith("-") and not s.startswith("*") and len(s.split("=")[0].strip()) < 30)
                        or s.startswith("#")
                    )

                    if is_code_line:
                        in_code = True
                        code_buf.append(line)
                    else:
                        if in_code and code_buf:
                            md_lines.append("```\n" + "\n".join(code_buf) + "\n```")
                            in_code = False
                            code_buf = []
                        md_lines.append(f"- {s}")

                if in_code and code_buf:
                    md_lines.append("```\n" + "\n".join(code_buf) + "\n```")

        return "\n".join(md_lines)

    def _local_markdown_fallback(self, doc_name: str, raw_text: str) -> str:
        """Formats raw slide text into clean Markdown when a specific document call fails."""
        clean_name = doc_name.replace(".pdf", "")
        lines = raw_text.split("\n")
        out = [f"# Lecture Notes: {clean_name}\n"]

        code_buf = []
        in_code = False

        for raw in lines:
            s = raw.strip()
            if not s:
                continue

            if s.startswith("--- [Slide") and s.endswith("]---"):
                if in_code and code_buf:
                    out.append("```\n" + "\n".join(code_buf) + "\n```")
                    in_code = False
                    code_buf = []
                out.append(f"\n## {s.strip('- []')}\n")
                continue

            is_code = (
                any(s.startswith(kw) for kw in ("def ", "class ", "print(", "import ", "for ", "while ", "if ", "with "))
                or raw.startswith("    ")
                or raw.startswith("\t")
            )
            if is_code:
                in_code = True
                code_buf.append(raw)
            else:
                if in_code and code_buf:
                    out.append("```\n" + "\n".join(code_buf) + "\n```")
                    in_code = False
                    code_buf = []
                out.append(f"- {s}")

        if in_code and code_buf:
            out.append("```\n" + "\n".join(code_buf) + "\n```")

        return "\n".join(out)
