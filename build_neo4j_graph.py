import os
import re
import json
import glob
import argparse
from urllib.parse import urlparse
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

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

def parse_prodi_details(pages, prodi_key):
    info = FACULTY_MAP.get(prodi_key, {"code": "FTD", "faculty": "Fakultas Teknologi dan Desain", "name": prodi_key.upper()})
    prodi_data = {
        "code": prodi_key.upper(),
        "name": info["name"],
        "faculty": info["faculty"],
        "faculty_code": info["code"],
        "degree": "",
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
    
    for p in pages:
        content = p.get("content", "")
        url = p.get("url", "")
        
        degree_match = re.search(r'(Bachelor of [^\n\r]+(?:\([A-Za-z\.]+\))?)', content)
        if degree_match and not prodi_data["degree"]:
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
            career_sec = re.search(r'(?:Future Career|Karir masa depan|Career Prospects)[^\n]*\n([\s\S]+?)(?:Alumni|Cerita Alumni|Join|Contact Us|«|$)', content)
            if career_sec:
                sec_text = career_sec.group(1)
                items = re.findall(r'(?:[-•]\s*|\b(?:Become a|Menjadi|sebagai)\s+)?([A-Za-z0-9 &\(\)/]+(?:Engineer|Developer|Analyst|Consultant|Specialist|Manager|Auditor|Accountant|Architect|Designer|Entrepreneur))', sec_text, re.IGNORECASE)
                for item in items:
                    clean_item = item.strip()
                    if clean_item and len(clean_item) > 3 and clean_item not in prodi_data["career_paths"]:
                        prodi_data["career_paths"].append(clean_item)
                        
        if 'facilities' in url:
            fac_lines = [l.strip() for l in content.split('\n') if l.strip()]
            for l in fac_lines:
                if l in ['Facilities', 'Contact Us', 'PMB', '1 / 6', '1 / 2'] or len(l) < 3 or len(l) > 60:
                    continue
                if l not in prodi_data["facilities"]:
                    prodi_data["facilities"].append(l)
                    
        if "Alumni Testimonials" in content or "Cerita Alumni" in content or "Alumni Stories" in content:
            alumni_sec = re.search(r'(?:Alumni Testimonials|Cerita Alumni|Alumni Stories)\n([\s\S]+?)(?:Contact Us|PMB|«|$)', content)
            if alumni_sec:
                a_text = alumni_sec.group(1)
                a_matches = re.findall(r'([A-Z][a-zA-Z\s]+,\s*S\.[A-Za-z\.]+)\n+([^\n]+)', a_text)
                for name, role in a_matches:
                    prodi_data["alumni"].append({
                        "name": name.strip(),
                        "role": role.strip()
                    })
                    
    return prodi_data

def extract_all_data(data_dir="."):
    files = sorted(glob.glob(os.path.join(data_dir, "scraped_*_upj.json")))
    all_prodi = []
    all_lecturers = []
    all_courses = []
    all_pages = []
    
    # Load PMB data if available
    pmb_data = {}
    pmb_path = os.path.join(data_dir, "scraped_pmb_upj.json")
    if os.path.exists(pmb_path):
        try:
            with open(pmb_path, "r", encoding="utf-8") as f:
                pmb_data = json.load(f)
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
            
        prodi_info = parse_prodi_details(pages, key)
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
                
    return {
        "prodi": all_prodi,
        "lecturers": all_lecturers,
        "courses": all_courses,
        "pages": all_pages,
        "pmb": pmb_data
    }

def populate_neo4j(data, uri="bolt://localhost:7687", user="neo4j", password="password123"):
    if not GraphDatabase:
        raise RuntimeError("neo4j python package not installed. Run 'pip install neo4j'")
        
    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        print("Creating constraints and indexes...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:University) REQUIRE u.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Faculty) REQUIRE f.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:ProgramStudi) REQUIRE p.code IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Lecturer) REQUIRE l.email IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (w:WebPage) REQUIRE w.url IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Beasiswa) REQUIRE b.nama IS UNIQUE"
        ]
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                print(f"Constraint notice: {e}")
                
        # University & Faculties
        print("Ingesting University and Faculties...")
        session.run("""
        MERGE (u:University {code: 'UPJ'})
        ON CREATE SET u.name = 'Universitas Pembangunan Jaya', 
                      u.website = 'https://upj.ac.id',
                      u.pmb_website = 'https://pmb.upj.ac.id',
                      u.living_lab = 'Grup Pembangunan Jaya (17 unit usaha)',
                      u.tagline = 'Mendidik Manusia Jaya yang Berintegritas, Profesional, dan Berjiwa Entrepreneur'
        MERGE (ftd:Faculty {code: 'FTD'})
        ON CREATE SET ftd.name = 'Fakultas Teknologi dan Desain'
        MERGE (fhb:Faculty {code: 'FHB'})
        ON CREATE SET fhb.name = 'Fakultas Humaniora dan Bisnis'
        MERGE (u)-[:HAS_FACULTY]->(ftd)
        MERGE (u)-[:HAS_FACULTY]->(fhb)
        """)
        
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
            # Biaya SPP & SKS per prodi
            biaya_list = pmb.get("biaya_kuliah", {}).get("tabel_spp_sks_semester_1", [])
            for bk in biaya_list:
                if not isinstance(bk, dict) or not bk.get("prodi"):
                    continue
                session.run("""
                MATCH (prodi:ProgramStudi)
                WHERE toLower(prodi.name) CONTAINS toLower($p_name) OR toLower($p_name) CONTAINS toLower(prodi.name)
                MERGE (b:BiayaKuliah {prodi: $p_name})
                SET b.spp = $spp,
                    b.sks_kelas = $sks_kelas,
                    b.sks_praktik = $sks_praktik,
                    b.total_semester_1 = $total_sem_1
                MERGE (prodi)-[:HAS_TUITION_FEE]->(b)
                """, {
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
                
            # Peminatan / Konsentrasi
            for pem in pmb.get("peminatan_konsentrasi", []):
                p_name = pem.get("prodi", "")
                if not p_name:
                    continue
                for p_item in pem.get("peminatan", []):
                    if not isinstance(p_item, str) or not p_item.strip():
                        continue
                    session.run("""
                    MATCH (prodi:ProgramStudi)
                    WHERE toLower(prodi.name) CONTAINS toLower($p_name)
                    MERGE (sp:Peminatan {name: $p_item, prodi_code: prodi.code})
                    SET sp.waktu_pemilihan = $waktu
                    MERGE (prodi)-[:HAS_SPECIALIZATION]->(sp)
                    """, {"p_name": p_name, "p_item": p_item.strip(), "waktu": pem.get("waktu_pemilihan", "Semester 5")})
                    
            # Syarat Khusus Masuk
            for sk in pmb.get("syarat_khusus_prodi", []):
                if not isinstance(sk, dict) or not sk.get("prodi"):
                    continue
                session.run("""
                MATCH (prodi:ProgramStudi)
                WHERE toLower(prodi.name) CONTAINS toLower($p_name)
                MERGE (req:SyaratKhusus {prodi: $p_name})
                SET req.syarat_khusus = $syarat_khusus,
                    req.latar_belakang = $latar_belakang
                MERGE (prodi)-[:HAS_REQUIREMENT]->(req)
                """, {
                    "p_name":        sk.get("prodi", ""),
                    "syarat_khusus": sk.get("syarat_khusus", ""),
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
        print(f"Ingesting {len(data['pages'])} WebPages...")
        session.run("""
        UNWIND $pages AS p
        MATCH (prodi:ProgramStudi {code: p.prodi_code})
        MERGE (page:WebPage {url: p.url})
        SET page.title = p.title,
            page.snippet = p.snippet
        MERGE (prodi)-[:HAS_WEBPAGE]->(page)
        """, {"pages": data["pages"]})
        
    driver.close()
    print("Graph ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate Neo4j Graph from Scraped UPJ JSON files")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j Bolt URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j Username")
    parser.add_argument("--password", default="password123", help="Neo4j Password")
    parser.add_argument("--dry-run", action="store_true", help="Parse and output preview without connecting to Neo4j")
    parser.add_argument("--preview-file", default="graph_preview.json", help="Path to write JSON preview")
    args = parser.parse_args()
    
    print("Parsing scraped data (including PMB)...")
    extracted = extract_all_data(".")
    print(f"Parsed summary:")
    print(f" - {len(extracted['prodi'])} Program Studi")
    print(f" - {len(extracted['lecturers'])} Dosen/Lecturers")
    print(f" - {len(extracted['courses'])} Mata Kuliah/Courses")
    print(f" - {len(extracted['pages'])} Web Pages")
    if extracted.get("pmb"):
        print(f" - PMB Data loaded: Biaya Kuliah, Beasiswa ({len(extracted['pmb'].get('beasiswa', []))}), Peminatan ({len(extracted['pmb'].get('peminatan_konsentrasi', []))}), FAQ ({len(extracted['pmb'].get('faq', []))})")
    
    if args.dry_run:
        with open(args.preview_file, "w", encoding="utf-8") as fp:
            json.dump(extracted, fp, indent=2, ensure_ascii=False)
        print(f"Dry run preview saved to {args.preview_file}")
    else:
        populate_neo4j(extracted, uri=args.uri, user=args.user, password=args.password)
