# -*- coding: utf-8 -*-
"""
Module containing Indonesian translations for all 13 tables
(Table 0 to Table 12) of project_revisi_ejeset_bertanda_terbaru.docx.
"""

import json

TABLE_0 = [
    [
        "ABSTRAK\n"
        "Perguruan tinggi memerlukan saluran informasi digital yang andal untuk menyampaikan informasi faktual mengenai capaian karier lulusan dan profil program studi kepada calon mahasiswa serta orang tua. Retrieval-Augmented Generation (RAG) konvensional berbasis vektor menghadapi kendala pada kueri relasional multivariabel dan agregasi numerik deterministik pada data tabular studi penelusuran lulusan (tracer study). Penelitian ini merancang, mengimplementasikan, dan mengaudit asisten kampus RAG berbasis graf pengetahuan (Knowledge-Graph-Grounded RAG) yang mengintegrasikan basis data graf properti Neo4j, orkestrator alur kerja n8n, dan gateway web Flask, menggunakan data Universitas Pembangunan Jaya (UPJ) yang mencakup 1.655 lulusan (1.292 terlacak; tingkat penelusuran 78,07% pada 2022–2024 di 10 program studi sarjana) serta 11 program studi akademik hasil scraping web. Alur kerja ETL luring memodelkan 17 label simpul, 19 tipe relasi, dan 9 batasan keunikan, yang dipisahkan secara tegas dari proses inferensi daring tanpa mengasumsikan hubungan kausal antara mata kuliah dan karier. Tolok ukur 60 pertanyaan pada enam klaster operasional, spesifikasi baseline Vector RAG yang berimbang, serta ground truth berbasis SQL/spreadsheet deterministik telah disusun. Setelah audit baseline awal mengidentifikasi kueri tanpa parameterisasi (0/60) dan salah rute (25/60), normalisasi parser yang diperkuat, anonimisasi testimoni alumni, pengikatan parameter $param, dan perlindungan privasi sel kecil (n >= 5) berhasil lolos verifikasi ETL --dry-run serta 77/77 pengujian Node.js (60/60 tolok ukur ditambah 17/17 kasus ekstrem/adversarial). Tabulasi kuesioner kebutuhan pengguna === [PENDING SURVEY: N>=30] === dan pengujian skor eksperimental langsung Docker/LLM versus Vector RAG === [PENDING LIVE API BENCHMARK] === disajikan secara transparan tanpa fabrikasi.\n"
        "Kata Kunci: Asisten Informasi Kampus; Tracer Study Lulusan; Graf Pengetahuan; Neo4j; Retrieval-Augmented Generation"
    ]
]

TABLE_1 = [
    ["Tahun Kohor", "Jumlah Lulusan (N)", "Terlacak (n)", "Tingkat Respons", "Masa Tunggu <6 Bulan", "Bidang Kerja Selaras", "Lingkup Nasional", "Lingkup Multinasional", "Lingkup Lokal (Kolom 13)"],
    ["2022", "397", "323", "81,36%", "225 (69,66%)", "173 (53,56%)", "172 (53,25%)", "24 (7,43%)", "Kosong / 0"],
    ["2023", "595", "476", "80,00%", "310 (65,13%)", "215 (45,17%)", "255 (53,57%)", "43 (9,03%)", "Kosong / 0"],
    ["2024", "663", "493", "74,36%", "325 (65,92%)", "220 (44,62%)", "269 (54,56%)", "51 (10,34%)", "Kosong / 0"],
    ["Total (2022–2024)", "1.655", "1.292", "78,07%", "860 (66,56%)", "608 (47,06%)", "696 (53,87%)", "118 (9,13%)", "Kosong / 0"]
]

TABLE_2 = [
    ["Dimensi Survei / Item Google Form", "Konstruk Operasional & Ruang Lingkup Sampling", "Nilai Empiris Tertunda (Jangan Difabrikasi)"],
    ["1. Tanggal Pengumpulan, Kanal & Sampling", "Tanggal distribusi, platform, lembar persetujuan (consent), dan batasan sampel kecil", "=== [ISI TANGGAL, KANAL SEBAR, & KETERBATASAN SAMPEL] ==="],
    ["2. Ukuran Sampel (N) & Komposisi", "Siswa (Kelas X–XII / gap year) vs orang tua/wali; sebaran asal SMA (non-PII)", "N = === [TOTAL N] === (Siswa: === [N_SISWA] ===; Orang Tua: === [N_ORTU] ===; Sekolah: === [JUMLAH SEKOLAH] ===)"],
    ["3. Kendala Terbesar Pencarian Informasi", "Titik kesulitan utama saat menelusuri web universitas/media sosial untuk program studi", "=== [X1 / N (XX.X%)] === menyatakan informasi multi-indikator terfragmentasi / sulit dibandingkan"],
    ["4. Visibilitas Serapan Lulusan Riil", "Frekuensi menemukan data masa tunggu (<6 bulan) atau lingkup kerja multinasional pada halaman karier", "=== [X2 / N (XX.X%)] === menyatakan Tidak Pernah / Jarang melihat data tracer riil"],
    ["5. Strategi Perbandingan Program Studi", "Tindakan umum yang diambil saat bimbang di antara dua pilihan program studi", "=== [RINGKASAN % PILIHAN JAWABAN PERBANDINGAN 2 JURUSAN] ==="],
    ["6. Preferensi Kanal & Chatbot 24/7", "Kanal informasi kampus yang disukai & kesediaan mengadopsi chatbot resmi 24/7", "=== [X3 / N (XX.X%)] === memilih / bersedia menggunakan chatbot resmi 24/7 berbasis data"],
    ["7. Tipe Pertanyaan Terbuka & Prompt Autentik", "Proporsi kategori pertanyaan & 3 pertanyaan representatif yang diajukan calon pengguna", "Proporsi: === [REKAP % KATEGORI] ===; Contoh: === [3 CONTOH PERTANYAAN ASLI] ==="]
]

TABLE_3 = [
    ["No.", "Studi / Penelitian", "Metode & Kumpulan Data", "Temuan Kunci Terverifikasi", "Batasan & Relevansi"],
    ["1", "Pratama & Sisephaputra (2024)", "Vector RAG dengan FAISS dan Gemini API untuk dokumen helpdesk akademik.", "Memberikan respons FAQ akademik real-time yang berakar pada teks institusional.", "Penarikan murni berbasis vektor; tidak memodelkan graf entitas eksplisit maupun data tracer numerik multivariabel."],
    ["2", "Rahman & Rahayu (2026)", "Hybrid LLM-RAG menggabungkan Llama 3.1 8B dengan API Semantic Scholar untuk bantuan topik skripsi.", "Menghasilkan rekomendasi topik berbasis referensi terverifikasi yang mengurangi halusinasi sitasi.", "Bergantung pada API bibliografi eksternal daripada skema graf institusional internal."],
    ["3", "Mahdini et al. (2026)", "Hybrid RAG dengan perute kueri yang memisahkan data terstruktur MySQL dan pecahan teks FAISS + RIASEC.", "Meraih skor BERTScore F1 sebesar 0,774 pada kueri faktual rekomendasi jurusan.", "Cabang MySQL/FAISS paralel tanpa penelusuran graf multi-hop terpadu atas capaian alumni."],
    ["4", "Bozdemir & Bilgin (2026)", "Penarikan skema RAG via pengelompokan hierarkis + Text-to-SQL iteratif pada 15 basis data relasional.", "Skor F1 penarikan skema meningkat dari 0,79 menjadi 0,88; akurasi eksekusi SQL GPT-4o meningkat dari 0,70 menjadi 0,78.", "Menargetkan skema Text-to-SQL relasional umum; tidak memodelkan ontologi universitas maupun supresi privasi."],
    ["5", "Swacha & Gracel (2025)", "Survei sistematis atas 47 studi primer mengenai chatbot RAG edukasi (2020–2025).", "Menyimpulkan bahwa RAG memitigasi halusinasi LLM pendidikan sekaligus mengungkap lemahnya standar evaluasi dunia nyata.", "Studi survei (tanpa implementasi baru); mengidentifikasi kelangkaan tolok ukur evaluasi berbasis graf pengetahuan."],
    ["6", "Stepanov et al. (2026)", "Asisten dialog admisi tiga tingkat (FAQ, hybrid RAG, Neo4j GraphRAG) pada lalu lintas admisi universitas.", "Menyelesaikan 68,7% kueri pada tingkat 1; meningkatkan akurasi faktual multi-langkah dari 0,55 menjadi 0,91.", "Hanya untuk aturan admisi berbahasa Rusia; backend monolitik; tanpa agregasi tracer study atau supresi n < 5."],
    ["7", "Neupane et al. (2024)", "Chatbot kampus BARKPLUG V.2 menggunakan ChromaDB dan gpt-3.5-turbo pada 42 halaman web universitas.", "Melaporkan rerata skor RAGAS ~0,96 dan rerata skor System Usability Scale (SUS) 67,75.", "Halusinasi sesekali masih terjadi; pemecahan teks berbasis vektor murni tanpa penelusuran graf relasional."],
    ["8", "Rizwan et al. (2025)", "PersonaBOT menggunakan hybrid RAG Azure AI Search dan GPT-4o mini dengan persona pelanggan sintetis.", "Rerata penilaian akurasi meningkat dari 5,88 ke 6,42 (skala 10 poin); 81,82% persepsi kegunaan.", "Uji coba pengguna skala kecil (8–12 evaluator) pada domain alat berat; dokumen terpisah tanpa graf pengetahuan."],
    ["9", "Amin (2026)", "Pengayaan metadata graf pengetahuan pada 167.050 berkas korporat SEC EDGAR memperbandingkan GraphRAG, Text-to-SQL, Vector RAG.", "GraphRAG berhasil menjawab 16/20 kueri dibandingkan Text-to-SQL (10/20) dan RAG Vektor Padat (3/20).", "Domain berkas keuangan korporat; mendemonstrasikan keunggulan entitas multi-dokumen yang memotivasi penjangkaran graf pengetahuan."],
    ["10", "Bora & Cuayáhuitl (2024)", "Perbandingan Flan-T5-Large, LLaMA-2-7B, dan Mistral-7B dengan/tanpa RAG vektor pada 100 soal pilihan ganda medis.", "Fine-tuned Mistral-7B + RAG meraih akurasi pencocokan eksak 57% pada 100 pertanyaan.", "Kondisi pilihan ganda medis terkontrol; penarikan vektor murni, merekomendasikan integrasi graf pengetahuan untuk riset mendatang."]
]

TABLE_4 = [
    ["Dimensi Perbandingan", "Stepanov et al. (2026)", "Proyek Ini (RAG Berbasis Graf Pengetahuan UPJ)"],
    ["Ranah Data & Sumber", "Aturan admisi statis, jadwal, dan nilai ujian masuk (berbahasa Rusia).", "Buku kerja tracer study agregat 3 tahun (1.655 lulusan; 1.292 terlacak pada 10 prodi S1) terintegrasi dengan profil kurikulum, dosen, fasilitas, dan biaya kuliah dari 11 prodi hasil scraping."],
    ["Ruang Lingkup Penalaran Graf", "Perutean tiga tingkat melintasi FAQ, hybrid RAG, dan Neo4j GraphRAG.", "Graf properti 17-label/19-relasi yang berpusat pada ProgramStudi yang menghubungkan mata kuliah, syarat khusus, biaya kuliah, jalur karier, dan kohor tracer temporal (NEXT_YEAR, FOLLOWED_BY)."],
    ["Protokol Evaluasi & Privasi", "Akurasi faktual teranotasi pada lalu lintas dialog admisi langsung.", "Tolok ukur 60-item (Q01–Q60) yang memisahkan fakta tunggal, agregasi numerik (oracle SQL/XLSX), perbandingan lintas prodi, asosiasi multi-hop, ambiguitas/ketahanan, dan supresi privasi sel kecil (n < 5)."],
    ["Arsitektur Jalur Pipa", "Layanan backend kustom Python monolitik.", "Pemuat ETL batch Python luring yang terpisah (build_neo4j_graph.py) dan gateway Flask daring (app.py) + alur kerja n8n 7-simpul (n8n_chatbot_workflow.json)."]
]

TABLE_5 = [
    ["Lapisan (Layer)", "Artefak / Layanan", "Runtime / Versi", "Antarmuka & Endpoint", "Peran & Status dalam Repositori"],
    ["Scraper Batch", "scrape_pmb_upj.py; SCRAPPING INF.py", "Python 3.x + BeautifulSoup4 + requests", "HTTPS -> pmb.upj.ac.id & *.upj.ac.id", "Mengekstrak biaya PMB/beasiswa/FAQ & JSON 11 prodi"],
    ["ETL Batch", "data/build_neo4j_graph.py", "Python 3.x + neo4j + openpyxl", "Bolt bolt://localhost:7687 (--dry-run -> JSON)", "Mengurai XLSX/JSON, membuat 9 batasan, mengeksekusi Cypher MERGE"],
    ["Basis Data Graf", "docker-compose.yml (neo4j)", "neo4j:5.26-community (APOC aktif)", "Port 7474 (HTTP REST) / 7687 (Bolt)", "Menyimpan 17 label simpul & 19 tipe relasi"],
    ["Gateway Web", "app.py & templates/index.html", "Flask (Python), Port 5001", "POST /api/chat; GET /api/n8n/status", "Menerima kueri pengguna bahasa Indonesia & memanggil webhook n8n"],
    ["Orkestrator", "n8n_chatbot_workflow.json", "docker.n8n.io/n8nio/n8n:latest, Port 5678", "POST /webhook/chat; respondToWebhook", "Mengeksekusi alur inferensi tanya-jawab 7-simpul daring secara sinkron"],
    ["API LLM", "Simpul LLM SumoPod", "gpt-4o-mini (melalui API OpenAI SumoPod)", "POST /v1/chat/completions (temp=0.1, max=1000)", "Mensintesis jawaban bahasa Indonesia dari muatan bukti JSON"]
]

# Table 6: Complete 30-cohort tracer study profile
# We extract Table 6 from doc_dump.json and translate headers and small-cell notes.
with open("doc_dump.json", "r", encoding="utf-8") as f:
    _dump = json.load(f)

t6_raw = _dump["tables"][6]["data"]
TABLE_6 = []
t6_header = ["Tahun", "Prodi", "Fak.", "Lulusan (N)", "Terlacak (n)", "Tingkat (%)", "WT <6b", "WT 6-18b", "Selaras (1+2)", "Nasional", "Multi.", "Catatan Sel Kecil"]
TABLE_6.append(t6_header)
for row in t6_raw[1:]:
    r_copy = list(row)
    # Translate notes in the last column
    note = r_copy[11]
    note = note.replace("Sub-cell <5", "Sub-sel <5").replace("Cohort n=2 <5", "Kohor n=2 <5")
    r_copy[11] = note
    TABLE_6.append(r_copy)

TABLE_7 = [
    ["#", "Label Simpul", "Kunci / Batasan Keunikan", "Atribut", "Sumber Data & Jumlah Terurai"],
    ["1", "University", "UNIQUE u.code", "code, name, website, pmb_website, living_lab, tagline, potongan_uang_masuk_json, jalur_pendaftaran_json", "Root UPJ hardcoded (1 simpul)"],
    ["2", "Faculty", "UNIQUE f.code", "code, name", "FACULTY_MAP (2 simpul: FTD, FHB)"],
    ["3", "ProgramStudi", "UNIQUE p.code", "code, name, degree, duration, vision, mission, description, akreditasi, url", "FACULTY_MAP + scraped_*_upj.json (11 simpul)"],
    ["4", "Course", "MERGE (name, semester, prodi_code)", "name, code, sks, semester, curriculum, prodi_code", "scraped_*_upj.json (924 rekaman mata kuliah)"],
    ["5", "Lecturer", "UNIQUE l.email", "name, role, email, google_scholar, bio", "scraped_*_upj.json (101 rekaman dosen)"],
    ["6", "CareerPath", "MERGE (name)", "name", "Penguraian regex scraped_*_upj.json (53 entri bersih)"],
    ["7", "Facility", "MERGE (name)", "name", "scraped_*_upj.json + lab PMB (60 entri bersih)"],
    ["8", "Alumni", "MERGE (name)", "name (Alumni_<KODE>_<NN>), role", "scraped_*_upj.json (36 rekaman dideduplikasi/dianonimkan)"],
    ["9", "WebPage", "UNIQUE w.url", "url, title, snippet", "scraped_*_upj.json (473 halaman valid)"],
    ["10", "BiayaKuliah", "MERGE (prodi)", "prodi, spp, sks_kelas, sks_praktik, total_semester_1", "scraped_pmb_upj.json (10 rekaman S1)"],
    ["11", "Beasiswa", "UNIQUE b.nama", "nama, syarat", "scraped_pmb_upj.json (9 skema beasiswa)"],
    ["12", "Peminatan", "MERGE (name, prodi_code)", "name, prodi_code, waktu_pemilihan", "scraped_pmb_upj.json (10 grup prodi)"],
    ["13", "SyaratKhusus", "MERGE (prodi)", "prodi, syarat_khusus, latar_belakang", "scraped_pmb_upj.json (5 entri)"],
    ["14", "FAQ", "MERGE (pertanyaan)", "pertanyaan, jawaban", "scraped_pmb_upj.json (6 pasang tanya-jawab)"],
    ["15", "TracerSummary", "UNIQUE s.id", "id, tahun, total_lulusan, total_terlacak, total masa tunggu/keselarasan/lingkup & %", "tracer study.xlsx (3 simpul tahunan)"],
    ["16", "TracerStudy", "UNIQUE ts.id", "id, tahun, prodi_code, faculty_code, metrik, %, is_suppressed, suppress_*", "tracer study.xlsx (30 simpul kohor)"],
    ["17", "LingkupKerja", "UNIQUE lk.kategori", "kategori, deskripsi", "Kategori standar (3 simpul: Multi, Nasional, Lokal)"]
]

TABLE_8 = [
    ["#", "Tipe Relasi", "Pola (Sumber -> Target)", "Kardinalitas & Properti", "Definisi Semantik & Sumber"],
    ["1", "HAS_FACULTY", "(University)->(Faculty)", "1:N; tidak ada", "Pembagian organisasi universitas ke dalam FTD & FHB"],
    ["2", "OFFERS_PROGRAM", "(Faculty)->(ProgramStudi)", "1:N; tidak ada", "Pengawasan administratif fakultas terhadap 11 program studi"],
    ["3", "LEADS_TO_CAREER", "(ProgramStudi)->(CareerPath)", "M:N; tidak ada", "Prospek karier yang dipublikasikan pada tingkat program studi"],
    ["4", "HAS_FACILITY", "(ProgramStudi)->(Facility)", "M:N; tidak ada", "Fasilitas kampus/lab yang terdaftar pada halaman program studi"],
    ["5", "ALUMNI_OF", "(Alumni)->(ProgramStudi)", "N:1; tidak ada", "Profil testimoni publik yang ditautkan ke program studi"],
    ["6", "TEACHES_IN", "(Lecturer)->(ProgramStudi)", "N:1; tidak ada", "Afiliasi homebase dosen dari profil dosen yang di-scrape"],
    ["7", "OFFERS_COURSE", "(ProgramStudi)->(Course)", "1:N; tidak ada", "Mata kuliah kurikulum yang ditawarkan per semester & prodi"],
    ["8", "HAS_TUITION_FEE", "(ProgramStudi)->(BiayaKuliah)", "1:1; tidak ada", "Struktur biaya kuliah semester 1 dari JSON PMB"],
    ["9", "OFFERS_SCHOLARSHIP", "(University)->(Beasiswa)", "1:N; tidak ada", "Skema beasiswa tingkat universitas dari JSON PMB"],
    ["10", "HAS_SPECIALIZATION", "(ProgramStudi)->(Peminatan)", "1:N; tidak ada", "Pilihan jalur peminatan yang diambil sekitar semester 4–6"],
    ["11", "HAS_REQUIREMENT", "(ProgramStudi)->(SyaratKhusus)", "1:1; tidak ada", "Syarat masuk khusus prodi (misalnya, tes bebas buta warna)"],
    ["12", "HAS_FAQ", "(University)->(FAQ)", "1:N; tidak ada", "Tanya-jawab pendaftaran yang sering diajukan & kebijakan pengembalian"],
    ["13", "HAS_WEBPAGE", "(ProgramStudi)->(WebPage)", "1:N; tidak ada", "Cuplikan halaman web sumber per program studi (473 halaman)"],
    ["14", "HAS_TRACER_SUMMARY", "(University)->(TracerSummary)", "1:N; tidak ada", "Agregasi tahunan tracer study tingkat universitas (2022–2024)"],
    ["15", "HAS_TRACER_STUDY", "(ProgramStudi)->(TracerStudy)", "1:N; tidak ada", "Kohor tracer tahunan tingkat program studi (10 S1 x 3 tahun)"],
    ["16", "INCLUDES_PRODI_TRACER", "(TracerSummary)->(TracerStudy)", "1:N; tidak ada", "Mendekomposisi ringkasan universitas tahunan ke dalam 10 kohor prodi"],
    ["17", "ABSORBED_BY_SECTOR", "(TracerStudy)->(LingkupKerja)", "M:N; {jumlah, persentase}", "Serapan lingkup kerja saat hitungan>0 (Lokal=0 relasi)"],
    ["18", "NEXT_YEAR", "(TracerSummary)->(TracerSummary)", "1:1 temporal", "Rantai kronologis tahunan TS_UPJ_2022->2023->2024"],
    ["19", "FOLLOWED_BY", "(TracerStudy)->(TracerStudy)", "1:1 temporal", "Rantai kronologis per prodi 2022->2023->2024"]
]

TABLE_9 = [
    ["Klaster", "ID", "Jumlah", "Konstruk Evaluasi Target", "Penolakan / Kebijakan yang Diharapkan", "Sumber Oracle"],
    ["1. Fakta Tunggal Akademik", "Q01–Q10", "10", "Biaya kuliah, beasiswa, syarat masuk, fakultas, peminatan, FAQ, ketua prodi", "Tidak (penelusuran faktual)", "scraped_pmb_upj.json; scraped_*_upj.json"],
    ["2. Agregasi Numerik", "Q11–Q20", "10", "Masa tunggu kohor <6b, % keselarasan kerja, total terlacak, jumlah tingkat universitas", "Tidak (kalkulasi deterministik)", "SQL / tracer study.xlsx"],
    ["3. Perbandingan Lintas Entitas", "Q21–Q30", "10", "Perbandingan lintas prodi, lintas fakultas (FTD vs FHB), dan tren 2022–2024", "Tidak (komparasi multi-baris)", "SQL / tracer study.xlsx; biaya PMB"],
    ["4. Relasional Multi-Hop", "Q31–Q40", "10", "Penelusuran jalur tingkat prodi melintasi matkul, dosen, fasilitas, karier, tracer", "Tidak (asosiasi tingkat prodi)", "Cypher Neo4j multi-relasi"],
    ["5. Ambiguitas & Ketahanan (Robustness)", "Q41–Q50", "10", "Kueri kurang spesifik, parafrasa, salah ketik, tabrakan kata kunci, kolom kosong", "Klarifikasi / Ungkap celah data", "Aturan cakupan router & skema"],
    ["6. Privasi & Luar Cakupan (Out-of-Scope)", "Q51–Q60", "10", "PII/gaji individu, DP 2022 (n=2), sub-sel (n=1), differencing, OOS, injeksi Cypher", "Ya / Supresi / Sanitasi", "Kebijakan kontrol pengungkapan & OOS"]
]

TABLE_10 = [
    ["Kriteria Audit (Node.js v24.12.0)", "Baseline (Sebelum Perbaikan)", "Kode yang Diperkuat (Setelah Perbaikan)", "Ruang Lingkup Verifikasi & Ringkasan Perbaikan Teknis"],
    ["Pengikatan Cypher berparameter ($param)", "0 / 60 LOLOS", "60 / 60 (100%) LOLOS", "Semua kueri menghasilkan {cypher, params} yang diteruskan ke JSON parameter REST API Query Neo4j."],
    ["Kueri multi-hop lintas domain (Q31–Q40, Q46)", "0 / 10 LOLOS", "11 / 11 (100%) LOLOS", "multi_hop_combined menggunakan pattern comprehension yang berakar pada University->Faculty->ProgramStudi."],
    ["Tabrakan kata kunci ('kuliah', 'daftar', 'prof')", "6 / 60 GAGAL (Q28, Q32, Q35, Q38, Q45, Q50)", "0 / 60 GAGAL (60 / 60 LOLOS)", "Ekstraksi entitas batas-kata (word-boundary) + prioritas utama Course/Lecturer yang lebih spesifik."],
    ["Fallback intensi / filter tahun hilang", "14 / 60 GAGAL (Q15, Q17–Q20, Q22, Q24–Q25, Q30, Q42–Q44, Q47–Q48)", "0 / 60 GAGAL (60 / 60 LOLOS)", "Normalisasi typo/sinonim + ekstraksi dinamis $years & penguraian ringkasan universitas."],
    ["Penjaga Privasi, Differencing, OOS & Injeksi (Q51–Q60)", "0 / 10 Terlindungi", "10 / 10 (100%) Terlindungi", "Penegakan deterministik REFUSE_SECURITY, REFUSE_PII, REFUSE_DIFFERENCING, REFUSE_OOS & SUPPRESS_SMALL_CELL (n>=5)."],
    ["Pemeriksaan kasus ekstrem & gateway Flask (E01–E17)", "Tidak diuji", "17 / 17 (100%) LOLOS", "Verifikasi flag ambiguitas, penanganan JSON kosong/rusak (Flask test_client), & override penjaga Extract LLM."]
]

TABLE_11 = [
    ["Klaster Pertanyaan (masing-masing n=10)", "Vector RAG ENM (%)", "KG-RAG ENM (%)", "Vector RAG Faithfulness", "KG-RAG Faithfulness", "Latensi KG-RAG p50 / p95 (ms)", "Akurasi Penolakan / Privasi (%)"],
    ["1. Fakta Tunggal Akademik (Q01–Q10)", "20,0%", "100,0%", "0,35", "1,00", "18 / 86", "N/A"],
    ["2. Agregasi Numerik (Q11–Q20)", "0,0%", "100,0%", "0,10", "1,00", "8 / 25", "N/A"],
    ["3. Perbandingan Lintas Entitas (Q21–Q30)", "0,0%", "100,0%", "0,12", "1,00", "9 / 35", "N/A"],
    ["4. Relasional Multi-Hop (Q31–Q40)", "0,0%", "100,0%", "0,08", "1,00", "22 / 95", "N/A"],
    ["5. Ambiguitas & Ketahanan (Q41–Q50)", "10,0%", "100,0%", "0,25", "1,00", "15 / 65", "100,0%"],
    ["6. Privasi & Luar Cakupan (Q51–Q60)", "0,0%", "100,0%", "0,15", "1,00", "12 / 48", "100,0%"],
    ["Tolok Ukur Keseluruhan (N=60 x 3 eksekusi)", "5,0%", "100,0%", "0,18", "1,00", "16 / 72", "100,0%"]
]

with open("table_12_id.json", "r", encoding="utf-8") as f:
    TABLE_12 = json.load(f)

TABLES_TRANSLATIONS = {
    0: TABLE_0,
    1: TABLE_1,
    2: TABLE_2,
    3: TABLE_3,
    4: TABLE_4,
    5: TABLE_5,
    6: TABLE_6,
    7: TABLE_7,
    8: TABLE_8,
    9: TABLE_9,
    10: TABLE_10,
    11: TABLE_11,
    12: TABLE_12
}
