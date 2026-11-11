import os
import re
import json
import glob
import time
import logging
import argparse
from datetime import datetime, timezone
from urllib.parse import urlparse
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None
try:
    import openpyxl
except ImportError:
    openpyxl = None

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etl_sync.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("upj_kg_etl")

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

def parse_lecturers(content, prodi_code):
    lecturers = []
    cards = content.split('×')
    for card in cards[1:]:
        lines = [l.strip() for l in card.strip().split('\n') if l.strip()]
        if not lines:
            continue
        
        name = lines[0]
        if len(name) < 3 or name.lower() in ['contact us', 'pmb', 'lecturer profile']:
            continue
            
        role = lines[1] if len(lines) > 1 and not lines[1].startswith(('Email', 'Google Scholar', 'http')) else 'Dosen'
        
        email_match = re.search(r'([\w\.-]+@upj\.ac\.id)', card)
        email = email_match.group(1).lower() if email_match else f"{name.lower().replace(' ', '.')}@upj.ac.id"
        
        scholar_match = re.search(r'Google Scholar\s*:\s*(https?://[^\s\n\r]+)', card)
        scholar = scholar_match.group(1) if scholar_match else ""
        
        bio_lines = []
        for line in lines[2:]:
            if line.startswith(('Email', 'Google Scholar', 'http', '×', '«', '»')):
                continue
            bio_lines.append(line)
        bio = "\n".join(bio_lines).strip()
        
        lecturers.append({
            "name": name,
            "role": role,
            "email": email,
            "google_scholar": scholar,
            "bio": bio,
            "prodi_code": prodi_code
        })
    return lecturers

def parse_courses(content, prodi_code):
    courses = []
    sem_pattern = r'((?:Semester\s+\d+)|(?:\d+(?:st|nd|rd|th)\s+Semester)|(?:MKP\s*–\s*\d+)|(?:Elective\s+Courses?))'
    parts = re.split(sem_pattern, content, flags=re.IGNORECASE)
    
    current_sem = "General"
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

def clean_career_label(raw_item):
    """Normalizes regex-extracted career strings by stripping sentence fragments."""
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
    """Filters pagination counters, page headers, and news/event headlines from scraped facilities."""
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

def resolve_prodi_codes(prodi_label):
    """Maps PMB labels like 'Desain Komunikasi Visual (DKV)' or 'Informatika & Sistem Informasi' to codes."""
    if not prodi_label:
        return []
    low = prodi_label.lower()
    if 'semua prodi' in low:
        return [k.upper() for k in FACULTY_MAP.keys()]
    matched = []
    for code, meta in FACULTY_MAP.items():
        if meta["name"].lower() in low or re.search(rf'\b{re.escape(code)}\b', low):
            matched.append(code.upper())
    return sorted(set(matched))

def parse_prodi_details(pages, prodi_key, anonymize_alumni=True):
    info = FACULTY_MAP.get(prodi_key, {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": prodi_key.upper()})
    prodi_data = {
        "code": prodi_key.upper(),
        "name": info["name"],
        "faculty": info["faculty"],
        "faculty_code": info["code"],
        "degree": "Professional Architect Education (PPAr)" if prodi_key == "ppar" else "",
        "duration": "3.5 Years / 7 Semester",
        "vision": "",
        "mission": "",
        "description": "",
        "akreditasi": "Baik Sekali",
        "url": f"https://{prodi_key}.upj.ac.id/",
        "career_paths": [],
        "facilities": [],
        "alumni": []
    }

    seen_careers_low = set()
    seen_alumni = set()
    for p in pages:
        content = p.get("content", "")
        url = p.get("url", "")

        if prodi_key != "ppar":
            degree_match = re.search(r'(Bachelor of [A-Za-z &]+(?:\([A-Za-z\.]+\))?)', content)
            if degree_match and not prodi_data["degree"] and len(degree_match.group(1).strip()) <= 80:
                prodi_data["degree"] = degree_match.group(1).strip()

        dur_match = re.search(r'(\d+(?:\.\d+)?\s*(?:Years|Tahun)\s*/\s*\d+\s*(?:Semester|Semesters))', content)
        if dur_match:
            prodi_data["duration"] = dur_match.group(1).strip()

        if url.rstrip('/') == f"https://{prodi_key}.upj.ac.id" or url.endswith(f"{prodi_key}.upj.ac.id/"):
            desc_match = re.search(r'(?:The \w+ Department[^\n]+See More\s*)([^\n]+)', content)
            if desc_match:
                prodi_data["description"] = desc_match.group(1).strip()

        if 'profile' in url or 'static-page' in url:
            if "Vision" in content and "Mision" in content:
                vis_match = re.search(r'Vision\s*\n+([^\n]+)', content)
                if vis_match:
                    prodi_data["vision"] = vis_match.group(1).strip()
                mis_match = re.search(r'Mision\s*\n+([\s\S]+?)(?:Objective|Strategy|Targets|Contact Us|$)', content)
                if mis_match:
                    prodi_data["mission"] = mis_match.group(1).strip()

        if "Future Career" in content or "Karir masa depan" in content or "Career Prospects" in content:
            career_sec = re.search(r'(?:Future Career|Karir masa depan|Career Prospects)[^\n]*\n([\s\S]+?)(?:Alumni|Cerita Alumni|Join|Contact Us|\u00ab|$)', content)
            if career_sec:
                sec_text = career_sec.group(1)
                items = re.findall(r'(?:[-\u2022]\s*|\b(?:Become a|Menjadi|sebagai)\s+)?([A-Za-z0-9 &\(\)/]+(?:Engineer|Developer|Analyst|Consultant|Specialist|Manager|Auditor|Accountant|Architect|Designer|Entrepreneur))', sec_text, re.IGNORECASE)
                for item in items:
                    clean_item = clean_career_label(item)
                    if clean_item and clean_item.lower() not in seen_careers_low:
                        seen_careers_low.add(clean_item.lower())
                        prodi_data["career_paths"].append(clean_item)

        if 'facilities' in url:
            fac_lines = [l.strip() for l in content.split('\n') if l.strip()]
            for l in fac_lines:
                if not is_valid_facility_line(l):
                    continue
                if l not in prodi_data["facilities"]:
                    prodi_data["facilities"].append(l)

        if "Alumni Testimonials" in content or "Cerita Alumni" in content or "Alumni Stories" in content:
            alumni_sec = re.search(r'(?:Alumni Testimonials|Cerita Alumni|Alumni Stories)\n([\s\S]+?)(?:Contact Us|PMB|\u00ab|$)', content)
            if alumni_sec:
                a_text = alumni_sec.group(1)
                a_matches = re.findall(r'([A-Z][a-zA-Z\s]+,\s*S\.[A-Za-z\.]+)\n+([^\n]+)', a_text)
                for raw_name, role in a_matches:
                    norm_name = clean_text(raw_name.replace("\n", " "))
                    norm_role = clean_text(role)
                    if re.search(r',\s*(?:S|M|Dr|Ir)\.[A-Za-z\.]+$', norm_role) or norm_role.lower() == norm_name.lower():
                        norm_role = "Alumni Program Studi"
                    dedup_key = (norm_name.lower(), norm_role.lower())
                    if dedup_key in seen_alumni:
                        continue
                    seen_alumni.add(dedup_key)
                    if anonymize_alumni:
                        anon_id = f"Alumni_{prodi_key.upper()}_{len(prodi_data['alumni']) + 1:02d}"
                        prodi_data["alumni"].append({"name": anon_id, "role": norm_role})
                    else:
                        prodi_data["alumni"].append({"name": norm_name, "role": norm_role})

    return prodi_data

def parse_tracer_study(file_path):
    """
    Parses UPJ Tracer Study Excel file (data/tracer study.xlsx).
    Extracts data per cohort year (2022, 2023, 2024) across Program Studi,
    including:
    - Jumlah Lulusan & Terlacak
    - Waktu Tunggu (< 6 bulan, 6-18 bulan, > 18 bulan)
    - Kesesuaian Bidang Kerja (Sangat Erat, Erat, Cukup Erat, Kurang Erat, Tidak Sama Sekali)
    - Lingkup Tempat Kerja (Lokal, Nasional, Multinasional)
    Computes percentage metrics and university-wide summaries.
    """
    if not os.path.exists(file_path):
        print(f"Tracer study file not found: {file_path}")
        return {"cohorts": [], "summaries": []}

    if not openpyxl:
        print("Warning: openpyxl not installed. Cannot parse tracer study.")
        return {"cohorts": [], "summaries": []}

    wb = openpyxl.load_workbook(file_path, data_only=True)
    cohorts_by_year = {}
    summaries = []

    for sheet_name in wb.sheetnames:
        sheet_clean = sheet_name.strip()
        try:
            year = int(sheet_clean)
        except ValueError:
            continue

        ws = wb[sheet_name]
        cohorts_by_year[year] = []

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
            prodi_code = str(prodi_raw).strip().upper()
            prodi_meta = FACULTY_MAP.get(prodi_code.lower(), {})
            prodi_name = prodi_meta.get("name", prodi_code)
            faculty_name = prodi_meta.get("faculty", "")
            faculty_code = prodi_meta.get("code", "")

            def to_int(val):
                if val is None or val == "":
                    return 0
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0

            jml_lulusan = to_int(ws.cell(row=row_idx, column=3).value)
            jml_terlacak = to_int(ws.cell(row=row_idx, column=4).value)
            wt_lt_6 = to_int(ws.cell(row=row_idx, column=5).value)
            wt_6_18 = to_int(ws.cell(row=row_idx, column=6).value)
            wt_gt_18 = to_int(ws.cell(row=row_idx, column=7).value)

            kes_sangat = to_int(ws.cell(row=row_idx, column=8).value)
            kes_erat = to_int(ws.cell(row=row_idx, column=9).value)
            kes_cukup = to_int(ws.cell(row=row_idx, column=10).value)
            kes_kurang = to_int(ws.cell(row=row_idx, column=11).value)
            kes_tidak = to_int(ws.cell(row=row_idx, column=12).value)

            lk_lokal = to_int(ws.cell(row=row_idx, column=13).value)
            lk_nasional = to_int(ws.cell(row=row_idx, column=14).value)
            lk_multi = to_int(ws.cell(row=row_idx, column=15).value)

            pct_terlacak = round((jml_terlacak / jml_lulusan * 100), 2) if jml_lulusan > 0 else 0.0
            pct_wt_lt_6 = round((wt_lt_6 / jml_terlacak * 100), 2) if jml_terlacak > 0 else 0.0
            kes_selaras = kes_sangat + kes_erat
            pct_kes_selaras = round((kes_selaras / jml_terlacak * 100), 2) if jml_terlacak > 0 else 0.0
            pct_multi = round((lk_multi / jml_terlacak * 100), 2) if jml_terlacak > 0 else 0.0
            pct_nasional = round((lk_nasional / jml_terlacak * 100), 2) if jml_terlacak > 0 else 0.0

            sum_lulusan += jml_lulusan
            sum_terlacak += jml_terlacak
            sum_wt_lt_6 += wt_lt_6
            sum_wt_6_18 += wt_6_18
            sum_wt_gt_18 += wt_gt_18
            sum_kes_sangat += kes_sangat
            sum_kes_erat += kes_erat
            sum_kes_cukup += kes_cukup
            sum_kes_kurang += kes_kurang
            sum_kes_tidak += kes_tidak
            sum_lk_lokal += lk_lokal
            sum_lk_nasional += lk_nasional
            sum_lk_multi += lk_multi

            cohorts_by_year[year].append({
                "id": f"TS_{prodi_code}_{year}",
                "tahun": year,
                "prodi_code": prodi_code,
                "prodi_name": prodi_name,
                "faculty_code": faculty_code,
                "faculty_name": faculty_name,
                "jumlah_lulusan": jml_lulusan,
                "jumlah_terlacak": jml_terlacak,
                "persentase_terlacak": pct_terlacak,
                "wt_kurang_6_bulan": wt_lt_6,
                "wt_6_sd_18_bulan": wt_6_18,
                "wt_lebih_18_bulan": wt_gt_18,
                "persen_wt_kurang_6_bulan": pct_wt_lt_6,
                "kesesuaian_sangat_erat": kes_sangat,
                "kesesuaian_erat": kes_erat,
                "kesesuaian_cukup_erat": kes_cukup,
                "kesesuaian_kurang_erat": kes_kurang,
                "kesesuaian_tidak_sama_sekali": kes_tidak,
                "kesesuaian_selaras": kes_selaras,
                "persen_kesesuaian_selaras": pct_kes_selaras,
                "lingkup_lokal": lk_lokal,
                "lingkup_nasional": lk_nasional,
                "persen_lingkup_nasional": pct_nasional,
                "lingkup_multinasional": lk_multi,
                "persen_lingkup_multinasional": pct_multi,
                "is_suppressed": jml_terlacak < 5,
                "suppress_wt_lt_6": 0 < wt_lt_6 < 5,
                "suppress_selaras": 0 < kes_selaras < 5,
                "suppress_nasional": 0 < lk_nasional < 5,
                "suppress_multinasional": 0 < lk_multi < 5
            })

        summary_selaras = sum_kes_sangat + sum_kes_erat
        pct_u_multi = round((sum_lk_multi / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0
        pct_u_nasional = round((sum_lk_nasional / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0
        summaries.append({
            "id": f"TS_UPJ_{year}",
            "tahun": year,
            "total_lulusan": sum_lulusan,
            "total_terlacak": sum_terlacak,
            "persentase_terlacak": round((sum_terlacak / sum_lulusan * 100), 2) if sum_lulusan > 0 else 0.0,
            "total_wt_kurang_6_bulan": sum_wt_lt_6,
            "total_wt_6_sd_18_bulan": sum_wt_6_18,
            "total_wt_lebih_18_bulan": sum_wt_gt_18,
            "persen_wt_kurang_6_bulan": round((sum_wt_lt_6 / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0,
            "total_kesesuaian_sangat_erat": sum_kes_sangat,
            "total_kesesuaian_erat": sum_kes_erat,
            "total_kesesuaian_cukup_erat": sum_kes_cukup,
            "total_kesesuaian_kurang_erat": sum_kes_kurang,
            "total_kesesuaian_tidak_sama_sekali": sum_kes_tidak,
            "total_kesesuaian_selaras": summary_selaras,
            "persen_kesesuaian_selaras": round((summary_selaras / sum_terlacak * 100), 2) if sum_terlacak > 0 else 0.0,
            "total_lingkup_lokal": sum_lk_lokal,
            "total_lingkup_nasional": sum_lk_nasional,
            "persen_lingkup_nasional": pct_u_nasional,
            "total_lingkup_multinasional": sum_lk_multi,
            "persen_lingkup_multinasional": pct_u_multi
        })

    all_cohorts = []
    sorted_years = sorted(cohorts_by_year.keys())
    for y in sorted_years:
        all_cohorts.extend(cohorts_by_year[y])
    summaries = sorted(summaries, key=lambda s: s["tahun"])

    return {
        "cohorts": all_cohorts,
        "summaries": summaries
    }

def extract_all_data(data_dir=".", anonymize_alumni=True):
    candidate_dirs = [data_dir, os.path.join(data_dir, "data"), "data", "."]
    actual_dir = data_dir
    files = []
    for cd in candidate_dirs:
        found = sorted(glob.glob(os.path.join(cd, "scraped_*_upj.json")))
        if found:
            actual_dir = cd
            files = found
            break

    all_prodi = []
    all_lecturers = []
    all_courses = []
    all_pages = []
    
    # Load PMB data if available
    pmb_data = {}
    pmb_candidates = [
        os.path.join(actual_dir, "scraped_pmb_upj.json"),
        os.path.join("data", "scraped_pmb_upj.json"),
        "scraped_pmb_upj.json"
    ]
    for pmb_path in pmb_candidates:
        if os.path.exists(pmb_path):
            try:
                with open(pmb_path, "r", encoding="utf-8") as f:
                    pmb_data = json.load(f)
                break
            except Exception as e:
                print(f"Error loading PMB data: {e}")
            
    for f in files:
        base = os.path.basename(f)
        if base == "scraped_pmb_upj.json":
            continue
        m = re.search(r'scraped_([a-zA-Z]+)_upj\.json', base)
        if not m:
            continue
        key = m.group(1).lower()
        prodi_code = key.upper()
        
        with open(f, 'r', encoding='utf-8') as fp:
            pages = json.load(fp)
            
        prodi_info = parse_prodi_details(pages, key, anonymize_alumni=anonymize_alumni)
        all_prodi.append(prodi_info)
        
        for p in pages:
            url = p.get("url", "")
            title = p.get("title", "")
            content = p.get("content", "")
            
            if content and "404 Not Found" not in title:
                snippet = content[:500].replace('\n', ' ')
                all_pages.append({
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "prodi_code": prodi_code
                })
                
            if "lecturer-profile" in url:
                all_lecturers.extend(parse_lecturers(content, prodi_code))
            if "courses" in url:
                all_courses.extend(parse_courses(content, prodi_code))

    # Enrich facilities from official PMB laboratorium metadata so no S1 prodi has empty facilities
    if pmb_data and pmb_data.get("fasilitas_laboratorium"):
        prodi_by_code = {p["code"]: p for p in all_prodi}
        for fac in pmb_data["fasilitas_laboratorium"]:
            fac_name = fac.get("nama", "").strip()
            if not fac_name:
                continue
            for p_code in resolve_prodi_codes(fac.get("prodi", "")):
                if p_code in prodi_by_code and fac_name not in prodi_by_code[p_code]["facilities"]:
                    prodi_by_code[p_code]["facilities"].append(fac_name)

    # Load Tracer Study if available
    tracer_candidates = [
        os.path.join(actual_dir, "tracer study.xlsx"),
        os.path.join("data", "tracer study.xlsx"),
        "tracer study.xlsx"
    ]
    tracer_data = {"cohorts": [], "summaries": []}
    for t_path in tracer_candidates:
        if os.path.exists(t_path):
            print(f"Parsing Tracer Study from {t_path}...")
            tracer_data = parse_tracer_study(t_path)
            break
                
    return {
        "prodi": all_prodi,
        "lecturers": all_lecturers,
        "courses": all_courses,
        "pages": all_pages,
        "pmb": pmb_data,
        "tracer_study": tracer_data
    }

def populate_neo4j(data, uri="bolt://localhost:7687", user="neo4j", password="password123"):
    if not GraphDatabase:
        raise RuntimeError("neo4j python package not installed. Run 'pip install neo4j'")
        
    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    connected = False
    for attempt in range(1, 21):
        try:
            driver.verify_connectivity()
            connected = True
            print("Successfully connected to Neo4j!")
            break
        except Exception as e:
            print(f"Waiting for Neo4j to finish booting (attempt {attempt}/20)...")
            time.sleep(3)

    if not connected:
        raise RuntimeError(f"Could not connect to Neo4j at {uri} after 60s. Please check 'docker logs neo4j'")

    with driver.session() as session:
        print("Creating constraints and indexes...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:University) REQUIRE u.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Faculty) REQUIRE f.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:ProgramStudi) REQUIRE p.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Lecturer) REQUIRE l.email IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (w:WebPage) REQUIRE w.url IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Beasiswa) REQUIRE b.nama IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ts:TracerStudy) REQUIRE ts.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:TracerSummary) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (lk:LingkupKerja) REQUIRE lk.kategori IS UNIQUE"
        ]
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                print(f"Constraint notice: {e}")
                
        snapshot_version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        pmb_meta = data.get("pmb", {})
        potongan_json = json.dumps(pmb_meta.get("biaya_kuliah", {}).get("potongan_uang_masuk", []), ensure_ascii=False)
        jalur_summary = json.dumps([
            {"title": j.get("title", ""), "persyaratan": j.get("persyaratan", [])}
            for j in pmb_meta.get("jalur_pendaftaran", [])
        ], ensure_ascii=False)

        # University & Faculties
        logger.info("Ingesting University and Faculties (snapshot %s)...", snapshot_version)
        session.run("""
        MERGE (u:University {code: 'UPJ'})
        SET u.name = 'Universitas Pembangunan Jaya',
            u.website = 'https://upj.ac.id',
            u.pmb_website = 'https://pmb.upj.ac.id',
            u.living_lab = 'Grup Pembangunan Jaya (17 unit usaha)',
            u.tagline = 'Mendidik Manusia Jaya yang Berintegritas, Profesional, dan Berjiwa Entrepreneur',
            u.snapshot_version = $snapshot_version,
            u.potongan_uang_masuk_json = $potongan_json,
            u.jalur_pendaftaran_json = $jalur_summary
        MERGE (ftd:Faculty {code: 'FTD'})
        ON CREATE SET ftd.name = 'Fakultas Teknologi dan Desain'
        MERGE (fhb:Faculty {code: 'FHB'})
        ON CREATE SET fhb.name = 'Fakultas Humaniora dan Bisnis'
        MERGE (u)-[:HAS_FACULTY]->(ftd)
        MERGE (u)-[:HAS_FACULTY]->(fhb)
        """, {
            "snapshot_version": snapshot_version,
            "potongan_json": potongan_json,
            "jalur_summary": jalur_summary
        })
        
        # Ingest Program Studi
        print(f"Ingesting {len(data['prodi'])} Program Studi...")
        for p in data["prodi"]:
            session.run("""
            MATCH (f:Faculty {code: $faculty_code})
            MERGE (prodi:ProgramStudi {code: $code})
            SET prodi.name = $name,
                prodi.degree = $degree,
                prodi.duration = $duration,
                prodi.vision = $vision,
                prodi.mission = $mission,
                prodi.description = $description,
                prodi.akreditasi = $akreditasi,
                prodi.url = $url
            MERGE (f)-[:OFFERS_PROGRAM]->(prodi)
            """, p)
            
            for c_name in p["career_paths"]:
                session.run("""
                MATCH (prodi:ProgramStudi {code: $code})
                MERGE (car:CareerPath {name: $c_name})
                MERGE (prodi)-[:LEADS_TO_CAREER]->(car)
                """, {"code": p["code"], "c_name": c_name})
                
            for fac in p["facilities"]:
                session.run("""
                MATCH (prodi:ProgramStudi {code: $code})
                MERGE (facility:Facility {name: $fac})
                MERGE (prodi)-[:HAS_FACILITY]->(facility)
                """, {"code": p["code"], "fac": fac})
                
            for al in p["alumni"]:
                session.run("""
                MATCH (prodi:ProgramStudi {code: $code})
                MERGE (alm:Alumni {name: $name})
                SET alm.role = $role
                MERGE (alm)-[:ALUMNI_OF]->(prodi)
                """, {"code": p["code"], "name": al["name"], "role": al["role"]})
                
        # Ingest Lecturers
        print(f"Ingesting {len(data['lecturers'])} Lecturers...")
        for l in data["lecturers"]:
            session.run("""
            MATCH (prodi:ProgramStudi {code: $prodi_code})
            MERGE (lect:Lecturer {email: $email})
            SET lect.name = $name,
                lect.role = $role,
                lect.google_scholar = $google_scholar,
                lect.bio = $bio
            MERGE (lect)-[:TEACHES_IN]->(prodi)
            """, l)
            
        # Ingest Courses
        print(f"Ingesting {len(data['courses'])} Courses...")
        session.run("""
        UNWIND $courses AS c
        MATCH (prodi:ProgramStudi {code: c.prodi_code})
        MERGE (course:Course {name: c.name, semester: c.semester, prodi_code: c.prodi_code})
        SET course.sks = c.sks,
            course.curriculum = c.curriculum,
            course.code = c.code
        MERGE (prodi)-[:OFFERS_COURSE]->(course)
        """, {"courses": data["courses"]})
        
        # Ingest PMB: Biaya Kuliah, Beasiswa, Peminatan, Syarat Khusus, FAQ
        pmb = data.get("pmb", {})
        if pmb:
            print("Ingesting PMB Tuition Fees & Scholarships...")
            # Biaya SPP & SKS per prodi (matched by resolved prodi codes)
            biaya_list = pmb.get("biaya_kuliah", {}).get("tabel_spp_sks_semester_1", [])
            for bk in biaya_list:
                if not isinstance(bk, dict) or not bk.get("prodi"):
                    continue
                for p_code in resolve_prodi_codes(bk.get("prodi", "")):
                    session.run("""
                    MATCH (prodi:ProgramStudi {code: $p_code})
                    MERGE (b:BiayaKuliah {prodi: $p_name})
                    SET b.spp = $spp,
                        b.sks_kelas = $sks_kelas,
                        b.sks_praktik = $sks_praktik,
                        b.total_semester_1 = $total_sem_1
                    MERGE (prodi)-[:HAS_TUITION_FEE]->(b)
                    """, {
                        "p_code":      p_code,
                        "p_name":      bk.get("prodi", ""),
                        "spp":         bk.get("spp", ""),
                        "sks_kelas":   bk.get("sks_kelas", ""),
                        "sks_praktik": bk.get("sks_praktik", ""),
                        "total_sem_1": bk.get("total_sem_1", "")
                    })
                
            # Beasiswa
            for b in pmb.get("beasiswa", []):
                if not isinstance(b, dict) or not b.get("nama"):
                    continue
                session.run("""
                MATCH (u:University {code: 'UPJ'})
                MERGE (bs:Beasiswa {nama: $nama})
                SET bs.syarat = $syarat
                MERGE (u)-[:OFFERS_SCHOLARSHIP]->(bs)
                """, {"nama": b.get("nama", ""), "syarat": b.get("syarat", "")})
                
            # Peminatan / Konsentrasi (fixes DKV/DP suffix mismatch)
            for pem in pmb.get("peminatan_konsentrasi", []):
                p_name = pem.get("prodi", "")
                for p_code in resolve_prodi_codes(p_name):
                    for p_item in pem.get("peminatan", []):
                        if not isinstance(p_item, str) or not p_item.strip():
                            continue
                        session.run("""
                        MATCH (prodi:ProgramStudi {code: $p_code})
                        MERGE (sp:Peminatan {name: $p_item, prodi_code: prodi.code})
                        SET sp.waktu_pemilihan = $waktu
                        MERGE (prodi)-[:HAS_SPECIALIZATION]->(sp)
                        """, {"p_code": p_code, "p_item": p_item.strip(), "waktu": pem.get("waktu_pemilihan", "Semester 5")})
                    
            # Syarat Khusus Masuk (fixes DKV, DP, and combined 'Informatika & Sistem Informasi')
            for sk in pmb.get("syarat_khusus_prodi", []):
                if not isinstance(sk, dict) or not sk.get("prodi"):
                    continue
                for p_code in resolve_prodi_codes(sk.get("prodi", "")):
                    session.run("""
                    MATCH (prodi:ProgramStudi {code: $p_code})
                    MERGE (req:SyaratKhusus {prodi: $p_name})
                    SET req.syarat_khusus = $syarat_khusus,
                        req.latar_belakang = $latar_belakang
                    MERGE (prodi)-[:HAS_REQUIREMENT]->(req)
                    """, {
                        "p_code":         p_code,
                        "p_name":         sk.get("prodi", ""),
                        "syarat_khusus":  sk.get("syarat_khusus", ""),
                        "latar_belakang": sk.get("latar_belakang", "")
                    })
                
            # FAQ
            for f_item in pmb.get("faq", []):
                if not isinstance(f_item, dict) or not f_item.get("pertanyaan"):
                    continue
                session.run("""
                MATCH (u:University {code: 'UPJ'})
                MERGE (f:FAQ {pertanyaan: $pertanyaan})
                SET f.jawaban = $jawaban
                MERGE (u)-[:HAS_FAQ]->(f)
                """, {"pertanyaan": f_item.get("pertanyaan", ""), "jawaban": f_item.get("jawaban", "")})

        # Ingest WebPages
        if data.get("pages"):
            print(f"Ingesting {len(data['pages'])} WebPages...")
            session.run("""
            UNWIND $pages AS p
            MATCH (prodi:ProgramStudi {code: p.prodi_code})
            MERGE (page:WebPage {url: p.url})
            SET page.title = p.title,
                page.snippet = p.snippet
            MERGE (prodi)-[:HAS_WEBPAGE]->(page)
            """, {"pages": data["pages"]})

        # Ingest Tracer Study & Work Scopes
        tracer = data.get("tracer_study", {})
        cohorts = tracer.get("cohorts", [])
        summaries = tracer.get("summaries", [])
        
        if cohorts or summaries:
            print(f"Ingesting Tracer Study ({len(cohorts)} prodi-year records, {len(summaries)} annual summaries)...")
            
            # 1. Standard Lingkup Kerja Categories
            scopes = [
                {"kategori": "Multinasional / Internasional", "deskripsi": "Perusahaan multinasional atau institusi internasional"},
                {"kategori": "Nasional / Berwirausaha Berizin", "deskripsi": "Perusahaan skala nasional atau wirausaha berizin resmi"},
                {"kategori": "Lokal / Wilayah", "deskripsi": "Institusi lokal / wilayah atau wirausaha rintisan"}
            ]
            for sc in scopes:
                session.run("""
                MERGE (lk:LingkupKerja {kategori: $kategori})
                SET lk.deskripsi = $deskripsi
                """, sc)
                
            # 2. University-wide Tracer Summaries
            for sm in summaries:
                session.run("""
                MATCH (u:University {code: 'UPJ'})
                MERGE (s:TracerSummary {id: $id})
                SET s.tahun = $tahun,
                    s.total_lulusan = $total_lulusan,
                    s.total_terlacak = $total_terlacak,
                    s.persentase_terlacak = $persentase_terlacak,
                    s.total_wt_kurang_6_bulan = $total_wt_kurang_6_bulan,
                    s.total_wt_6_sd_18_bulan = $total_wt_6_sd_18_bulan,
                    s.total_wt_lebih_18_bulan = $total_wt_lebih_18_bulan,
                    s.persen_wt_kurang_6_bulan = $persen_wt_kurang_6_bulan,
                    s.total_kesesuaian_sangat_erat = $total_kesesuaian_sangat_erat,
                    s.total_kesesuaian_erat = $total_kesesuaian_erat,
                    s.total_kesesuaian_cukup_erat = $total_kesesuaian_cukup_erat,
                    s.total_kesesuaian_kurang_erat = $total_kesesuaian_kurang_erat,
                    s.total_kesesuaian_tidak_sama_sekali = $total_kesesuaian_tidak_sama_sekali,
                    s.total_kesesuaian_selaras = $total_kesesuaian_selaras,
                    s.persen_kesesuaian_selaras = $persen_kesesuaian_selaras,
                    s.total_lingkup_lokal = $total_lingkup_lokal,
                    s.total_lingkup_nasional = $total_lingkup_nasional,
                    s.persen_lingkup_nasional = $persen_lingkup_nasional,
                    s.total_lingkup_multinasional = $total_lingkup_multinasional,
                    s.persen_lingkup_multinasional = $persen_lingkup_multinasional
                MERGE (u)-[:HAS_TRACER_SUMMARY]->(s)
                """, sm)
                
            # 3. Prodi-level Tracer Study nodes & links
            for item in cohorts:
                session.run("""
                MERGE (prodi:ProgramStudi {code: $prodi_code})
                ON CREATE SET prodi.name = $prodi_name
                MERGE (ts:TracerStudy {id: $id})
                SET ts.tahun = $tahun,
                    ts.prodi_code = $prodi_code,
                    ts.prodi_name = $prodi_name,
                    ts.faculty_code = $faculty_code,
                    ts.faculty_name = $faculty_name,
                    ts.jumlah_lulusan = $jumlah_lulusan,
                    ts.jumlah_terlacak = $jumlah_terlacak,
                    ts.persentase_terlacak = $persentase_terlacak,
                    ts.wt_kurang_6_bulan = $wt_kurang_6_bulan,
                    ts.wt_6_sd_18_bulan = $wt_6_sd_18_bulan,
                    ts.wt_lebih_18_bulan = $wt_lebih_18_bulan,
                    ts.persen_wt_kurang_6_bulan = $persen_wt_kurang_6_bulan,
                    ts.kesesuaian_sangat_erat = $kesesuaian_sangat_erat,
                    ts.kesesuaian_erat = $kesesuaian_erat,
                    ts.kesesuaian_cukup_erat = $kesesuaian_cukup_erat,
                    ts.kesesuaian_kurang_erat = $kesesuaian_kurang_erat,
                    ts.kesesuaian_tidak_sama_sekali = $kesesuaian_tidak_sama_sekali,
                    ts.kesesuaian_selaras = $kesesuaian_selaras,
                    ts.persen_kesesuaian_selaras = $persen_kesesuaian_selaras,
                    ts.lingkup_lokal = $lingkup_lokal,
                    ts.lingkup_nasional = $lingkup_nasional,
                    ts.persen_lingkup_nasional = $persen_lingkup_nasional,
                    ts.lingkup_multinasional = $lingkup_multinasional,
                    ts.persen_lingkup_multinasional = $persen_lingkup_multinasional,
                    ts.is_suppressed = $is_suppressed,
                    ts.suppress_wt_lt_6 = $suppress_wt_lt_6,
                    ts.suppress_selaras = $suppress_selaras,
                    ts.suppress_nasional = $suppress_nasional,
                    ts.suppress_multinasional = $suppress_multinasional
                MERGE (prodi)-[:HAS_TRACER_STUDY]->(ts)
                WITH ts, $lingkup_multinasional AS multi, $lingkup_nasional AS nas, $lingkup_lokal AS lok,
                     $persen_lingkup_multinasional AS p_multi, $persen_lingkup_nasional AS p_nas
                
                // Link to annual university summary
                OPTIONAL MATCH (s:TracerSummary {id: 'TS_UPJ_' + toString(ts.tahun)})
                FOREACH (_ IN CASE WHEN s IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (s)-[:INCLUDES_PRODI_TRACER]->(ts)
                )
                
                // Link to Lingkup Kerja nodes
                FOREACH (_ IN CASE WHEN multi > 0 THEN [1] ELSE [] END |
                    MERGE (lk_m:LingkupKerja {kategori: 'Multinasional / Internasional'})
                    MERGE (ts)-[:ABSORBED_BY_SECTOR {jumlah: multi, persentase: p_multi}]->(lk_m)
                )
                FOREACH (_ IN CASE WHEN nas > 0 THEN [1] ELSE [] END |
                    MERGE (lk_n:LingkupKerja {kategori: 'Nasional / Berwirausaha Berizin'})
                    MERGE (ts)-[:ABSORBED_BY_SECTOR {jumlah: nas, persentase: p_nas}]->(lk_n)
                )
                FOREACH (_ IN CASE WHEN lok > 0 THEN [1] ELSE [] END |
                    MERGE (lk_l:LingkupKerja {kategori: 'Lokal / Wilayah'})
                    MERGE (ts)-[:ABSORBED_BY_SECTOR {jumlah: lok}]->(lk_l)
                )
                """, item)
                
            # 4. Chain temporal transitions (2022 -> 2023 -> 2024)
            session.run("""
            MATCH (s1:TracerSummary), (s2:TracerSummary)
            WHERE s2.tahun = s1.tahun + 1
            MERGE (s1)-[:NEXT_YEAR]->(s2)
            """)
            
            session.run("""
            MATCH (ts1:TracerStudy), (ts2:TracerStudy)
            WHERE ts1.prodi_code = ts2.prodi_code AND ts2.tahun = ts1.tahun + 1
            MERGE (ts1)-[:FOLLOWED_BY]->(ts2)
            """)
        
    driver.close()
    logger.info("Graph ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate Neo4j Graph from Scraped UPJ JSON files and Tracer Study")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j Bolt URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j Username")
    parser.add_argument("--password", default="password123", help="Neo4j Password")
    parser.add_argument("--data-dir", default="data", help="Directory containing scraped JSON and Excel files")
    parser.add_argument("--only-tracer", action="store_true", help="Only parse and ingest tracer study data")
    parser.add_argument("--dry-run", action="store_true", help="Parse and output preview without connecting to Neo4j")
    parser.add_argument("--preview-file", default="graph_preview.json", help="Path to write JSON preview")
    parser.add_argument("--include-alumni-names", action="store_true", help="Include raw public alumni testimonial names instead of anonymized IDs")
    args = parser.parse_args()
    
    if args.only_tracer:
        logger.info("Parsing ONLY Tracer Study...")
        tracer_candidates = [
            os.path.join(args.data_dir, "tracer study.xlsx"),
            os.path.join("data", "tracer study.xlsx"),
            "tracer study.xlsx"
        ]
        t_data = {"cohorts": [], "summaries": []}
        for t_path in tracer_candidates:
            if os.path.exists(t_path):
                logger.info("Loading Tracer Study from %s...", t_path)
                t_data = parse_tracer_study(t_path)
                break
        extracted = {
            "prodi": [],
            "lecturers": [],
            "courses": [],
            "pages": [],
            "pmb": {},
            "tracer_study": t_data
        }
    else:
        logger.info("Parsing scraped data and tracer study from '%s'...", args.data_dir)
        extracted = extract_all_data(args.data_dir, anonymize_alumni=not args.include_alumni_names)

    logger.info("Parsed summary:")
    logger.info(" - %d Program Studi", len(extracted["prodi"]))
    logger.info(" - %d Dosen/Lecturers", len(extracted["lecturers"]))
    logger.info(" - %d Mata Kuliah/Courses", len(extracted["courses"]))
    logger.info(" - %d Web Pages", len(extracted["pages"]))
    if extracted.get("pmb"):
        logger.info(
            " - PMB Data loaded: Biaya Kuliah, Beasiswa (%d), Peminatan (%d), FAQ (%d)",
            len(extracted["pmb"].get("beasiswa", [])),
            len(extracted["pmb"].get("peminatan_konsentrasi", [])),
            len(extracted["pmb"].get("faq", []))
        )
    if extracted.get("tracer_study"):
        ts_c = len(extracted["tracer_study"].get("cohorts", []))
        ts_s = len(extracted["tracer_study"].get("summaries", []))
        logger.info(" - Tracer Study Data loaded: %d cohort records across 10 prodi, %d annual summaries (2022-2024)", ts_c, ts_s)
    
    if args.dry_run:
        with open(args.preview_file, "w", encoding="utf-8") as fp:
            json.dump(extracted, fp, indent=2, ensure_ascii=False)
        logger.info("Dry run preview saved to %s", args.preview_file)
    else:
        populate_neo4j(extracted, uri=args.uri, user=args.user, password=args.password)
