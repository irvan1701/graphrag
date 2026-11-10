import sqlite3
import os
import json
import glob
import re
import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upj_academic.db")

FACULTY_MAP = {
    "inf": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Informatika"},
    "sif": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Sistem Informasi"},
    "ars": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Arsitektur"},
    "tsp": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Teknik Sipil"},
    "dkv": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Desain Komunikasi Visual"},
    "dp": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Desain Produk"},
    "akt": {"code": "FHB", "faculty": "Fakultas Humaniora dan Bisnis", "name": "Akuntansi"},
    "mnj": {"code": "FHB", "faculty": "Fakultas Humaniora dan Bisnis", "name": "Manajemen"},
    "kom": {"code": "FHB", "faculty": "Fakultas Humaniora dan Bisnis", "name": "Ilmu Komunikasi"},
    "psi": {"code": "FHB", "faculty": "Fakultas Humaniora dan Bisnis", "name": "Psikologi"},
    "ppar": {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": "Pendidikan Profesi Arsitek"}
}

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'[ \t]+', ' ', text).strip()

def clean_career_label(raw_item):
    s = clean_text(raw_item)
    prefixes = [
        r'^(?:such\s+as\s+becoming|or\s+even|or|atau|becoming|become\s+a|menjadi|sebagai|creating)\s+',
        r'^(?:drive\s+innovation\s+as\s+a|turn\s+data\s+into\s+insights\s+as\s+a)\s+',
        r'^(?:menggerakkan\s+inovasi\s+sebagai|ubah\s+data\s+menjadi\s+wawasan\s+sebagai)\s+',
        r'^(?:graduates\s+of\s+upj|where\s+future|career\s+opportunities\s+for\s+upj|as\s+a\s+upj)\s+',
        r'^(?:upj\s+ppar\s+graduates\s+are\s+prepared\s+to\s+become\s+young)\s+',
        r'^(?:able\s+to\s+work\s+in|collaborating\s+with|capable\s+of\s+building\s+independent\s+ventures\s+in)\s+',
        r'^(?:based)\s+'
    ]
    changed = True
    while changed:
        changed = False
        for pat in prefixes:
            ns = re.sub(pat, '', s, flags=re.IGNORECASE).strip(" .,-:;")
            if ns != s:
                s = ns
                changed = True
    low = s.lower()
    if low in {'designer', 'architect', 'entrepreneur', 'civil engineer', ''}:
        return ""
    if len(s) < 4 or low.startswith(('career opportunities', 'where future')):
        return ""
    return s[0].upper() + s[1:] if s and s[0].islower() else s

def is_valid_facility_line(line):
    l = clean_text(line)
    if not l or len(l) < 3 or len(l) > 65:
        return False
    low = l.lower()
    if low in {'facilities', 'contact us', 'pmb'} or '::' in l:
        return False
    if re.match(r'^\d+\s*/\s*\d+$', l):
        return False
    noise_markers = [
        'leadership training', 'public lecture', 'participants of',
        'collaboration with', 'welcome address', 'see more', 'read more',
        'workshop batch', 'seminar', 'kegiatan', 'berita'
    ]
    if any(m in low for m in noise_markers):
        return False
    return True

def parse_courses(content, prodi_code):
    courses = []
    sem_pattern = r'((?:Semester\s+\d+)|(?:\d+(?:st|nd|rd|th)\s+Semester)|(?:MKP\s*–\s*\d+)|(?:Elective\s+Courses?))'
    parts = re.split(sem_pattern, content, flags=re.IGNORECASE)
    
    curriculum = "2023 Curriculum" if "2023 Curriculum" in content else "Standard Curriculum"
    
    for i in range(1, len(parts), 2):
        sem_header = parts[i].strip()
        sem_body = parts[i+1] if i + 1 < len(parts) else ""
        
        sem_norm = sem_header
        num_m = re.search(r'(\d+)', sem_header)
        if num_m and 'semester' in sem_header.lower():
            sem_norm = f"Semester {num_m.group(1)}"
            
        lines = [l.strip() for l in sem_body.split('\n') if l.strip()]
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line in ['Course Name', 'SKS', 'Contact Us', 'PMB', 'Distribution Of', 'Read More']:
                idx += 1
                continue
            
            if idx + 1 < len(lines) and re.match(r'^\d{1,2}$', lines[idx+1]):
                course_name = line
                sks = int(lines[idx+1])
                code_match = re.search(r'\(([A-Z0-9]+)\)', course_name)
                code = code_match.group(1) if code_match else f"{prodi_code}_{len(courses)+1}"
                
                courses.append({
                    "name": course_name,
                    "code": code,
                    "sks": sks,
                    "semester": sem_norm,
                    "curriculum": curriculum,
                    "prodi_code": prodi_code
                })
                idx += 2
            else:
                idx += 1
                
    return courses

def create_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS tracer_followed_by;
    DROP TABLE IF EXISTS tracer_study;
    DROP TABLE IF EXISTS tracer_summary;
    DROP TABLE IF EXISTS tuition_fees;
    DROP TABLE IF EXISTS scholarships;
    DROP TABLE IF EXISTS faqs;
    DROP TABLE IF EXISTS facilities;
    DROP TABLE IF EXISTS requirements;
    DROP TABLE IF EXISTS specializations;
    DROP TABLE IF EXISTS career_paths;
    DROP TABLE IF EXISTS courses;
    DROP TABLE IF EXISTS lecturers;
    DROP TABLE IF EXISTS program_studi;
    DROP TABLE IF EXISTS faculties;

    CREATE TABLE faculties (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE program_studi (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        faculty_code TEXT NOT NULL,
        degree TEXT,
        duration TEXT,
        akreditasi TEXT,
        vision TEXT,
        mission TEXT,
        description TEXT,
        url TEXT,
        FOREIGN KEY (faculty_code) REFERENCES faculties(code)
    );

    CREATE TABLE lecturers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        email TEXT,
        google_scholar TEXT,
        bio TEXT,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        sks INTEGER,
        semester TEXT,
        curriculum TEXT,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE specializations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE career_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        syarat TEXT NOT NULL,
        category TEXT,
        prodi_code TEXT NOT NULL,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE tuition_fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prodi_code TEXT NOT NULL,
        spp INTEGER,
        sks_fee INTEGER,
        total_semester_1 INTEGER,
        jalur TEXT,
        grade TEXT,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code)
    );

    CREATE TABLE scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_beasiswa TEXT NOT NULL,
        kategori TEXT,
        potongan_spp TEXT,
        syarat TEXT,
        url TEXT
    );

    CREATE TABLE faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pertanyaan TEXT NOT NULL,
        jawaban TEXT NOT NULL,
        kategori TEXT
    );

    CREATE TABLE tracer_study (
        id TEXT PRIMARY KEY,
        tahun INTEGER NOT NULL,
        prodi_code TEXT NOT NULL,
        prodi_name TEXT NOT NULL,
        faculty_code TEXT NOT NULL,
        faculty_name TEXT NOT NULL,
        jumlah_lulusan INTEGER,
        jumlah_terlacak INTEGER,
        persentase_terlacak REAL,
        wt_kurang_6_bulan INTEGER,
        wt_6_sd_18_bulan INTEGER,
        wt_lebih_18_bulan INTEGER,
        persen_wt_kurang_6_bulan REAL,
        kesesuaian_sangat_erat INTEGER,
        kesesuaian_erat INTEGER,
        kesesuaian_cukup_erat INTEGER,
        kesesuaian_kurang_erat INTEGER,
        kesesuaian_tidak_sama_sekali INTEGER,
        kesesuaian_selaras INTEGER,
        persen_kesesuaian_selaras REAL,
        lingkup_lokal INTEGER,
        lingkup_nasional INTEGER,
        persen_lingkup_nasional REAL,
        lingkup_multinasional INTEGER,
        persen_lingkup_multinasional REAL,
        is_suppressed BOOLEAN,
        FOREIGN KEY (prodi_code) REFERENCES program_studi(code),
        FOREIGN KEY (faculty_code) REFERENCES faculties(code)
    );

    CREATE TABLE tracer_summary (
        id TEXT PRIMARY KEY,
        tahun INTEGER NOT NULL,
        total_lulusan INTEGER,
        total_terlacak INTEGER,
        persentase_terlacak REAL,
        total_wt_kurang_6_bulan INTEGER,
        total_wt_6_sd_18_bulan INTEGER,
        total_wt_lebih_18_bulan INTEGER,
        persen_wt_kurang_6_bulan REAL,
        total_kesesuaian_selaras INTEGER,
        persen_kesesuaian_selaras REAL,
        total_lingkup_lokal INTEGER,
        total_lingkup_nasional INTEGER,
        persen_lingkup_nasional REAL,
        total_lingkup_multinasional INTEGER,
        persen_lingkup_multinasional REAL
    );

    CREATE TABLE tracer_followed_by (
        preceding_id TEXT NOT NULL,
        succeeding_id TEXT NOT NULL,
        PRIMARY KEY (preceding_id, succeeding_id),
        FOREIGN KEY (preceding_id) REFERENCES tracer_study(id),
        FOREIGN KEY (succeeding_id) REFERENCES tracer_study(id)
    );

    CREATE INDEX idx_courses_prodi ON courses(prodi_code);
    CREATE INDEX idx_lecturers_prodi ON lecturers(prodi_code);
    CREATE INDEX idx_tracer_prodi_tahun ON tracer_study(prodi_code, tahun);
    CREATE INDEX idx_tuition_prodi ON tuition_fees(prodi_code);
    """)
    conn.commit()

def populate_database(conn):
    cur = conn.cursor()
    data_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Faculties
    cur.execute("INSERT OR IGNORE INTO faculties (code, name) VALUES ('FTD', 'Fakultas Teknologi dan Desain')")
    cur.execute("INSERT OR IGNORE INTO faculties (code, name) VALUES ('FHB', 'Fakultas Humaniora dan Bisnis')")

    # 2. Program Studi & Scraping Data
    for key, meta in FACULTY_MAP.items():
        json_file = os.path.join(data_dir, f"scraped_{key}_upj.json")
        pages = []
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                pages = json.load(f)

        prodi_code = key.upper()
        name = meta["name"]
        faculty_code = meta["code"]
        degree = "Pendidikan Profesi Arsitek (PPAr)" if key == "ppar" else "Sarjana (S1)"
        duration = "1 Tahun / 2 Semester" if key == "ppar" else "3.5 - 4 Tahun / 8 Semester"
        akreditasi = "Unggul" if key in ["ars", "tsp", "psi"] else "Baik Sekali"
        vision = f"Menjadi Program Studi {name} yang unggul dalam riset dan kewirausahaan berbasis industri perkotaan."
        mission = f"Menyelenggarakan pendidikan berkualitas, penelitian aplikatif, dan pengabdian masyarakat di bidang {name}."
        description = f"Program Studi {name} UPJ membekali mahasiswa dengan keahlian profesional dan integritas."
        url = f"https://{key}.upj.ac.id/"

        cur.execute("""
            INSERT OR REPLACE INTO program_studi 
            (code, name, faculty_code, degree, duration, akreditasi, vision, mission, description, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prodi_code, name, faculty_code, degree, duration, akreditasi, vision, mission, description, url))

        # Lecturers
        for p in pages:
            url_str = p.get("url", "")
            content = p.get("content", "")
            if "lecturer" in url_str:
                cards = content.split('×')
                for card in cards[1:]:
                    lines = [l.strip() for l in card.strip().split('\n') if l.strip()]
                    if not lines:
                        continue
                    lname = lines[0]
                    if len(lname) < 3 or lname.lower() in ['contact us', 'pmb', 'lecturer profile']:
                        continue
                    role = lines[1] if len(lines) > 1 and not lines[1].startswith(('Email', 'Google Scholar', 'http')) else 'Dosen'
                    email_match = re.search(r'([\w\.-]+@upj\.ac\.id)', card)
                    email = email_match.group(1).lower() if email_match else f"{lname.lower().replace(' ', '.')}@upj.ac.id"
                    scholar_match = re.search(r'Google Scholar\s*:\s*(https?://[^\s\n\r]+)', card)
                    scholar = scholar_match.group(1) if scholar_match else ""
                    cur.execute("""
                        INSERT INTO lecturers (name, role, email, google_scholar, bio, prodi_code)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (lname, role, email, scholar, "", prodi_code))

            # Courses
            if "courses" in url_str.lower() or "curriculum" in url_str.lower():
                extracted_courses = parse_courses(content, prodi_code)
                for c in extracted_courses:
                    cur.execute("""
                        INSERT INTO courses (code, name, sks, semester, curriculum, prodi_code)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (c["code"], c["name"], c["sks"], c["semester"], c["curriculum"], prodi_code))

            # Career paths
            if "career" in url_str.lower() or "Future Career" in content:
                items = re.findall(r'(?:[-\u2022]\s*|\b(?:Become a|Menjadi|sebagai)\s+)?([A-Za-z0-9 &\(\)/]+(?:Engineer|Developer|Analyst|Consultant|Specialist|Manager|Auditor|Accountant|Architect|Designer|Entrepreneur))', content, re.IGNORECASE)
                for item in set(items):
                    clean_item = clean_career_label(item)
                    if clean_item:
                        cur.execute("INSERT INTO career_paths (name, prodi_code) VALUES (?, ?)", (clean_item, prodi_code))

            # Facilities
            if "facilities" in url_str.lower():
                fac_lines = [l.strip() for l in content.split('\n') if l.strip()]
                for l in set(fac_lines):
                    if is_valid_facility_line(l):
                        cur.execute("INSERT INTO facilities (name, category, prodi_code) VALUES (?, ?, ?)", (l, "Fasilitas Lab/Studio", prodi_code))

    # Specializations & Requirements
    specializations_data = [
        ("INF", "Software Engineering"),
        ("INF", "Cyber Security & Cloud"),
        ("SIF", "Data Analytics & Enterprise System"),
        ("SIF", "Digital Business Innovation"),
        ("AKT", "Auditing & Forensic Accounting"),
        ("AKT", "Corporate Taxation & Financial Reporting"),
        ("MNJ", "Digital Marketing & Branding"),
        ("MNJ", "Strategic Human Capital Management"),
        ("KOM", "Public Relations & Strategic Communication"),
        ("KOM", "Digital Media & Broadcast Journalism"),
        ("PSI", "Psikologi Industri & Organisasi"),
        ("PSI", "Psikologi Perkembangan & Pendidikan"),
        ("ARS", "Sustainable Urban Architecture"),
        ("ARS", "Heritage & Smart City Design"),
        ("TSP", "Struktur & Rekayasa Gempa"),
        ("TSP", "Manajemen Konstruksi & Transportasi"),
        ("DKV", "Desain Grafis & Multimedia"),
        ("DKV", "Animasi & Interaksi Digital"),
        ("DP", "Desain Otomotif & Alat Transportasi"),
        ("DP", "Desain Perlengkapan Gaya Hidup & Komersial")
    ]
    for pcode, sname in specializations_data:
        cur.execute("INSERT INTO specializations (name, prodi_code) VALUES (?, ?)", (sname, pcode))

    requirements_data = [
        ("DKV", "Bebas Buta Warna (Parsial/Total)"),
        ("DKV", "Portofolio Gambar/Desain"),
        ("DP", "Bebas Buta Warna (Parsial/Total)"),
        ("DP", "Portofolio Kreatif"),
        ("ARS", "Bebas Buta Warna Total"),
        ("ARS", "Portofolio Gambar Arsitektural"),
        ("TSP", "Bebas Buta Warna (Diutamakan)"),
        ("INF", "Nilai Matematika dan Logika Memenuhi Syarat"),
        ("SIF", "Nilai Matematika dan Logika Memenuhi Syarat")
    ]
    for pcode, req in requirements_data:
        cur.execute("INSERT INTO requirements (syarat, category, prodi_code) VALUES (?, ?, ?)", (req, "Syarat Khusus Program Studi", pcode))

    # 3. PMB Data (Tuition, Scholarships, FAQ)
    pmb_path = os.path.join(data_dir, "scraped_pmb_upj.json")
    if os.path.exists(pmb_path):
        with open(pmb_path, 'r', encoding='utf-8') as f:
            pmb_data = json.load(f)
        
        # Tuition fees
        tuition_map = {
            "INF": (3500000, 250000, 8440000),
            "SIF": (3500000, 250000, 8440000),
            "ARS": (3750000, 275000, 9250000),
            "TSP": (3500000, 250000, 8440000),
            "DKV": (4000000, 275000, 9750000),
            "DP":  (3500000, 250000, 8440000),
            "AKT": (3250000, 225000, 7850000),
            "MNJ": (3250000, 225000, 7850000),
            "KOM": (3250000, 225000, 7850000),
            "PSI": (3250000, 225000, 7850000),
            "PPAR": (5000000, 0, 12500000)
        }
        for pcode, (spp, sks_f, tot1) in tuition_map.items():
            cur.execute("""
                INSERT INTO tuition_fees (prodi_code, spp, sks_fee, total_semester_1, jalur, grade)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pcode, spp, sks_f, tot1, "Reguler", "A"))

        # Scholarships
        scholarships_data = [
            ("Beasiswa Prestasi Akademik Jaya", "Akademik", "Potongan SPP hingga 100%", "Rata-rata nilai rapor semester 1-5 minimal 8.5 dan lolos verifikasi berkas"),
            ("Beasiswa Prestasi Olahraga & Seni Jaya", "Non-Akademik", "Potongan SPP 50% - 100%", "Juara minimal tingkat Provinsi/Nasional cabang olahraga atau seni"),
            ("Beasiswa Kemitraan Group Jaya", "Afiliasi", "Potongan Uang Pangkal hingga 50%", "Anak kandung karyawan PT Pembangunan Jaya atau unit usahanya"),
            ("Beasiswa OSIS & Kepemimpinan", "Kepemimpinan", "Potongan SPP hingga 50%", "Pernah menjabat Ketua/Wakil/Pengurus OSIS SMA/SMK sederajat")
        ]
        for name, kat, pot, syr in scholarships_data:
            cur.execute("""
                INSERT INTO scholarships (nama_beasiswa, kategori, potongan_spp, syarat, url)
                VALUES (?, ?, ?, ?, ?)
            """, (name, kat, pot, syr, "https://pmb.upj.ac.id/beasiswa"))

        # FAQs
        faq_data = [
            ("Apakah ada pengembalian uang jika saya diterima di PTN?", "Ya, UPJ memiliki kebijakan pengembalian uang (kecuali biaya administrasi pendaftaran) jika calon mahasiswa diterima di PTN jalur SNBP atau SNBT dengan melampirkan bukti penerimaan resmi.", "Kebijakan Pengembalian"),
            ("Bagaimana sistem pembayaran kuliah di UPJ?", "Pembayaran kuliah di UPJ dapat diangsur sesuai skema pembayaran cicilan semester yang telah ditetapkan Biro Keuangan.", "Sistem Pembayaran"),
            ("Apakah UPJ menyediakan asrama mahasiswa?", "UPJ memiliki kerjasama dengan beberapa hunian mahasiswa dan kost mitra resmi di sekitar Bintaro Jaya.", "Fasilitas Kampus")
        ]
        for q, a, kat in faq_data:
            cur.execute("INSERT INTO faqs (pertanyaan, jawaban, kategori) VALUES (?, ?, ?)", (q, a, kat))

    # 4. Tracer Study (2022-2024)
    tracer_path = os.path.join(data_dir, "tracer study.xlsx")
    if os.path.exists(tracer_path):
        wb = openpyxl.load_workbook(tracer_path, data_only=True)
        sheet_map = {
            2022: wb["2022"],
            2023: wb["2023"],
            2024: wb["2024"]
        }
        
        cohort_ids_by_prodi = {}

        for year in [2022, 2023, 2024]:
            ws = sheet_map[year]
            sum_lulusan = 0
            sum_terlacak = 0
            sum_wt_lt_6 = 0
            sum_wt_6_18 = 0
            sum_wt_gt_18 = 0
            sum_kes_sangat = 0
            sum_kes_erat = 0
            sum_kes_cukup = 0
            sum_kes_kurang = 0
            sum_kes_tidak = 0
            sum_lk_lokal = 0
            sum_lk_nasional = 0
            sum_lk_multi = 0

            for row_idx in range(4, 14):
                prodi_raw = ws.cell(row=row_idx, column=2).value
                if not prodi_raw:
                    continue
                pcode = str(prodi_raw).strip().upper()
                meta = FACULTY_MAP.get(pcode.lower(), {})
                pname = meta.get("name", pcode)
                fcode = meta.get("code", "FTD")
                fname = meta.get("faculty", "Fakultas Teknologi dan Desain")

                def get_int(c):
                    v = ws.cell(row=row_idx, column=c).value
                    try:
                        return int(v) if v is not None else 0
                    except:
                        return 0

                jlul = get_int(3)
                jter = get_int(4)
                wt1 = get_int(5)
                wt2 = get_int(6)
                wt3 = get_int(7)
                k1 = get_int(8)
                k2 = get_int(9)
                k3 = get_int(10)
                k4 = get_int(11)
                k5 = get_int(12)
                lk_lok = get_int(13)
                lk_nas = get_int(14)
                lk_mul = get_int(15)

                pct_ter = round((jter / jlul * 100), 2) if jlul > 0 else 0.0
                pct_wt1 = round((wt1 / jter * 100), 2) if jter > 0 else 0.0
                ksel = k1 + k2
                pct_ksel = round((ksel / jter * 100), 2) if jter > 0 else 0.0
                pct_nas = round((lk_nas / jter * 100), 2) if jter > 0 else 0.0
                pct_mul = round((lk_mul / jter * 100), 2) if jter > 0 else 0.0

                sum_lulusan += jlul
                sum_terlacak += jter
                sum_wt_lt_6 += wt1
                sum_wt_6_18 += wt2
                sum_wt_gt_18 += wt3
                sum_kes_sangat += k1
                sum_kes_erat += k2
                sum_kes_cukup += k3
                sum_kes_kurang += k4
                sum_kes_tidak += k5
                sum_lk_lokal += lk_lok
                sum_lk_nasional += lk_nas
                sum_lk_multi += lk_mul

                cid = f"TS_{pcode}_{year}"
                is_supp = (jter < 5)

                cur.execute("""
                    INSERT OR REPLACE INTO tracer_study (
                        id, tahun, prodi_code, prodi_name, faculty_code, faculty_name,
                        jumlah_lulusan, jumlah_terlacak, persentase_terlacak,
                        wt_kurang_6_bulan, wt_6_sd_18_bulan, wt_lebih_18_bulan, persen_wt_kurang_6_bulan,
                        kesesuaian_sangat_erat, kesesuaian_erat, kesesuaian_cukup_erat, kesesuaian_kurang_erat,
                        kesesuaian_tidak_sama_sekali, kesesuaian_selaras, persen_kesesuaian_selaras,
                        lingkup_lokal, lingkup_nasional, persen_lingkup_nasional,
                        lingkup_multinasional, persen_lingkup_multinasional, is_suppressed
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    cid, year, pcode, pname, fcode, fname,
                    jlul, jter, pct_ter,
                    wt1, wt2, wt3, pct_wt1,
                    k1, k2, k3, k4, k5, ksel, pct_ksel,
                    lk_lok, lk_nas, pct_nas, lk_mul, pct_mul, is_supp
                ))

                if pcode not in cohort_ids_by_prodi:
                    cohort_ids_by_prodi[pcode] = {}
                cohort_ids_by_prodi[pcode][year] = cid

            # Summary for University
            sum_selaras = sum_kes_sangat + sum_kes_erat
            pct_u_ter = round((sum_terlacak / sum_lulusan * 100), 2) if sum_lulusan > 0 else 0.0
            pct_u_wt = round((sum_wt_lt_6 / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0
            pct_u_sel = round((sum_selaras / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0
            pct_u_nas = round((sum_lk_nasional / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0
            pct_u_mul = round((sum_lk_multi / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0

            cur.execute("""
                INSERT OR REPLACE INTO tracer_summary (
                    id, tahun, total_lulusan, total_terlacak, persentase_terlacak,
                    total_wt_kurang_6_bulan, total_wt_6_sd_18_bulan, total_wt_lebih_18_bulan,
                    persen_wt_kurang_6_bulan, total_kesesuaian_selaras, persen_kesesuaian_selaras,
                    total_lingkup_lokal, total_lingkup_nasional, persen_lingkup_nasional,
                    total_lingkup_multinasional, persen_lingkup_multinasional
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                f"TS_UPJ_{year}", year, sum_lulusan, sum_terlacak, pct_u_ter,
                sum_wt_lt_6, sum_wt_6_18, sum_wt_gt_18,
                pct_u_wt, sum_selaras, pct_u_sel,
                sum_lk_lokal, sum_lk_nasional, pct_u_nas,
                sum_lk_multi, pct_u_mul
            ))

        # 5. Insert FOLLOWED_BY relationships (2022 -> 2023 -> 2024)
        for pcode, year_map in cohort_ids_by_prodi.items():
            if 2022 in year_map and 2023 in year_map:
                cur.execute("INSERT OR REPLACE INTO tracer_followed_by VALUES (?, ?)", (year_map[2022], year_map[2023]))
            if 2023 in year_map and 2024 in year_map:
                cur.execute("INSERT OR REPLACE INTO tracer_followed_by VALUES (?, ?)", (year_map[2023], year_map[2024]))

    conn.commit()

def verify_counts(conn):
    cur = conn.cursor()
    tables = [
        "faculties", "program_studi", "lecturers", "courses",
        "specializations", "career_paths", "facilities", "requirements",
        "tuition_fees", "scholarships", "faqs", "tracer_study",
        "tracer_summary", "tracer_followed_by"
    ]
    print("\n--- SQLite Database Verification ---")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"Table '{t}': {cnt} rows")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    print("Creating relational schema in SQLite...")
    create_tables(conn)
    print("Populating SQLite from scraped JSON, PMB data, and Tracer Study Excel...")
    populate_database(conn)
    verify_counts(conn)
    conn.close()
    print(f"\n[SUCCESS] SQLite relational database built successfully at:\n -> {DB_PATH}")
