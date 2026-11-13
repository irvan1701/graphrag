# -*- coding: utf-8 -*-
"""
Build the Indonesian version of project_revisi_ejeset_bertanda_terbaru.docx.
Saves to project_revisi_ejeset_bertanda_terbaru_id.docx.
"""

import docx
import re
from docx.shared import RGBColor, Pt
from translate_paragraphs import PARAGRAPH_TRANSLATIONS
from translate_tables import TABLES_TRANSLATIONS

RED_COLOR = RGBColor(0xCC, 0x00, 0x00)

def update_paragraph(p, new_text):
    """
    Updates a paragraph while preserving font style, size,
    and styling placeholders === [...] === with bold red font.
    """
    if not p.text.strip():
        return
    
    # Extract formatting from existing non-placeholder run
    font_color = None
    font_name = None
    font_size = None
    bold = None
    italic = None
    for r in p.runs:
        if r.text.strip() and not r.text.startswith("==="):
            if r.font.color and r.font.color.rgb:
                font_color = r.font.color.rgb
            font_name = r.font.name
            font_size = r.font.size
            bold = r.bold
            italic = r.italic
            break

    p.text = ""
    parts = re.split(r'(===.*?===)', new_text)
    for part in parts:
        if not part:
            continue
        run = p.add_run(part)
        if font_name:
            run.font.name = font_name
        if font_size:
            run.font.size = font_size
        
        if part.startswith("===") and part.endswith("==="):
            run.bold = True
            run.font.color.rgb = RED_COLOR
        else:
            if bold is not None:
                run.bold = bold
            if italic is not None:
                run.italic = italic
            if font_color:
                run.font.color.rgb = font_color

def update_cell(cell, new_text):
    """
    Updates a table cell while preserving font style, size, color,
    and styling placeholders === [...] === with bold red font.
    """
    font_color = None
    font_name = None
    font_size = None
    bold = None
    italic = None
    
    if cell.paragraphs and cell.paragraphs[0].runs:
        orig_run = cell.paragraphs[0].runs[0]
        if orig_run.font.color and orig_run.font.color.rgb:
            font_color = orig_run.font.color.rgb
        font_name = orig_run.font.name
        font_size = orig_run.font.size
        bold = orig_run.bold
        italic = orig_run.italic

    cell.text = ""
    p = cell.paragraphs[0]
    
    parts = re.split(r'(===.*?===)', new_text)
    for part in parts:
        if not part:
            continue
        run = p.add_run(part)
        if font_name:
            run.font.name = font_name
        if font_size:
            run.font.size = font_size
        
        if part.startswith("===") and part.endswith("==="):
            run.bold = True
            run.font.color.rgb = RED_COLOR
        else:
            if bold is not None:
                run.bold = bold
            if italic is not None:
                run.italic = italic
            if font_color:
                run.font.color.rgb = font_color

def main():
    src_path = "project_revisi_ejeset_bertanda_terbaru.docx"
    dst_path = "project_revisi_ejeset_bertanda_terbaru_id.docx"
    
    print(f"Loading {src_path}...")
    doc = docx.Document(src_path)
    
    print("Translating paragraphs...")
    paras_updated = 0
    for idx, p in enumerate(doc.paragraphs):
        if idx in PARAGRAPH_TRANSLATIONS:
            update_paragraph(p, PARAGRAPH_TRANSLATIONS[idx])
            paras_updated += 1
    print(f"Updated {paras_updated} paragraphs.")
    
    print("Translating tables...")
    tables_updated = 0
    for t_idx, table in enumerate(doc.tables):
        if t_idx in TABLES_TRANSLATIONS:
            t_data = TABLES_TRANSLATIONS[t_idx]
            for r_idx, row_data in enumerate(t_data):
                if r_idx < len(table.rows):
                    row = table.rows[r_idx]
                    for c_idx, cell_value in enumerate(row_data):
                        if c_idx < len(row.cells):
                            update_cell(row.cells[c_idx], str(cell_value))
            tables_updated += 1
    print(f"Updated {tables_updated} tables.")
    
    print(f"Saving to {dst_path}...")
    doc.save(dst_path)
    print("Successfully created Indonesian version:", dst_path)

if __name__ == "__main__":
    main()
