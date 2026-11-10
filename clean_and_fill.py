import openpyxl
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
import html
import shutil
import os

def clean_text(text):
    if not text:
        return ""
    t = str(text)
    # Fix mojibake
    t = t.replace("â€“", "–")
    # Replace <br> variants with newline
    t = re.sub(r"<\s*br\s*/?>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"<\s*/\s*br\s*>", "\n", t, flags=re.IGNORECASE)
    # Remove HTML tags (<b>, </b>, <strong>, <i>, <em>, <span>, <div>, <p>, <a>, etc.)
    t = re.sub(r"</?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>", "", t)
    # Unescape HTML entities
    t = html.unescape(t)
    
    # Normalize lines: strip each line and collapse excess blank lines
    lines = [line.strip() for line in t.splitlines()]
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False
            
    return "\n".join(cleaned_lines).strip()

def main():
    excel_path = "evaluasi_60_pertanyaan_dan_audit_sistem.xlsx"
    docx_path = "daftar pertanyaan.docx"
    backup_docx_path = "daftar pertanyaan_backup.docx"

    # Backup original docx if not backed up yet
    if not os.path.exists(backup_docx_path):
        shutil.copyfile(docx_path, backup_docx_path)
        print(f"Backup created at: {backup_docx_path}")

    # Load Excel
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb["Q01_Q60_Benchmark"]

    answers = {}
    for r in range(2, 62):
        qid = ws.cell(row=r, column=1).value
        sistem_new_val = ws.cell(row=r, column=5).value or ""
        cleaned = clean_text(sistem_new_val)
        answers[qid] = cleaned

    print(f"Loaded and cleaned {len(answers)} answers from Excel.")

    # Load Word document
    doc = docx.Document(docx_path)
    table = doc.tables[0]

    updated_count = 0
    for r_idx in range(1, len(table.rows)):
        row = table.rows[r_idx]
        qid = row.cells[0].text.strip()
        if qid in answers:
            cell = row.cells[4] # Column 5: 'Jawaban Bot'
            clean_ans = answers[qid]
            
            # Clear existing paragraphs in cell
            # In python-docx, cell.paragraphs has at least 1 paragraph
            p = cell.paragraphs[0]
            p.text = ""
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = 19050 # 1.5 pt
            p.paragraph_format.space_after = 19050  # 1.5 pt
            p.paragraph_format.line_spacing = 1.05
            
            # Add run with same font and size as expected answer (Times New Roman, 6.5 pt)
            run = p.add_run(clean_ans + "\n")
            run.font.name = "Times New Roman"
            run.font.size = Pt(6.5)
            
            updated_count += 1
        else:
            print(f"Warning: QID {qid} not found in Excel!")

    print(f"Successfully updated {updated_count} rows in {docx_path}.")
    doc.save(docx_path)
    print("Document saved successfully.")

if __name__ == "__main__":
    main()
