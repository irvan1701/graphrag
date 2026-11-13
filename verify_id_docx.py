# -*- coding: utf-8 -*-
"""
Verification script for project_revisi_ejeset_bertanda_terbaru_id.docx
"""

import docx

doc = docx.Document("project_revisi_ejeset_bertanda_terbaru_id.docx")

print(f"Total Paragraphs: {len(doc.paragraphs)}")
print(f"Total Tables: {len(doc.tables)}")

# Check key paragraphs
print("\n--- Key Paragraphs ---")
check_paras = [0, 1, 2, 4, 5, 6, 8, 9, 14, 16, 24, 25, 28, 30, 32, 36, 39, 44, 45, 47, 51, 56, 57, 59, 64, 69, 72, 77, 116, 118]
for idx in check_paras:
    if idx < len(doc.paragraphs):
        p = doc.paragraphs[idx]
        print(f"P{idx:03d}: {p.text[:90]}")

# Check red runs
red_runs = []
for p_idx, p in enumerate(doc.paragraphs):
    for r in p.runs:
        if r.font.color and r.font.color.rgb:
            if r.font.color.rgb == docx.shared.RGBColor(0xCC, 0x00, 0x00):
                red_runs.append((f"P{p_idx}", r.text))

print(f"\nTotal Red Marked Runs in Paragraphs: {len(red_runs)}")
for r in red_runs:
    print(f"  {r[0]}: {r[1]}")

# Check tables
print("\n--- Key Tables ---")
for t_idx, t in enumerate(doc.tables):
    h = [c.text.strip().replace('\n', ' ') for c in t.rows[0].cells[:3]]
    print(f"Table {t_idx} ({len(t.rows)} rows x {len(t.columns)} cols): {h}")

# Check Table 0 (Abstract)
print("\n--- Table 0 (Abstract Preview) ---")
print(doc.tables[0].rows[0].cells[0].text[:300])

# Check Table 12 (Table A1 Preview)
print("\n--- Table 12 (Table A1 Preview) ---")
print("Header:", [c.text.strip().replace('\n', ' ') for c in doc.tables[12].rows[0].cells])
print("Row 1 (Q01):", [c.text.strip().replace('\n', ' ')[:40] for c in doc.tables[12].rows[1].cells])
print("Row 60 (Q60):", [c.text.strip().replace('\n', ' ')[:40] for c in doc.tables[12].rows[60].cells])
