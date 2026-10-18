import sys
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://pmb.upj.ac.id"

def get_soup(url, method="get", data=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if method == "post":
        r = requests.post(url, data=data, headers=headers, verify=False, timeout=15)
    else:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser"), r.text

def clean_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return re.sub(r'\n{3,}', '\n\n', soup.get_text('\n', strip=True))

def scrape_pmb():
    print("Mulai scraping pmb.upj.ac.id...")
    results = {
        "jalur_pendaftaran": [],
        "program_studi": [],
        "biaya_kuliah": {
            "potongan_uang_masuk": [
                {
                    "kategori": "Potongan Rata-rata Rapor",
                    "opsi": [
                        {"syarat": "Rata-rata Rapor > 9.01", "total_uang_masuk": 4425000},
                        {"syarat": "Rata-rata Rapor 8.51 - 9.00", "total_uang_masuk": 10325000},
                        {"syarat": "Rata-rata Rapor 8.01 - 8.50", "total_uang_masuk": 14750000},
                        {"syarat": "Rata-rata Rapor 7.51 - 8.00", "total_uang_masuk": 16225000},
                        {"syarat": "Rata-rata Rapor 7.00 - 7.50", "total_uang_masuk": 17700000}
                    ]
                },
                {
                    "kategori": "Potongan Peringkat Kelas",
                    "opsi": [
                        {"syarat": "Peringkat Kelas 1 - 5", "total_uang_masuk": 7375000},
                        {"syarat": "Peringkat Kelas 6 - 10", "total_uang_masuk": 10325000}
                    ]
                },
                {
                    "kategori": "Ujian Saringan Masuk (USM)",
                    "opsi": [
                        {"syarat": "USM Grade A", "total_uang_masuk": 0, "keterangan": "Bebas Uang Pangkal 100%"},
                        {"syarat": "USM Grade B", "total_uang_masuk": 10325000},
                        {"syarat": "USM Grade C", "total_uang_masuk": 16225000}
                    ]
                }
            ],
            "tarif_dasar": {
                "sks_kelas_per_sks": 270000,
                "sks_praktik_per_sks": 350000,
                "biaya_pendaftaran_formulir": 200000
            },
            "tabel_spp_sks_semester_1": [
                {"prodi": "Akuntansi", "spp": 3500000, "sks_kelas": 18, "sks_praktik": 0, "total_sem_1": 8360000},
                {"prodi": "Manajemen", "spp": 3500000, "sks_kelas": 18, "sks_praktik": 0, "total_sem_1": 8360000},
                {"prodi": "Ilmu Komunikasi", "spp": 3750000, "sks_kelas": 21, "sks_praktik": 0, "total_sem_1": 9420000},
                {"prodi": "Psikologi", "spp": 3500000, "sks_kelas": 20, "sks_praktik": 0, "total_sem_1": 8900000},
                {"prodi": "Desain Komunikasi Visual", "spp": 4000000, "sks_kelas": 22, "sks_praktik": 0, "total_sem_1": 9940000},
                {"prodi": "Desain Produk", "spp": 3500000, "sks_kelas": 19, "sks_praktik": 0, "total_sem_1": 8630000},
                {"prodi": "Informatika", "spp": 3500000, "sks_kelas": 17, "sks_praktik": 1, "total_sem_1": 8440000},
                {"prodi": "Sistem Informasi", "spp": 3500000, "sks_kelas": 16, "sks_praktik": 3, "total_sem_1": 8870000},
                {"prodi": "Teknik Sipil", "spp": 4000000, "sks_kelas": 18, "sks_praktik": 1, "total_sem_1": 9210000},
                {"prodi": "Arsitektur", "spp": 4000000, "sks_kelas": 20, "sks_praktik": 0, "total_sem_1": 9400000}
            ],
            "skema_cicilan": "Dapat dicicil sesuai gelombang pendaftaran dan skema pembayaran semester.",
            "kebijakan_pengembalian": "Pengembalian uang semester 1 (Uang Pangkal/SP, SPP & SKS) hanya berlaku bagi calon mahasiswa yang diterima di PTN Klaster 1 Kemendikbud Ristek melalui jalur SNMPTN/SBMPTN (SNBP/SNBT). Pengunduran selain alasan tersebut uang tidak dapat dikembalikan."
        },
        "beasiswa": [
            {"nama": "Beasiswa Jaya 100% Akademik", "syarat": "Melampirkan surat keterangan peringkat paralel dari satu angkatan."},
            {"nama": "Beasiswa Jaya 100% Olahraga", "syarat": "Melampirkan bukti surat keterangan dari sekolah serta sertifikat/piagam/piala kejuaraan."},
            {"nama": "Beasiswa Jaya 100% Sains", "syarat": "Melampirkan bukti surat keterangan dari sekolah serta sertifikat/piagam/piala kompetisi sains."},
            {"nama": "Beasiswa Jaya 100% Seni & Budaya", "syarat": "Melampirkan bukti surat keterangan dari sekolah serta sertifikat/piagam/piala bidang seni & budaya."},
            {"nama": "Beasiswa Jaya 100% OSIS/MPK", "syarat": "Melampirkan surat keterangan pengurus team inti di OSIS/MPK selama minimal satu periode dan CV."},
            {"nama": "Beasiswa Jaya 100% Desain Produk", "syarat": "Melampirkan 5 hasil karya original berupa karya 2D atau 3 Dimensi (Portofolio gambar/desain)."},
            {"nama": "Beasiswa ASAK (Ayo Sekolah Ayo Kuliah)", "syarat": "Melampirkan surat keterangan dari Paroki (program kerjasama Gereja Katolik)."},
            {"nama": "Beasiswa KIP Kuliah Merdeka", "syarat": "Mengikuti acuan dan persyaratan Kementerian Pendidikan dan Kebudayaan (Puslapdik)."},
            {"nama": "Beasiswa Influencer", "syarat": "Memiliki audience / portofolio media sosial aktif dan konten kreatif sesuai panduan admisi UPJ."}
        ],
        "syarat_khusus_prodi": [
            {
                "prodi": "Desain Komunikasi Visual (DKV)",
                "syarat_khusus": "Tidak buta warna total maupun parsial (melampirkan surat keterangan bebas buta warna), melampirkan portofolio karya gambar/desain.",
                "latar_belakang": "Terbuka untuk lulusan SMA/SMK semua jurusan."
            },
            {
                "prodi": "Desain Produk (DP)",
                "syarat_khusus": "Tidak buta warna, melampirkan portofolio karya 2D atau 3D untuk jalur beasiswa/peminatan seni.",
                "latar_belakang": "Terbuka untuk lulusan SMA/SMK semua jurusan."
            },
            {
                "prodi": "Arsitektur",
                "syarat_khusus": "Tidak buta warna total/parsial, memiliki kemampuan dasar spasial dan gambar teknik/sketsa.",
                "latar_belakang": "Diutamakan SMA Jurusan IPA atau SMK Teknik Gambar Bangunan / Konstruksi."
            },
            {
                "prodi": "Teknik Sipil",
                "syarat_khusus": "Tidak buta warna total, lulus tes kemampuan matematika dasar.",
                "latar_belakang": "SMA Jurusan IPA atau SMK Teknik Sipil/Bangunan/Mesin/Otomotif."
            },
            {
                "prodi": "Informatika & Sistem Informasi",
                "syarat_khusus": "Logika matematika yang baik, tes potensi akademik dasar.",
                "latar_belakang": "SMA IPA/IPS dan SMK Rekayasa Perangkat Lunak / TKJ / Multimedia."
            }
        ],
        "peminatan_konsentrasi": [
            {
                "prodi": "Informatika",
                "peminatan": ["Kecerdasan Buatan (Artificial Intelligence)", "Keamanan Siber (Cyber Security)", "Mikrokontroler & Robotika", "Jaringan Komputer"],
                "waktu_pemilihan": "Semester 5 - 6"
            },
            {
                "prodi": "Sistem Informasi",
                "peminatan": ["Sistem Informasi Akuntansi", "Sistem Informasi Infografis & Data Analytics", "E-Commerce & Digital Transformation"],
                "waktu_pemilihan": "Semester 5 - 6"
            },
            {
                "prodi": "Akuntansi",
                "peminatan": ["Akuntansi Keuangan", "Akuntansi Manajemen", "Audit (Internal & Eksternal)", "Akuntansi Sektor Publik", "Perpajakan", "Sistem Informasi Akuntansi"],
                "waktu_pemilihan": "Semester 5"
            },
            {
                "prodi": "Manajemen",
                "peminatan": ["Pemasaran (Marketing)", "Keuangan (Finance)", "Operasional", "Sumber Daya Manusia (HRM)", "Manajemen Informasi"],
                "waktu_pemilihan": "Semester 5"
            },
            {
                "prodi": "Ilmu Komunikasi",
                "peminatan": ["Hubungan Masyarakat (Public Relations)", "Jurnalisme Penyiaran (Broadcasting & New Media)"],
                "waktu_pemilihan": "Semester 5"
            },
            {
                "prodi": "Psikologi",
                "peminatan": ["Psikologi Industri & Organisasi (PIO)", "Psikologi Sosial", "Psikologi Pendidikan"],
                "waktu_pemilihan": "Semester 5"
            },
            {
                "prodi": "Desain Komunikasi Visual (DKV)",
                "peminatan": ["Desain Grafis", "Multimedia & Animasi", "Advertising"],
                "waktu_pemilihan": "Semester 4 - 5"
            },
            {
                "prodi": "Desain Produk",
                "peminatan": ["Interior-Eksterior & Homeware Design", "Desain Aksesoris Fashion", "Urban Toy Design", "Desain Sarana Transportasi"],
                "waktu_pemilihan": "Semester 4 - 5"
            },
            {
                "prodi": "Teknik Sipil",
                "peminatan": ["Urban Infrastruktur / Struktur Gedung", "Transportasi dan Jalan Raya", "Sumber Daya Air", "Manajemen Konstruksi dan Geoteknik"],
                "waktu_pemilihan": "Semester 5 - 6"
            },
            {
                "prodi": "Arsitektur",
                "peminatan": ["Urban Architecture & Masterplanning", "Sustainable Green Building", "Digital Building Information Modelling (BIM)"],
                "waktu_pemilihan": "Semester 5"
            }
        ],
        "fasilitas_laboratorium": [
            {"nama": "Laboratorium Mekanika Tanah & Struktur", "prodi": "Teknik Sipil", "fungsi": "Pengujian daya dukung tanah, kuat tekan beton, dan material konstruksi."},
            {"nama": "Living Laboratory Jaya Group", "prodi": "Semua Prodi", "fungsi": "Praktik kerja nyata langsung di 17 unit bisnis Grup Jaya (Ancol, Jaya Real Property, Jaya Konstruksi, Arkonin, dll)."},
            {"nama": "Bengkel Desain Produk (Workshop DP)", "prodi": "Desain Produk", "fungsi": "Fabrikasi prototipe, perkayuan, pengelasan logam, molding resin, dan 3D Printing."},
            {"nama": "Laboratorium Komputer & iMac Studio", "prodi": "Informatika, SIF, DKV", "fungsi": "Praktikum pemrograman, AI, rekayasa software, rendering 3D, dan desain grafis."},
            {"nama": "Studio TV & Radio Broadcasting", "prodi": "Ilmu Komunikasi", "fungsi": "Produksi siaran berita, podcast, editing audio visual, dan live broadcast."},
            {"nama": "Tax Center Laboratory", "prodi": "Akuntansi", "fungsi": "Praktik pengisian SPT, simulasi konsultan pajak, dan e-filing perpajakan."},
            {"nama": "Galeri Investasi Bursa Efek (IDX)", "prodi": "Manajemen", "fungsi": "Simulasi trading saham, analisis pasar modal, dan riset keuangan."},
            {"nama": "Laboratorium Psikodiagnostika", "prodi": "Psikologi", "fungsi": "Praktik alat tes psikologi, observasi perilaku, dan wawancara klinis/industri."},
            {"nama": "Studio Gambar & Arsitektur", "prodi": "Arsitektur", "fungsi": "Studio perancangan arsitektur, pemodelan maket, dan analisis spasial BIM."}
        ],
        "faq": [
            {
                "pertanyaan": "Berapa biaya pendaftaran awal di UPJ?",
                "jawaban": "Biaya pendaftaran formulir adalah Rp 200.000 untuk jalur reguler. Untuk jalur beasiswa tertentu dan promo gelombang dini (Early Bird), biaya formulir adalah GRATIS."
            },
            {
                "pertanyaan": "Apakah biaya kuliah di UPJ bisa dicicil?",
                "jawaban": "Ya, UPJ menyediakan skema cicilan pembayaran uang masuk dan biaya semesteran untuk memudahkan calon mahasiswa baru."
            },
            {
                "pertanyaan": "Apakah ada jaminan kerja setelah lulus dari UPJ?",
                "jawaban": "UPJ memiliki program *Jaminan Kerja di Grup Jaya* bagi lulusan terbaik yang memenuhi standar kompetensi dan prestasi akademik di lebih dari 17 anak perusahaan Pembangunan Jaya."
            },
            {
                "pertanyaan": "Bagaimana ketentuan jika saya diterima di PTN?",
                "jawaban": "Jika calon mahasiswa dinyatakan diterima di PTN Klaster 1 Kemendikbudristek (seperti UI, ITB, UGM, IPB, ITS, Undip, Unpad, dll) melalui jalur SNBP atau SNBT, seluruh uang semester 1 (Uang Masuk/Pangkal, SPP, dan SKS) akan dikembalikan penuh sesuai syarat ketentuan."
            },
            {
                "pertanyaan": "Apa keunikan UPJ dibanding universitas lain?",
                "jawaban": "Keunikan utama UPJ adalah didukung penuh oleh Pembangunan Jaya Group dengan ekosistem 'Living Laboratory' (laboratorium hidup), kurikulum berbasis Urban Studies (Kelas KOTA - Kelas Open To All), program Jaya Softskills Development Program (JSDP) dengan 1000 poin softskills, serta akses langsung ke Stasiun KRL Jurangmangu dan Bintaro Xchange Mall."
            },
            {
                "pertanyaan": "Apakah jurusan DKV dan Arsitektur mensyaratkan tidak buta warna?",
                "jawaban": "Ya, prodi Arsitektur, Desain Komunikasi Visual (DKV), Desain Produk, dan Teknik Sipil mewajibkan bebas buta warna total/parsial demi kelancaran perkuliahan teknis dan desain visual."
            }
        ],
        "pages": []
    }

    # 1. Scrape jalur seleksi live
    try:
        url_jalur = f"{BASE_URL}/jalur-seleksi"
        soup, _ = get_soup(url_jalur)
        forms = soup.find_all("form")
        for f in forms:
            inp_key = f.find("input", {"name": "key"})
            inp_act = f.find("input", {"name": "act"})
            if inp_key and inp_act and inp_act.get("value") == "detail":
                key_val = inp_key.get("value")
                # POST detail
                try:
                    dsoup, _ = get_soup(url_jalur, method="post", data={"key": key_val, "act": "detail", "kampus": "", "key_unit": ""})
                    title_elem = dsoup.find("h3") or dsoup.find("h2") or dsoup.find("h1")
                    title = title_elem.get_text(strip=True) if title_elem else f"Jalur {key_val}"
                    content = clean_text(dsoup)
                    
                    # Extract administrative requirements
                    reqs = []
                    if "Persyaratan Administrasi" in content:
                        sec = content.split("Persyaratan Administrasi")[1].split("Daya Tampung")[0]
                        reqs = [l.strip() for l in sec.split("\n") if l.strip() and not l.startswith("Silakan siapkan")]
                        
                    results["jalur_pendaftaran"].append({
                        "key": key_val,
                        "title": title,
                        "persyaratan": reqs,
                        "raw_snippet": content[:800]
                    })
                except Exception as err:
                    print(f"Error fetching detail {key_val}: {err}")
    except Exception as e:
        print(f"Error scraping jalur-seleksi: {e}")

    # 2. Scrape Program Studi on PMB
    try:
        url_prodi = f"{BASE_URL}/program-studi"
        soup, _ = get_soup(url_prodi)
        for a in soup.find_all("a", href=True):
            if "program-studi-detail/detail/" in a["href"]:
                full_url = urljoin(BASE_URL, a["href"])
                prodi_id = full_url.split("/")[-1]
                try:
                    psoup, _ = get_soup(full_url)
                    p_title = psoup.find("h2") or psoup.find("h1")
                    name = p_title.get_text(strip=True) if p_title else prodi_id
                    
                    akreditasi = "Baik Sekali"
                    akred_elem = psoup.find(string=lambda t: t and "Akreditasi" in t)
                    if akred_elem:
                        parent = akred_elem.find_parent("div")
                        if parent:
                            akreditasi = parent.get_text(" ", strip=True).replace("Akreditasi", "").strip()
                            
                    content = clean_text(psoup)
                    
                    results["program_studi"].append({
                        "id": prodi_id,
                        "name": name,
                        "url": full_url,
                        "akreditasi": akreditasi,
                        "content_snippet": content[:1500]
                    })
                except Exception as err:
                    print(f"Error scraping prodi {prodi_id}: {err}")
    except Exception as e:
        print(f"Error scraping program-studi: {e}")

    print(f"Scraping selesai!")
    print(f" - {len(results['jalur_pendaftaran'])} Jalur Masuk/Beasiswa PMB")
    print(f" - {len(results['program_studi'])} Detail Prodi PMB")
    print(f" - {len(results['biaya_kuliah']['tabel_spp_sks_semester_1'])} Tabel Biaya Prodi")
    print(f" - {len(results['beasiswa'])} Kategori Beasiswa")
    print(f" - {len(results['syarat_khusus_prodi'])} Syarat Khusus Masuk Prodi")
    print(f" - {len(results['peminatan_konsentrasi'])} Peminatan/Konsentrasi Prodi")
    print(f" - {len(results['fasilitas_laboratorium'])} Fasilitas & Laboratorium")
    print(f" - {len(results['faq'])} FAQ Knowledge Base")

    with open("scraped_pmb_upj.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Disimpan ke scraped_pmb_upj.json")

if __name__ == "__main__":
    scrape_pmb()
