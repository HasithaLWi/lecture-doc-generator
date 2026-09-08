import os
import re
import shutil
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from .config import Config

class DocumentBuilder:
    """
    Builds professional, textbook-grade Microsoft Word documents (.docx and .doc)
    with modern typography, IDE-style code blocks, color-coded callouts,
    and beautifully formatted tables.
    """

    # Color Palette Tokens
    COLOR_NAVY = RGBColor(15, 44, 89)        # #0F2C59 Primary Header
    COLOR_TEAL = RGBColor(14, 131, 136)      # #0E8388 Accent
    COLOR_DARK = RGBColor(30, 41, 59)        # #1E293B Body text
    COLOR_MUTED = RGBColor(100, 116, 139)    # #64748B Secondary / Comments
    COLOR_CODE = RGBColor(190, 24, 93)       # #BE185D Crimson code highlight
    COLOR_WHITE = RGBColor(255, 255, 255)

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _set_cell_background(self, cell, fill_hex: str):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def _set_cell_margins(self, cell, top=100, bottom=100, left=140, right=140):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'''
            <w:tcMar {nsdecls("w")}>
                <w:top w:w="{top}" w:type="dxa"/>
                <w:bottom w:w="{bottom}" w:type="dxa"/>
                <w:left w:w="{left}" w:type="dxa"/>
                <w:right w:w="{right}" w:type="dxa"/>
            </w:tcMar>
        ''')
        tcPr.append(tcMar)

    def _set_cell_borders(self, cell, **kwargs):
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
        for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            edge_data = kwargs.get(edge)
            if edge_data:
                b_element = parse_xml(
                    f'<w:{edge} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" '
                    f'w:sz="{edge_data.get("sz", "4")}" w:space="0" w:color="{edge_data.get("color", "E2E8F0")}"/>'
                )
                borders.append(b_element)
            else:
                borders.append(parse_xml(f'<w:{edge} {nsdecls("w")} w:val="none"/>'))
        tcPr.append(borders)

    def _add_inline_formatted_text(self, paragraph, text: str, default_font: str = "Segoe UI",
                                   default_size: Pt = Pt(10.5), default_color: RGBColor = None,
                                   is_header: bool = False):
        """
        Parses markdown bold (**text**), inline code (`code`), and italics (*text*),
        rendering them as beautifully styled native Word runs without literal markdown characters.
        Recursively handles nested inline code inside bold tags (e.g. **`code`** or **sign (`=`)**).
        """
        if default_color is None:
            default_color = self.COLOR_DARK

        # Tokenize by bold+italic, bold, inline code, and italic
        token_regex = re.compile(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*[^*]+?\*|`[^`]+`)')
        parts = token_regex.split(text)

        for part in parts:
            if not part:
                continue

            # 1. Bold + Italic (***text***)
            if part.startswith('***') and part.endswith('***') and len(part) >= 6:
                inner = part[3:-3]
                if '`' in inner:
                    for sp in re.split(r'(`[^`]+`)', inner):
                        if not sp:
                            continue
                        if sp.startswith('`') and sp.endswith('`') and len(sp) >= 2:
                            r = paragraph.add_run(sp[1:-1])
                            r.font.name = "Consolas"
                            r.font.size = Pt(9.5) if not is_header else Pt(9)
                            r.bold = True
                            r.italic = True
                            r.font.color.rgb = self.COLOR_CODE if not is_header else self.COLOR_WHITE
                        else:
                            r = paragraph.add_run(sp)
                            r.font.name = default_font
                            r.font.size = default_size
                            r.bold = True
                            r.italic = True
                            r.font.color.rgb = self.COLOR_NAVY if not is_header else default_color
                else:
                    run = paragraph.add_run(inner)
                    run.bold = True
                    run.italic = True
                    run.font.name = default_font
                    run.font.size = default_size
                    run.font.color.rgb = self.COLOR_NAVY if not is_header else default_color

            # 2. Bold (**text**)
            elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
                inner = part[2:-2]
                if '`' in inner:
                    for sp in re.split(r'(`[^`]+`)', inner):
                        if not sp:
                            continue
                        if sp.startswith('`') and sp.endswith('`') and len(sp) >= 2:
                            r = paragraph.add_run(sp[1:-1])
                            r.font.name = "Consolas"
                            r.font.size = Pt(9.5) if not is_header else Pt(9)
                            r.bold = True
                            r.font.color.rgb = self.COLOR_CODE if not is_header else self.COLOR_WHITE
                        else:
                            r = paragraph.add_run(sp)
                            r.font.name = default_font
                            r.font.size = default_size
                            r.bold = True
                            r.font.color.rgb = self.COLOR_NAVY if not is_header else default_color
                else:
                    run = paragraph.add_run(inner)
                    run.bold = True
                    run.font.name = default_font
                    run.font.size = default_size
                    run.font.color.rgb = self.COLOR_NAVY if not is_header else default_color

            # 3. Inline Code (`code`)
            elif part.startswith('`') and part.endswith('`') and len(part) >= 2:
                run = paragraph.add_run(part[1:-1])
                run.font.name = "Consolas"
                run.font.size = Pt(9.5) if not is_header else Pt(9)
                run.font.color.rgb = self.COLOR_CODE if not is_header else self.COLOR_WHITE
                run.bold = True if is_header else False

            # 4. Italic (*text*)
            elif part.startswith('*') and part.endswith('*') and len(part) >= 2:
                inner = part[1:-1]
                if '`' in inner:
                    for sp in re.split(r'(`[^`]+`)', inner):
                        if not sp:
                            continue
                        if sp.startswith('`') and sp.endswith('`') and len(sp) >= 2:
                            r = paragraph.add_run(sp[1:-1])
                            r.font.name = "Consolas"
                            r.font.size = Pt(9.5) if not is_header else Pt(9)
                            r.italic = True
                            r.font.color.rgb = self.COLOR_CODE if not is_header else self.COLOR_WHITE
                        else:
                            r = paragraph.add_run(sp)
                            r.font.name = default_font
                            r.font.size = default_size
                            r.italic = True
                            r.font.color.rgb = default_color
                else:
                    run = paragraph.add_run(inner)
                    run.italic = True
                    run.font.name = default_font
                    run.font.size = default_size
                    run.font.color.rgb = default_color

            # 5. Plain Text
            else:
                run = paragraph.add_run(part)
                run.font.name = default_font
                run.font.size = default_size
                run.font.color.rgb = default_color

    def _add_styled_heading(self, doc, text: str, level: int):
        """Adds structured hierarchical headings with modern typography and clean inline formatting."""
        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True

        # Strip any accidental leading markdown hashes
        clean_text = re.sub(r"^#+\s*", "", text).strip()

        if level == 1:
            p.paragraph_format.space_before = Pt(24)
            p.paragraph_format.space_after = Pt(8)
            self._add_inline_formatted_text(p, clean_text, default_font="Segoe UI Semibold",
                                           default_size=Pt(17), default_color=self.COLOR_NAVY, is_header=True)
        elif level == 2:
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            self._add_inline_formatted_text(p, clean_text, default_font="Segoe UI Semibold",
                                           default_size=Pt(13.5), default_color=self.COLOR_TEAL, is_header=True)
        elif level == 3:
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            self._add_inline_formatted_text(p, clean_text, default_font="Segoe UI Semibold",
                                           default_size=Pt(11.5), default_color=RGBColor(51, 65, 85), is_header=True)

    def _add_code_block(self, doc, code_text: str):
        """Builds an IDE-style code block with header bar, editor card background, and syntax tinting."""
        tbl = doc.add_table(rows=2, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Row 0: IDE Top Bar
        cell_header = tbl.cell(0, 0)
        self._set_cell_background(cell_header, "1E293B")  # Dark Slate header
        self._set_cell_margins(cell_header, top=60, bottom=60, left=140, right=140)
        self._set_cell_borders(cell_header,
                               left=dict(val="single", sz="24", color="0E8388"),
                               top=dict(val="single", sz="4", color="1E293B"),
                               right=dict(val="single", sz="4", color="1E293B"),
                               bottom=dict(val="single", sz="4", color="0F172A"))
        p_hdr = cell_header.paragraphs[0]
        p_hdr.paragraph_format.space_after = Pt(0)
        r_hdr = p_hdr.add_run("[PYTHON]")
        r_hdr.font.name = "Consolas"
        r_hdr.font.size = Pt(8)
        r_hdr.bold = True
        r_hdr.font.color.rgb = RGBColor(148, 163, 184)  # Slate-400

        # Row 1: Code Body
        cell_body = tbl.cell(1, 0)
        self._set_cell_background(cell_body, "F8FAFC")  # Crisp code editor background
        self._set_cell_margins(cell_body, top=120, bottom=120, left=160, right=160)
        self._set_cell_borders(cell_body,
                               left=dict(val="single", sz="24", color="0E8388"),
                               top=dict(val="single", sz="4", color="F8FAFC"),
                               right=dict(val="single", sz="4", color="CBD5E1"),
                               bottom=dict(val="single", sz="8", color="CBD5E1"))

        lines = code_text.strip().split("\n")
        p = cell_body.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1

        for i, line in enumerate(lines):
            if i > 0:
                p = cell_body.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1

            run = p.add_run(line)
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)

            # Code editor comment tinting
            line_s = line.strip()
            if line_s.startswith("# Output:") or "Output:" in line_s:
                run.font.color.rgb = RGBColor(3, 105, 161)  # Blue-600
                run.bold = True
            elif line_s.startswith("#"):
                run.font.color.rgb = RGBColor(100, 116, 139)  # Slate-500 muted
                run.italic = True
            else:
                run.font.color.rgb = RGBColor(15, 23, 42)    # Slate-900

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def _add_callout(self, doc, box_type: str, title: str, content_lines: list):
        """Creates a color-coded callout card (Tip, Note, Warning, Question) with styled content."""
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)

        card_types = {
            "tip": {
                "bg": "F0FDF4",       # Emerald-50
                "border": "16A34A",   # Emerald-600
                "prefix": "💡 PRO TIP",
                "color": RGBColor(22, 101, 52)
            },
            "warning": {
                "bg": "FFFBEB",       # Amber-50
                "border": "D97706",   # Amber-600
                "prefix": "⚠️ IMPORTANT NOTE",
                "color": RGBColor(180, 83, 9)
            },
            "question": {
                "bg": "FAF5FF",       # Purple-50
                "border": "7C3AED",   # Purple-600
                "prefix": "🎯 EXAM & PRACTICE CONCEPT",
                "color": RGBColor(109, 40, 217)
            },
            "note": {
                "bg": "EFF6FF",       # Blue-50
                "border": "2563EB",   # Blue-600
                "prefix": "📌 KEY TAKEAWAY",
                "color": RGBColor(29, 78, 216)
            }
        }

        cfg = card_types.get(box_type.lower(), card_types["note"])

        self._set_cell_background(cell, cfg["bg"])
        self._set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
        self._set_cell_borders(cell,
                               left=dict(val="single", sz="24", color=cfg["border"]),
                               top=dict(val="single", sz="4", color="E2E8F0"),
                               right=dict(val="single", sz="4", color="E2E8F0"),
                               bottom=dict(val="single", sz="4", color="E2E8F0"))

        # Header of Callout
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(3)
        header_text = cfg["prefix"]
        if title and title.strip():
            header_text += f": {title.strip()}"
        r_head = p.add_run(header_text)
        r_head.bold = True
        r_head.font.name = "Segoe UI Semibold"
        r_head.font.size = Pt(10.5)
        r_head.font.color.rgb = cfg["color"]

        # Body of Callout
        for line in content_lines:
            if not line.strip():
                continue
            p_body = cell.add_paragraph()
            p_body.paragraph_format.space_after = Pt(3)
            p_body.paragraph_format.line_spacing = 1.15
            self._add_inline_formatted_text(p_body, line.strip(), default_font="Segoe UI",
                                           default_size=Pt(10), default_color=RGBColor(51, 65, 85))

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def _add_table(self, doc, table_lines: list):
        """Builds a beautifully styled Word table with navy headers, alternating zebra rows, and formatted cells."""
        parsed_rows = []
        for line in table_lines:
            # Skip separator line like |---|---|
            if re.match(r"^\s*\|?\s*[-:]+[-| :]*\s*$", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if any(cells):
                parsed_rows.append(cells)

        if not parsed_rows:
            return

        headers = parsed_rows[0]
        data_rows = parsed_rows[1:]

        tbl = doc.add_table(rows=len(data_rows) + 1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Headers Row
        for i, h_text in enumerate(headers):
            cell = tbl.rows[0].cells[i]
            self._set_cell_background(cell, "0F2C59")  # Deep Navy
            self._set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            self._set_cell_borders(cell,
                                   top=dict(val="single", sz="4", color="0F2C59"),
                                   bottom=dict(val="single", sz="12", color="0E8388"),
                                   left=dict(val="single", sz="4", color="1E3A8A"),
                                   right=dict(val="single", sz="4", color="1E3A8A"))
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            self._add_inline_formatted_text(p, h_text, default_font="Segoe UI Semibold",
                                           default_size=Pt(9.5), default_color=self.COLOR_WHITE,
                                           is_header=True)

        # Data Rows
        for r_idx, row in enumerate(data_rows):
            bg_col = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
            for c_idx, val in enumerate(row):
                if c_idx < len(headers):
                    cell = tbl.rows[r_idx + 1].cells[c_idx]
                    self._set_cell_background(cell, bg_col)
                    self._set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                    self._set_cell_borders(cell,
                                           top=dict(val="single", sz="4", color="E2E8F0"),
                                           bottom=dict(val="single", sz="4", color="E2E8F0"),
                                           left=dict(val="single", sz="4", color="E2E8F0"),
                                           right=dict(val="single", sz="4", color="E2E8F0"))
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2)
                    self._add_inline_formatted_text(p, val, default_font="Segoe UI",
                                                   default_size=Pt(9), default_color=self.COLOR_DARK)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def build_document(self, markdown_text: str, base_filename: str = "Master_Lecture_Notes") -> dict:
        """Parses markdown and generates formatted .docx and .doc documents."""
        doc = Document()

        # Hidden Document Metadata Properties
        try:
            doc.core_properties.author = Config.AUTHOR
            doc.core_properties.last_modified_by = Config.AUTHOR
            doc.core_properties.comments = f"Generated by Lecture Document Generator {Config.VERSION} (GitHub: @HasithaLWi)"
            doc.core_properties.category = "Educational Lecture Notes"
            doc.core_properties.keywords = f"Lecture Notes, Python, {Config.AUTHOR}, {Config.VERSION}"
        except Exception:
            pass

        # Document Page Margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

            header = section.header.paragraphs[0]
            header.text = "Comprehensive Lecture Study Guide  |  ITS 2122 – Python for Data Science & AI"
            header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if header.runs:
                header.runs[0].font.name = "Segoe UI"
                header.runs[0].font.size = Pt(8.5)
                header.runs[0].font.color.rgb = self.COLOR_MUTED

            footer = section.footer.paragraphs[0]
            footer.text = f"Generated by Lecture Document Generator {Config.VERSION}  |  {Config.AUTHOR} (@HasithaLWi)"
            footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if footer.runs:
                footer.runs[0].font.name = "Segoe UI"
                footer.runs[0].font.size = Pt(8.5)
                footer.runs[0].font.color.rgb = RGBColor(148, 163, 184)

        # Style defaults
        normal = doc.styles['Normal']
        normal.font.name = 'Segoe UI'
        normal.font.size = Pt(10.5)
        normal.font.color.rgb = self.COLOR_DARK
        normal.paragraph_format.line_spacing = 1.15
        normal.paragraph_format.space_after = Pt(5)

        # Line-by-line streaming parser
        lines = markdown_text.split("\n")
        in_code_block = False
        code_buffer = []

        in_table = False
        table_buffer = []

        in_callout = False
        callout_type = "note"
        callout_title = ""
        callout_lines = []

        def flush_callout():
            nonlocal in_callout, callout_type, callout_title, callout_lines
            if in_callout and (callout_title or callout_lines):
                self._add_callout(doc, callout_type, callout_title, callout_lines)
            in_callout = False
            callout_type = "note"
            callout_title = ""
            callout_lines = []

        def flush_table():
            nonlocal in_table, table_buffer
            if in_table and table_buffer:
                self._add_table(doc, table_buffer)
            in_table = False
            table_buffer = []

        def flush_code():
            nonlocal in_code_block, code_buffer
            if in_code_block and code_buffer:
                self._add_code_block(doc, "\n".join(code_buffer))
            in_code_block = False
            code_buffer = []

        for raw_line in lines:
            line_str = raw_line.strip()

            # 1. Code Block Delimiter
            if line_str.startswith("```"):
                flush_table()
                flush_callout()
                if in_code_block:
                    flush_code()
                else:
                    in_code_block = True
                    code_buffer = []
                continue

            if in_code_block:
                code_buffer.append(raw_line)
                continue

            # 2. Table Rows
            if "|" in raw_line and raw_line.strip().startswith("|"):
                flush_callout()
                in_table = True
                table_buffer.append(raw_line)
                continue
            else:
                if in_table:
                    flush_table()

            # 3. Callouts / Blockquotes
            if line_str.startswith(">"):
                stripped = re.sub(r"^>\s?", "", line_str).strip()

                # Check if this line is an alert marker
                alert_match = re.match(r"^\[!(TIP|WARNING|IMPORTANT|NOTE|QUESTION|CAUTION)\](.*)$", stripped, re.IGNORECASE)
                named_match = re.match(r"^(TIP|IMPORTANT NOTE|KEY TAKEAWAY|NOTE|QUESTION|EXAM):\s*(.*)$", stripped, re.IGNORECASE)

                if alert_match:
                    flush_callout()
                    tag = alert_match.group(1).lower()
                    if tag in ["warning", "important", "caution"]:
                        callout_type = "warning"
                    elif tag == "tip":
                        callout_type = "tip"
                    elif tag == "question":
                        callout_type = "question"
                    else:
                        callout_type = "note"
                    callout_title = alert_match.group(2).strip()
                    in_callout = True
                    continue

                elif named_match:
                    flush_callout()
                    prefix = named_match.group(1).lower()
                    if "warning" in prefix or "important" in prefix:
                        callout_type = "warning"
                    elif "tip" in prefix:
                        callout_type = "tip"
                    elif "question" in prefix or "exam" in prefix:
                        callout_type = "question"
                    else:
                        callout_type = "note"
                    callout_title = named_match.group(2).strip()
                    in_callout = True
                    continue

                else:
                    # Content line inside blockquote
                    if not in_callout:
                        in_callout = True
                        callout_type = "note"
                        callout_title = ""
                    callout_lines.append(stripped)
                    continue
            else:
                if in_callout:
                    flush_callout()

            # Empty lines
            if not line_str:
                continue

            # 4. Headings
            if line_str.startswith("# "):
                self._add_styled_heading(doc, line_str[2:].strip(), level=1)
            elif line_str.startswith("## "):
                self._add_styled_heading(doc, line_str[3:].strip(), level=2)
            elif line_str.startswith("### "):
                self._add_styled_heading(doc, line_str[4:].strip(), level=3)
            elif line_str.startswith("#### "):
                # Render Level 4 heading as bold section subtitle
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.keep_with_next = True
                self._add_inline_formatted_text(p, line_str[5:].strip(), default_font="Segoe UI Semibold",
                                               default_size=Pt(10.5), default_color=self.COLOR_NAVY)

            # 5. Horizontal Dividers
            elif line_str in ["---", "***", "___"]:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(6)

            # 6. Bullet Lists
            elif line_str.startswith(("- ", "* ", "• ")):
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.15
                bullet_content = re.sub(r"^[-*•]\s+", "", line_str)
                self._add_inline_formatted_text(p, bullet_content, default_font="Segoe UI",
                                               default_size=Pt(10.5), default_color=self.COLOR_DARK)

            # 7. Numbered Lists
            elif re.match(r"^\d+\.\s+", line_str):
                p = doc.add_paragraph(style='List Number')
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.15
                num_content = re.sub(r"^\d+\.\s+", "", line_str)
                self._add_inline_formatted_text(p, num_content, default_font="Segoe UI",
                                               default_size=Pt(10.5), default_color=self.COLOR_DARK)

            # 8. Standard Paragraph
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(5)
                p.paragraph_format.line_spacing = 1.15
                self._add_inline_formatted_text(p, raw_line, default_font="Segoe UI",
                                               default_size=Pt(10.5), default_color=self.COLOR_DARK)

        # Flush any remaining buffers
        flush_code()
        flush_table()
        flush_callout()

        # Save files
        docx_file = self.output_dir / f"{base_filename}.docx"
        doc_file = self.output_dir / f"{base_filename}.doc"

        doc.save(str(docx_file))
        shutil.copyfile(str(docx_file), str(doc_file))

        print(f"\n[DocumentBuilder] Successfully created documents:")
        print(f"  • DOCX: {docx_file}")
        print(f"  • DOC : {doc_file}")

        return {
            "docx_path": str(docx_file),
            "doc_path": str(doc_file)
        }
