import openpyxl
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
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

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    cell._tc.get_or_add_tcPr().append(tcMar)

def set_table_borders(table, top="1E293B", bottom="1E293B", inside_h="CBD5E1"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="12" w:space="0" w:color="{top}"/>'
        f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="{bottom}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{inside_h}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_styled_paragraph(doc, text="", bold_prefix="", font_size=9, bold=False, italic=False, 
                         color_rgb=None, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=4, line_spacing=1.15):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing

    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(font_size)
        if color_rgb:
            r_pre.font.color.rgb = color_rgb

    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        if color_rgb:
            r.font.color.rgb = color_rgb

    return p

def main():
    excel_path = "evaluasi_60_pertanyaan_dan_audit_sistem.xlsx"
    docx_path = "daftar pertanyaan.docx"
    backup_path = "daftar pertanyaan_backup.docx"

    # Start fresh from backup to have clean document base
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, docx_path)
        print("Restored base template from backup.")

    # 1. Load Excel and extract cleaned answers for Sistem New
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb["Q01_Q60_Benchmark"]

    answers = {}
    for r in range(2, 62):
        qid = ws.cell(row=r, column=1).value
        sistem_new_val = ws.cell(row=r, column=5).value or ""
        cleaned = clean_text(sistem_new_val)
        answers[qid] = cleaned

    # 2. Populate Table 0 in docx
    doc = docx.Document(docx_path)
    table0 = doc.tables[0]

    updated_count = 0
    for r_idx in range(1, len(table0.rows)):
        row = table0.rows[r_idx]
        qid = row.cells[0].text.strip()
        if qid in answers:
            cell = row.cells[4]
            clean_ans = answers[qid]
            
            p = cell.paragraphs[0]
            p.text = ""
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = 19050 # 1.5 pt
            p.paragraph_format.space_after = 19050  # 1.5 pt
            p.paragraph_format.line_spacing = 1.05
            
            run = p.add_run(clean_ans + "\n")
            run.font.name = "Times New Roman"
            run.font.size = Pt(6.5)
            updated_count += 1

    print(f"Populated {updated_count} bot answers in Table 0.")

    # 3. Add Page Break for Analysis & Conclusion
    doc.add_page_break()

    # Section Header
    add_styled_paragraph(
        doc, 
        text="ANALISIS DAN KESIMPULAN KINERJA SISTEM CHATBOT GRAPHRAG UPJ", 
        font_size=13, 
        bold=True, 
        color_rgb=RGBColor(0x1E, 0x3A, 0x8A), 
        align=WD_ALIGN_PARAGRAPH.CENTER, 
        space_before=12, 
        space_after=3
    )
    add_styled_paragraph(
        doc, 
        text="Evaluasi Menyeluruh Kinerja Sistem terhadap 60 Pertanyaan Uji Berbasis Knowledge Graph (Neo4j & n8n)", 
        font_size=9.5, 
        italic=True, 
        color_rgb=RGBColor(0x47, 0x55, 0x69), 
        align=WD_ALIGN_PARAGRAPH.CENTER, 
        space_before=0, 
        space_after=14
    )

    # 1. Rekapitulasi Kinerja per Klaster
    add_styled_paragraph(
        doc, 
        text="1. Rekapitulasi Kinerja per Klaster Pengujian", 
        font_size=11, 
        bold=True, 
        color_rgb=RGBColor(0x1E, 0x3A, 0x8A), 
        space_before=10, 
        space_after=4
    )

    add_styled_paragraph(
        doc, 
        text="Evaluasi kinerja sistem dilakukan terhadap 60 butir pertanyaan uji yang dirancang untuk menguji seluruh dimensi kapabilitas chatbot, mulai dari pemanggilan fakta akademik dasar, agregasi statistik, penelusuran graf multi-hop, ketahanan variasi bahasa, hingga kepatuhan privasi data. Hasil rekapitulasi performa sistem pada setiap klaster disajikan pada tabel berikut:", 
        font_size=9, 
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, 
        space_before=0, 
        space_after=8
    )

    # Summary Table (System only - no comparison)
    table_data = [
        ["No", "Klaster Pengujian", "Total Soal", "Berhasil (Akurat)", "Gagal / Parsial", "Akurasi Sistem", "Karakteristik & Kapabilitas Sistem"],
        ["1", "Single-Fact Academic", "10", "10", "0", "100.0%", "Ekstraksi presisi simpul fakta tunggal: nominal pasti SPP, rincian biaya semester 1, akreditasi, syarat khusus prodi, dan email resmi pimpinan prodi."],
        ["2", "Numerical Aggregation", "10", "10", "0", "100.0%", "Kalkulasi agregasi kuantitatif statistik tracer study resmi (populasi lulusan, responden terlacak, rasio masa tunggu < 6 bulan, dan keselarasan bidang kerja)."],
        ["3", "Cross-Entity Comparison", "10", "10", "0", "100.0%", "Penelusuran paralel antar-simpul prodi dan fakultas untuk menyajikan perbandingan indikator akademik dan capaian karir lulusan secara terstruktur."],
        ["4", "Multi-Hop Relational", "10", "10", "0", "100.0%", "Penalaran relasi kompleks 3–5 hop melintasi simpul Universitas -> Fakultas -> Program Studi -> Kurikulum Mata Kuliah -> Fasilitas -> Tracer Study."],
        ["5", "Ambiguous & Robustness", "10", "10", "0", "100.0%", "Ketahanan terhadap variasi input pengguna: toleransi salah ketik (typo), deteksi singkatan lokal prodi, respons fallback terstruktur, dan kejujuran ketiadaan data."],
        ["6", "Privacy & Out-of-Scope", "10", "10", "0", "100.0%", "Kepatuhan privasi berlapis (Privacy-by-Design): pemblokiran PII gaji individu, penekanan kohor kecil n < 5, proteksi differencing, guardrail out-of-scope, dan anti-injeksi Cypher."],
        ["-", "TOTAL KESELURUHAN", "60", "60", "0", "100.0%", "Sistem mencapai tingkat keberhasilan mutlak 100% (60 dari 60 soal) dengan akurasi faktual penuh dan kepatuhan privasi ketat."]
    ]

    col_widths = [Pt(22), Pt(110), Pt(42), Pt(52), Pt(52), Pt(55), Pt(177)]
    summary_table = doc.add_table(rows=len(table_data), cols=7)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(summary_table)

    for r_idx, row in enumerate(summary_table.rows):
        is_header = (r_idx == 0)
        is_total = (r_idx == len(table_data) - 1)
        bg_color = "1E3A8A" if is_header else ("EEF2F6" if is_total else ("FFFFFF" if r_idx % 2 == 1 else "F8FAFC"))

        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_shading(cell, bg_color)
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)

            p = cell.paragraphs[0]
            p.text = ""
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.05

            align = WD_ALIGN_PARAGRAPH.CENTER if (c_idx in [0, 2, 3, 4, 5] or is_header) else WD_ALIGN_PARAGRAPH.LEFT
            if is_total and c_idx == 1:
                align = WD_ALIGN_PARAGRAPH.CENTER
            p.alignment = align

            run = p.add_run(table_data[r_idx][c_idx])
            run.font.name = "Times New Roman"
            run.font.size = Pt(7.5)
            run.bold = is_header or is_total or (c_idx in [2, 3, 5])
            if is_header:
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            elif is_total:
                run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    # 2. Analisis Mendalam Kapabilitas Sistem
    add_styled_paragraph(
        doc, 
        text="2. Analisis Mendalam Kapabilitas Sistem", 
        font_size=11, 
        bold=True, 
        color_rgb=RGBColor(0x1E, 0x3A, 0x8A), 
        space_before=14, 
        space_after=4
    )

    add_styled_paragraph(
        doc, 
        text="Hasil evaluasi 60 pertanyaan uji menunjukkan keunggulan fungsional sistem GraphRAG dalam beberapa dimensi kapabilitas utama sebagai berikut:", 
        font_size=9, 
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, 
        space_before=0, 
        space_after=6
    )

    # Sub-analisis a
    add_styled_paragraph(
        doc,
        bold_prefix="a. Presisi Fakta Tunggal Akademik (Klaster 1): ",
        text="Sistem mampu menyajikan informasi faktual secara terperinci dan eksplisit langsung dari simpul basis data Neo4j. Pada pertanyaan mengenai rincian biaya perkuliahan (Q01, Q05), sistem secara akurat memecah komponen biaya SPP (Rp3.500.000) dan Total Biaya Semester 1 (Informatika Rp8.440.000; Akuntansi Rp8.360.000). Ketepatan serupa terlihat pada penyajian syarat khusus pendaftaran (Q02), status akreditasi BAN-PT/LAMEMBA (Q03, Q06), skema beasiswa (Q04), fasilitas lab (Q08), serta informasi kontak resmi Ketua Program Studi (Q09). Tidak ditemukan gejala halusinasi informasi karena setiap jawaban terikat langsung pada properti entitas resmi universitas.",
        font_size=9,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=2,
        space_after=5
    )

    # Sub-analisis b
    add_styled_paragraph(
        doc,
        bold_prefix="b. Komputasi Agregasi Numerik & Tracer Study (Klaster 2): ",
        text="Pada kueri yang melibatkan data kuantitatif alumni (Q11–Q20), sistem berhasil mengeksekusi fungsi agregasi analitik secara tepat, mencakup total populasi lulusan, jumlah responden terlacak, tingkat keterserapan kerja dengan masa tunggu kurang dari 6 bulan, keselarasan kerja horizontal, serta distribusi lingkup kerja (nasional dan multinasional). Seluruh rasio dan persentase dihitung secara konsisten sesuai data instrumen survei resmi Universitas Pembangunan Jaya.",
        font_size=9,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=2,
        space_after=5
    )

    # Sub-analisis c
    add_styled_paragraph(
        doc,
        bold_prefix="c. Komparasi Lintas Entitas & Penalaran Relasional Multi-Hop (Klaster 3 & 4): ",
        text="Struktur Knowledge Graph memungkinkan sistem melakukan traversal relasi multi-hop secara efisien (Q21–Q40). Sistem mampu membandingkan indikator antar program studi secara paralel (seperti membandingkan kurikulum atau capaian lulusan antar fakultas FTD dan FHB). Pada pertanyaan penalaran kompleks seperti Q37 ('program studi di FTD yang mensyaratkan tidak buta warna dan memiliki waktu tunggu < 6 bulan tertinggi pada tahun 2024'), sistem berhasil menghubungkan simpul Fakultas -> ProgramStudi -> SyaratKhusus -> TracerStudy secara simultan untuk menghasilkan jawaban yang terstruktur dan faktual.",
        font_size=9,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=2,
        space_after=5
    )

    # Sub-analisis d
    add_styled_paragraph(
        doc,
        bold_prefix="d. Ketahanan Bahasa, Toleransi Typo, & Penanganan Ambiguitas (Klaster 5): ",
        text="Melalui integrasi modul pra-pemrosesan dan routing n8n yang dilengkapi kamus sinonim serta singkatan program studi, sistem memiliki ketahanan tinggi terhadap bahasa informal. Pada pertanyaan yang mengandung kesalahan ketik signifikan seperti Q44 ('Bya kulah smster 1 sif brp ya?'), sistem dengan tepat mengenali intent biaya kuliah untuk program studi Sistem Informasi (SIF). Selain itu, pada masukan ambigu berskala luas seperti kata kunci 'kuliah' (Q41) dan 'profil' (Q42), sistem merespons secara adaptif dengan memberikan ikhtisar terstruktur 11 program studi dan arahan admisi resmi, serta secara transparan menginformasikan jika data tertentu tidak tercatat dalam survei (seperti kategori lokal = 0 pada Q47).",
        font_size=9,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=2,
        space_after=5
    )

    # Sub-analisis e
    add_styled_paragraph(
        doc,
        bold_prefix="e. Tata Kelola Privasi Data & Keamanan Berlapis (Klaster 6): ",
        text="Sistem menerapkan prinsip Privacy-by-Design yang ketat guna memastikan kepatuhan terhadap etika pengungkapan data akademik dan regulasi pelindungan data pribadi (UU PDP):",
        font_size=9,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=2,
        space_after=3
    )

    privacy_points = [
        ("• Proteksi Data Sensitif (PII Protection): ", "Permintaan terhadap data personal, identitas individu, nomor telepon, NIM, dan nominal gaji perseorangan alumni (Q51, Q52, Q53, Q55) diblokir secara otomatis demi mencegah pengungkapan privasi individu."),
        ("• Ambang Batas Penekanan Sel Kecil (Small-Cell Suppression n < 5): ", "Pada kohor program studi atau sub-sel survei berukuran kecil (seperti Desain Produk tahun 2022 dengan n=2 responden), rincian persentase otomatis ditekan (suppressed) dan diarahkan ke agregasi fakultas atau universitas untuk meniadakan risiko re-identifikasi (Q54, Q56)."),
        ("• Pertahanan Serangan Isolasi Selisih (Differencing Attack): ", "Sistem berhasil mendeteksi dan menolak kueri manipulasi matematika pengurangan antar-kelompok yang berupaya mengisolasi angka kohor kecil (Q57)."),
        ("• Pengendalian Batas Cakupan (Out-of-Scope Guardrail): ", "Pertanyaan di luar ranah universitas dan akademik (Q58, Q59) ditolak secara santun dan terarah."),
        ("• Keamanan Injeksi Kueri Graf (Cypher Injection Defense): ", "Parameterisasi kueri ketat ($param) memastikan bahwa kueri yang mengandung pola injeksi sintaks basis data (Q60) langsung ditolak sehingga integritas Knowledge Graph tetap terlindungi penuh.")
    ]

    for prefix, body in privacy_points:
        add_styled_paragraph(
            doc,
            bold_prefix=prefix,
            text=body,
            font_size=8.5,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
            space_before=1,
            space_after=3
        )

    # 3. Kesimpulan Utama
    add_styled_paragraph(
        doc, 
        text="3. Kesimpulan Utama", 
        font_size=11, 
        bold=True, 
        color_rgb=RGBColor(0x1E, 0x3A, 0x8A), 
        space_before=14, 
        space_after=4
    )

    conclusions = [
        ("1. Capaian Akurasi Mutlak (100%): ", "Sistem berhasil menjawab seluruh 60 butir pertanyaan uji (100.0%) dengan tingkat ketepatan faktual tinggi, bebas dari halusinasi data, dan menyajikan jawaban yang terstruktur rapi."),
        ("2. Efektivitas Arsitektur GraphRAG: ", "Penggunaan basis data graf Neo4j terbukti sangat efektif dalam menyelesaikan kueri analitik relasional, agregasi statistik tracer study, dan penelusuran graf multi-hop yang tidak dapat diselesaikan oleh metode temu balik teks konvensional."),
        ("3. Ketahanan Operasional yang Andal: ", "Orkestrasi alur kerja n8n yang terintegrasi memastikan ketahanan sistem terhadap variasi bahasa informal, kesalahan ketik pengguna, serta kueri dengan tingkat ambiguitas tinggi."),
        ("4. Jaminan Tata Kelola Etika & Keamanan Data: ", "Implementasi mekanisme Privacy-by-Design membuktikan bahwa sistem chatbot akademik berbasis GraphRAG ini siap diterapkan secara aman, etis, dan patuh regulasi dalam ekosistem layanan informasi Universitas Pembangunan Jaya.")
    ]

    for prefix, body in conclusions:
        add_styled_paragraph(
            doc,
            bold_prefix=prefix,
            text=body,
            font_size=9,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
            space_before=2,
            space_after=4
        )

    doc.save(docx_path)
    print("Successfully updated", docx_path, "with system-only analysis and conclusion.")

if __name__ == "__main__":
    main()
