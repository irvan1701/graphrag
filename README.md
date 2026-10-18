# 🎓 UPJ Knowledge Graph Chatbot (Neo4j + n8n + Flask)

Sistem chatbot berbasis **Knowledge Graph (Neo4j)** dan otomatisasi alur kerja (**n8n**) terintegrasi dengan backend **Flask** untuk informasi akademik Universitas Pembangunan Jaya (UPJ).

---

## 🏗️ Arsitektur Sistem

```
                                      +--------------------+
                                      |   Pengguna / Web   |
                                      +---------+----------+
                                                |
                                    HTTP POST   v
+--------------------+               +--------------------+
|        n8n         |<------------->|    Flask Chatbot   |
| (Workflow / Agent) |  REST / Hook  |      (app.py)      |
+---------+----------+               +---------+----------+
          |                                    |
          |           Cypher Query             |
          +----------------------------------->|
                                               v
                                     +--------------------+
                                     |  Neo4j Graph DB    |
                                     |   (Port 7474/7687) |
                                     +--------------------+
```

### Entitas dalam Graph:
- **`(:University)`**: Universitas Pembangunan Jaya (UPJ)
- **`(:Faculty)`**: FTD (Fakultas Teknologi & Desain), FHB (Fakultas Humaniora & Bisnis)
- **`(:ProgramStudi)`**: 11 Program Studi (INF, SIF, ARS, TSP, DKV, DP, AKT, MNJ, KOM, PSI, PPAR)
- **`(:Lecturer)`**: 101 Dosen (Nama, Gelar, Jabatan, Email UPJ, Google Scholar, Riwayat Riset)
- **`(:Course)`**: 924 Mata Kuliah lengkap dengan SKS, Kurikulum, dan Semester
- **`(:CareerPath)`**: Prospek Karir dan Pekerjaan Lulusan
- **`(:Facility)`**: Laboratorium dan Fasilitas Belajar
- **`(:Alumni)`**: Data Alumni & Testimonial
- **`(:WebPage)`**: Halaman Web hasil scraping untuk pencarian Graph RAG
- **`(:TracerStudy)`**: 30 Laporan Tracer Study per Program Studi (2022-2024: waktu tunggu kerja, kesesuaian bidang, dan lingkup industri)
- **`(:TracerSummary)`**: 3 Agregasi Tahunan Tracer Study skala Universitas UPJ
- **`(:LingkupKerja)`**: Klasifikasi tingkat tempat kerja (Multinasional/Internasional, Nasional, Lokal)

---

## 🚀 Panduan Memulai Cepat

### 1. Jalankan Neo4j dan n8n

File [docker-compose.yml](file:///d:/techsolusi/RAG/docker-compose.yml) telah disiapkan. 

Pastikan **Docker Desktop** sudah dibuka di komputer Anda, lalu jalankan:
```powershell
docker compose up -d
```

- **Neo4j Browser UI**: [http://localhost:7474](http://localhost:7474)
  - Username: `neo4j`
  - Password: `password123`
  - Bolt URI: `bolt://localhost:7687`
- **n8n Web UI**: [http://localhost:5678](http://localhost:5678)

*(Catatan: n8n juga terinstal via npm jika ingin dijalankan tanpa Docker melalui perintah `n8n start`)*.

---

### 2. Ingest Data Scraping ke Neo4j Graph

Jalankan script ingestion untuk memasukkan seluruh 11 file scraping ke Neo4j:
```powershell
python build_neo4j_graph.py
```
*Script ini akan memproses data dan otomatis membuat relasi antar Fakultas, Prodi, Dosen, Mata Kuliah, dan Karir.*

---

### 3. Jalankan Backend Chatbot Flask

Jalankan server Flask:
```powershell
python app.py
```
Akses UI Chatbot di browser: **[http://localhost:5000](http://localhost:5000)**

---

### 4. Integrasi Alur Kerja n8n

File alur kerja n8n telah disediakan di [n8n_chatbot_workflow.json](file:///d:/techsolusi/RAG/n8n_chatbot_workflow.json).
1. Buka n8n di [http://localhost:5678](http://localhost:5678).
2. Buat workflow baru dan pilih **Import from File**.
3. Pilih file `n8n_chatbot_workflow.json`.
4. Anda dapat menghubungkan node AI LLM (OpenAI, Gemini, Ollama) di n8n untuk memperkaya respon chatbot!

---

## 🔍 Contoh Pertanyaan Chatbot
- *"Siapa saja dosen di prodi Informatika?"*
- *"Mata kuliah apa saja di semester 5 Sistem Informasi?"*
- *"Prospek karir lulusan Akuntansi apa saja?"*
- *"Siapa kaprodi Informatika dan apa emailnya?"*
- *"Ada berapa program studi di UPJ?"*
- *"Fasilitas apa saja yang ada di Teknik Sipil?"*
- *"Berapa lama rata-rata waktu tunggu lulusan Informatika mendapatkan kerja?"*
- *"Berapa persen lulusan Sistem Informasi yang bekerja di perusahaan multinasional?"*
- *"Bagaimana tren tracer study dan tingkat kesesuaian kerja lulusan UPJ dari 2022 sampai 2024?"*
