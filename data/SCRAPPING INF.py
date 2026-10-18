from urllib.parse import urljoin, urlparse
import time
import json
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import os

sites_to_scrape = [
    "https://dp.upj.ac.id/",
    "https://sif.upj.ac.id/",
    "https://tsp.upj.ac.id/",
    "https://ppar.upj.ac.id/",
    "https://ars.upj.ac.id/",
    "https://psi.upj.ac.id/",
    "https://mnj.upj.ac.id/",
    "https://kom.upj.ac.id/",
    "https://akt.upj.ac.id/"
]

print("Mempersiapkan browser (Undetected Selenium - VISIBLE)...")
options = uc.ChromeOptions()
# Hapus headless untuk memastikan Cloudflare challenge terlewati
# options.add_argument("--headless")
driver = uc.Chrome(options=options)
print("Browser siap!")

try:
    for base_url in sites_to_scrape:
        domain = urlparse(base_url).netloc
        
        # Penamaan file output berdasarkan subdomain (misal dp dari dp.upj.ac.id)
        subdomain = domain.split('.')[0]
        output_file = f"scraped_{subdomain}_upj.json"
        
        print(f"\n=========================================")
        print(f"MULAI SCRAPING: {base_url}")
        print(f"Output akan disimpan di: {output_file}")
        print(f"=========================================\n")
        
        visited_urls = set()
        to_visit = [
            base_url,
            urljoin(base_url, "/glance"),
            urljoin(base_url, "/profile"),
            urljoin(base_url, "/courses"),
            urljoin(base_url, "/facilities"),
            urljoin(base_url, "/lecturer-profile"),
            urljoin(base_url, "/activity")
        ]
        
        scraped_data = []

        while to_visit:
            current_url = to_visit.pop(0)
            if current_url in visited_urls:
                continue

            try:
                print(f"Mengakses: {current_url}")
                driver.get(current_url)
                
                # Beri waktu bagi JavaScript (anti-bot dan framework SPA) untuk memuat halaman asli
                time.sleep(8)
                
                html_content = driver.page_source
                visited_urls.add(current_url)

                soup = BeautifulSoup(html_content, "html.parser")

                # Ambil title
                title = ""
                if soup.title and soup.title.get_text(strip=True):
                    title = soup.title.get_text(strip=True)
                elif soup.find("h1"):
                    title = soup.find("h1").get_text(strip=True)
                else:
                    title = "Tanpa Judul"
                    
                # 1. EKSTRAK SEMUA RUTE INTERNAL DULU (sebelum navbar/header dihapus)
                found_links = 0
                for tag_a in soup.find_all("a", href=True):
                    if "href" not in tag_a.attrs:
                        continue
                    href = tag_a["href"].strip()

                    if href.startswith(("mailto:", "tel:", "javascript:", "#")) or not href:
                        continue

                    full_url = urljoin(base_url, href)
                    clean_url = full_url.split("#")[0]
                    parsed = urlparse(clean_url)

                    if parsed.netloc == domain and clean_url not in visited_urls and clean_url not in to_visit:
                        to_visit.append(clean_url)
                        found_links += 1

                # 2. HAPUS ELEMEN YANG TIDAK PERLU UNTUK KONTEN TEKS
                for unwanted in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    unwanted.decompose()
                
                # 3. AMBIL TEKS BERSIH
                lines = (line.strip() for line in soup.get_text().splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = '\n'.join(chunk for chunk in chunks if chunk)

                # Jangan simpan kalau masih tersangkut di halaman "Just a moment..." (Cloudflare)
                if "Just a moment" not in title and "Cloudflare" not in title:
                    scraped_data.append({
                        "url": current_url,
                        "title": title,
                        "content": content
                    })
                    # Tulis ke file JSON bertahap per website
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(scraped_data, f, ensure_ascii=False, indent=4)

                print(f"Berhasil scrape: {current_url} | Judul: {title}")
                print(f"-> Ditemukan {found_links} rute baru. Total antrean sisa: {len(to_visit)}\n")

            except Exception as e:
                print(f"Gagal mengambil {current_url}: {e}")
                
finally:
    try:
        driver.quit()
    except:
        pass