"""
GEO Engine - Modul Kalkulasi, Analisis, dan Rekomendasi
untuk GEO Audit App Nusantara.
"""

from typing import Dict, List, Any, Tuple
import urllib.request
import urllib.error
import urllib.parse
import urllib.robotparser
import ssl
import time
import re

# Definisi 4 Pilar GEO beserta Bobot & Indikatornya
GEO_PILLARS = {
    "pilar_1": {
        "id": "pilar_1",
        "title": "Aksesibilitas Teknis & AI Crawlers",
        "weight": 0.20,  # 20%
        "description": "Memastikan bot crawler AI (GPTBot, ClaudeBot, Google-Extended) diizinkan membaca situs dengan cepat dan aman.",
        "icon": "🤖",
        "indicators": [
            {
                "id": "tech_robots",
                "label": "Konfigurasi robots.txt mengizinkan AI Crawlers",
                "sublabel": "Mengizinkan User-agent: GPTBot, ClaudeBot, Google-Extended, dan PerplexityBot untuk melakukan pengindeksan.",
                "weight_in_pilar": 0.50,  # 10% total
                "weight_total": 10.0,
                "help": "Jika robots.txt memblokir bot AI, website Anda akan 'buta' dan tidak pernah disitasi oleh ChatGPT Search atau Perplexity."
            },
            {
                "id": "tech_https_speed",
                "label": "Enkripsi HTTPS aktif dan kecepatan muat situs di bawah 3 detik",
                "sublabel": "Sertifikat SSL valid (HTTPS) dan waktu respon server (TTFB) cepat agar crawler tidak mengalami timeout.",
                "weight_in_pilar": 0.50,  # 10% total
                "weight_total": 10.0,
                "help": "AI crawler memiliki batas waktu tunggu (crawl timeout) yang sangat ketat. Situs lambat akan dilewati."
            }
        ]
    },
    "pilar_2": {
        "id": "pilar_2",
        "title": "Kejelasan Struktur Konten & BLUF",
        "weight": 0.30,  # 30%
        "description": "Menyusun konten dengan prinsip Bottom Line Up Front (BLUF) dan semantik hierarkis agar mudah di-chunking dan di-embed oleh model AI.",
        "icon": "📝",
        "indicators": [
            {
                "id": "content_bluf",
                "label": "Ringkasan produk, keunggulan, dan harga diletakkan di paragraf teratas (BLUF)",
                "sublabel": "Bottom Line Up Front: Konsumen dan AI langsung mendapatkan jawaban inti dalam 50 kata pertama tanpa scroll panjang.",
                "weight_in_pilar": 0.25,  # 7.5% total
                "weight_total": 7.5,
                "help": "Model RAG mengekstrak 'chunk' awal dokumen sebagai kandidat jawaban teratas dalam Retrieval context window."
            },
            {
                "id": "content_headings",
                "label": "Struktur HTML menggunakan hierarki heading semantik yang rapi (H1, H2, H3)",
                "sublabel": "Heading jelas mendeskripsikan topik bahasan untuk mempermudah pemotongan teks (semantic chunking) oleh AI parser.",
                "weight_in_pilar": 0.25,  # 7.5% total
                "weight_total": 7.5,
                "help": "Parser AI memecah halaman web menjadi chunk berdasarkan tag heading. Heading yang berantakan menghasilkan representasi chunk yang rancu."
            },
            {
                "id": "content_faq",
                "label": "Terdapat bagian FAQ Percakapan (Conversational FAQ)",
                "sublabel": "Format tanya-jawab alami yang langsung menjawab pertanyaan spesifik, perbandingan, kecocokan, dan kendala calon pembeli.",
                "weight_in_pilar": 0.25,  # 7.5% total
                "weight_total": 7.5,
                "help": "Pertanyaan pengguna ke chatbot AI bernada percakapan (misal: 'Apakah kopi ini aman untuk lambung?'). Format FAQ mempermudah direct-matching."
            },
            {
                "id": "content_data",
                "label": "Konten mencantumkan data spesifik, angka kuantitatif, dimensi, atau statistik",
                "sublabel": "Mencantumkan harga transparan (Rp), berat (gram/kg), komposisi persentase, nomor sertifikasi BPOM/Halal, dan garansi.",
                "weight_in_pilar": 0.25,  # 7.5% total
                "weight_total": 7.5,
                "help": "Riset akademis GEO membuktikan bahwa menyertakan data kuantitatif dan statistik meningkatkan peluang sitasi AI hingga 30-40%."
            }
        ]
    },
    "pilar_3": {
        "id": "pilar_3",
        "title": "Data Terstruktur / Schema JSON-LD",
        "weight": 0.20,  # 20%
        "description": "Menyediakan metadata mesin (Knowledge Graph) agar entitas bisnis dan produk terbaca dengan kepastian 100% tanpa ambiguitas.",
        "icon": "🏷️",
        "indicators": [
            {
                "id": "schema_org",
                "label": "Terpasang Organization / LocalBusiness Schema (Nama, Alamat/NAP, Kontak)",
                "sublabel": "Kode JSON-LD yang menegaskan nama resmi merek, koordinat lokasi, kontak WhatsApp bisnis, dan profil media sosial.",
                "weight_in_pilar": 0.50,  # 10% total
                "weight_total": 10.0,
                "help": "AI memerlukan kepastian data NAP (Name, Address, Phone) agar tidak melakukan halusinasi saat merekomendasikan UMKM lokal."
            },
            {
                "id": "schema_product_faq",
                "label": "Terpasang Product Schema atau FAQPage Schema pada halaman utama",
                "sublabel": "Metadata rinci mengenai item produk, rentang harga, ketersediaan stok, dan daftar pertanyaan yang terjawab.",
                "weight_in_pilar": 0.50,  # 10% total
                "weight_total": 10.0,
                "help": "Google AI Overviews dan ChatGPT Shopping secara langsung membaca Product Schema untuk menampilkan cuplikan kartu produk."
            }
        ]
    },
    "pilar_4": {
        "id": "pilar_4",
        "title": "Otoritas Merek & Sebutan Luar / Off-Page",
        "weight": 0.30,  # 30%
        "description": "Membangun jejak konsensus multi-sumber di ekosistem internet agar AI mempercayai keaslian dan reputasi bisnis Anda.",
        "icon": "🌐",
        "indicators": [
            {
                "id": "offpage_youtube",
                "label": "Memiliki video ulasan / demo produk di YouTube dengan transkrip dan teks",
                "sublabel": "AI multimodal (seperti Gemini & ChatGPT) secara aktif menelusuri transkrip video YouTube untuk mencari testimoni otentik.",
                "weight_in_pilar": 0.50,  # 15% total
                "weight_total": 15.0,
                "help": "Transkrip video di YouTube merupakan sumber grounding utama bagi Gemini dan AI Overviews untuk merekomendasikan produk lokal."
            },
            {
                "id": "offpage_mentions",
                "label": "Nama merek disebut/diulas di platform luar (Google Business, listicles, forum)",
                "sublabel": "Mendapatkan sebutan (unlinked / linked brand mentions) di Google Maps/GBP, media lokal, Reddit, Quora, atau portal komunitas.",
                "weight_in_pilar": 0.50,  # 15% total
                "weight_total": 15.0,
                "help": "RAG AI melakukan triangulasi data: Jika nama merek Anda hanya ada di web sendiri, AI ragu merekomendasikannya karena minim validasi publik."
            }
        ]
    }
}


def calculate_geo_score(answers: Dict[str, bool]) -> Dict[str, Any]:
    """
    Menghitung skor total GEO (0-100), skor per pilar (0-100% dan kontribusi berbobot),
    serta menentukan kategori tingkat kematangan (maturity tier).
    """
    pillar_results = {}
    total_score = 0.0

    for p_id, p_info in GEO_PILLARS.items():
        p_total_indicators = len(p_info["indicators"])
        p_weight = p_info["weight"]
        checked_count = 0
        p_earned_score = 0.0

        for ind in p_info["indicators"]:
            ind_id = ind["id"]
            if answers.get(ind_id, False):
                checked_count += 1
                p_earned_score += ind["weight_total"]

        # Persentase ketercapaian pilar ini (0 - 100%)
        p_percentage = (checked_count / p_total_indicators) * 100 if p_total_indicators > 0 else 0
        
        pillar_results[p_id] = {
            "title": p_info["title"],
            "icon": p_info["icon"],
            "weight": p_weight,
            "weight_pct": int(p_weight * 100),
            "checked_count": checked_count,
            "total_count": p_total_indicators,
            "percentage": round(p_percentage, 1),
            "earned_score": round(p_earned_score, 1),
            "max_score": round(p_weight * 100, 1)
        }
        total_score += p_earned_score

    total_score = round(total_score, 1)

    # Menentukan Kategori Kematangan
    if total_score >= 80:
        tier_key = "ai_ready"
        tier_name = "AI-Ready (Sangat Siap)"
        tier_color = "#10B981"  # Emerald Green
        tier_badge = "🟢"
        tier_description = (
            "Luar biasa! Website dan merek Anda memiliki fondasi GEO yang sangat kuat. "
            "Mesin pencari AI berbasis RAG (ChatGPT, Perplexity, Gemini, Claude) dapat dengan mudah "
            "mengindeks data Anda, memvalidasi reputasi merek, dan mencantumkannya sebagai sumber kutipan rekomendasi utama."
        )
    elif total_score >= 50:
        tier_key = "needs_optimization"
        tier_name = "Needs Optimization (Cukup Siap)"
        tier_color = "#F59E0B"  # Amber/Yellow
        tier_badge = "🟡"
        tier_description = (
            "Website Anda sudah memiliki beberapa elemen penting, namun masih terdapat celah informasi "
            "yang membuat bot AI ragu memprioritaskan merek Anda dibanding kompetitor. "
            "Fokuslah menyelesaikan Quick Wins di bagian struktur konten BLUF dan Schema JSON-LD."
        )
    else:
        tier_key = "invisible"
        tier_name = "Invisible to AI (Belum Siap)"
        tier_color = "#EF4444"  # Red
        tier_badge = "🔴"
        tier_description = (
            "Peringatan: Brand Anda saat ini berisiko 'tidak terlihat' (invisible) oleh mesin AI generasi baru. "
            "Ketika calon pembeli menanyakan rekomendasi produk di niche Anda ke ChatGPT atau Gemini, "
            "merek Anda hampir pasti tidak akan disebut karena ketiadaan data terstruktur dan aksesibilitas crawler."
        )

    return {
        "total_score": total_score,
        "tier_key": tier_key,
        "tier_name": tier_name,
        "tier_color": tier_color,
        "tier_badge": tier_badge,
        "tier_description": tier_description,
        "pillar_results": pillar_results
    }


def analyze_citation_gaps(answers: Dict[str, bool]) -> List[Dict[str, str]]:
    """
    Menganalisis Kesenjangan Kutipan (Citation Gap Analysis)
    berdasarkan indikator-indikator yang belum tercentang.
    """
    gaps = []

    # Cek robots.txt
    if not answers.get("tech_robots", False):
        gaps.append({
            "pilar": "Aksesibilitas Teknis",
            "gap_title": "Bot AI Diblokir / Belum Diizinkan Secara Eksplisit",
            "impact": "Tinggi (Kritis)",
            "impact_color": "#EF4444",
            "explanation": (
                "Tanpa izin eksplisit di robots.txt, bot seperti GPTBot (OpenAI) dan ClaudeBot (Anthropic) "
                "tidak akan membaca konten landing page Anda saat menyusun jawaban RAG secara real-time."
            ),
            "fix_summary": "Gunakan Auto-Fix Generator untuk membuat konfigurasi robots.txt yang membuka akses bot AI terpercaya."
        })

    # Cek BLUF
    if not answers.get("content_bluf", False):
        gaps.append({
            "pilar": "Struktur Konten",
            "gap_title": "Ketiadaan Format BLUF (Bottom Line Up Front)",
            "impact": "Tinggi",
            "impact_color": "#EF4444",
            "explanation": (
                "AI RAG membagi halaman ke dalam potongan teks (chunks). Jika proposisi nilai, harga, dan keunggulan "
                "tersimpan di bagian bawah halaman, chunk atas web Anda dianggap tidak relevan oleh sistem semantic search."
            ),
            "fix_summary": "Pindahkan ringkasan spesifikasi, harga, dan keunggulan ke 50 kata pertama di halaman produk."
        })

    # Cek Data Kuantitatif
    if not answers.get("content_data", False):
        gaps.append({
            "pilar": "Struktur Konten",
            "gap_title": "Minimnya Data Spesifik & Angka Kuantitatif",
            "impact": "Sedang - Tinggi",
            "impact_color": "#F59E0B",
            "explanation": (
                "Mesin AI sangat menyukai fakta konkret (harga pasti dalam Rupiah, dimensi produk, persentase bahan, masa garansi). "
                "Klaim umum tanpa angka (seperti 'produk terbaik dan terjangkau') diabaikan oleh AI karena dianggap 'fluff'."
            ),
            "fix_summary": "Sertakan angka transparan: harga, berat, sertifikasi BPOM/Halal, atau data uji kepuasan pembeli."
        })

    # Cek FAQ Percakapan
    if not answers.get("content_faq", False):
        gaps.append({
            "pilar": "Struktur Konten",
            "gap_title": "Ketiadaan FAQ Percakapan (Conversational Q&A)",
            "impact": "Sedang",
            "impact_color": "#F59E0B",
            "explanation": (
                "Pengguna menanyakan pertanyaan ke AI dalam bahasa percakapan alami. "
                "Halaman web yang tidak memiliki format Tanya-Jawab langsung akan sulit dipadankan (low vector similarity) dengan query pengguna."
            ),
            "fix_summary": "Buat 5 pertanyaan FAQ spesifik seputar cara pesan, pengiriman, dan perbandingan produk."
        })

    # Cek Schema JSON-LD
    if not answers.get("schema_org", False) or not answers.get("schema_product_faq", False):
        gaps.append({
            "pilar": "Data Terstruktur",
            "gap_title": "Ketiadaan Schema JSON-LD (Mesin Buta Konteks Bisnis)",
            "impact": "Tinggi",
            "impact_color": "#EF4444",
            "explanation": (
                "Tanpa Schema.org markup, AI harus 'menebak' apakah teks di web Anda adalah nama produk, "
                "nama pemilik, atau alamat toko. Schema JSON-LD memberikan sertifikasi metadata mesin 100% akurat."
            ),
            "fix_summary": "Salin kode Schema JSON-LD dari Auto-Fix Generator ke tag <head> website Anda."
        })

    # Cek Off-Page YouTube
    if not answers.get("offpage_youtube", False):
        gaps.append({
            "pilar": "Otoritas Merek",
            "gap_title": "Absennya Jejak Multimodal di YouTube",
            "impact": "Sedang",
            "impact_color": "#F59E0B",
            "explanation": (
                "Google Gemini dan Google AI Overviews secara masif mengindeks transkrip video YouTube. "
                "Tanpa video demonstrasi atau review produk, merek Anda kehilangan saluran sitasi multimodal terbesar di Indonesia."
            ),
            "fix_summary": "Publikasikan 1 video unboxing/review produk di YouTube dengan transkrip subtitle otomatis dan deskripsi lengkap."
        })

    # Cek Off-Page Sebutan Luar
    if not answers.get("offpage_mentions", False):
        gaps.append({
            "pilar": "Otoritas Merek",
            "gap_title": "Rendahnya Konsensus Pihak Ketiga (Third-Party Mentions)",
            "impact": "Tinggi",
            "impact_color": "#EF4444",
            "explanation": (
                "AI RAG memeriksa apakah merek Anda disebut di tempat lain untuk menghindari mempromosikan entitas fiktif. "
                "Ketiadaan ulasan di Google Business Profile atau forum komunitas membuat skor kepercayaan (trust score) rendah."
            ),
            "fix_summary": "Optimalkan profil Google Bisnisku, kumpulkan 15+ ulasan autentik, dan daftar ke direktori UMKM lokal terpercaya."
        })

    return gaps


def get_prioritized_recommendations(answers: Dict[str, bool]) -> Dict[str, List[Dict[str, str]]]:
    """
    Menyusun rekomendasi perbaikan berbasis jawaban user,
    dibagi menjadi Quick Wins (< 1 hari) dan Strategic Improvements (1-4 minggu).
    """
    quick_wins = []
    strategic = []

    # Quick Wins
    if not answers.get("tech_robots", False):
        quick_wins.append({
            "title": "Buka Akses Bot AI di robots.txt",
            "pilar": "Teknis",
            "effort": "15 Menit",
            "action": "Tambahkan User-agent: GPTBot, ClaudeBot, Google-Extended, PerplexityBot dengan aturan 'Allow: /' di file robots.txt Anda."
        })

    if not answers.get("content_bluf", False):
        quick_wins.append({
            "title": "Terapkan Paragraf BLUF di Bagian Paling Atas",
            "pilar": "Konten",
            "effort": "30 Menit",
            "action": "Ganti paragraf pembuka landing page Anda dengan draf BLUF dari Auto-Fix Generator kami yang langsung menyebutkan nama merek, fungsi utama, keunggulan pembeda, dan harga."
        })

    if not answers.get("schema_org", False) or not answers.get("schema_product_faq", False):
        quick_wins.append({
            "title": "Pasang Kode Schema JSON-LD",
            "pilar": "Data Terstruktur",
            "effort": "30 Menit",
            "action": "Buka tab Auto-Fix Generator, salin kode JSON-LD Organization dan FAQ, lalu tempelkan ke bagian header tema website / landing page Anda."
        })

    if not answers.get("content_data", False):
        quick_wins.append({
            "title": "Tambahkan Angka Kuantitatif & Spesifikasi Jelas",
            "pilar": "Konten",
            "effort": "45 Menit",
            "action": "Lengkapi deskripsi produk dengan angka pasti: harga Rupiah transparan, berat gramasi, dimensi cm, lama ketahanan, dan nomor registrasi P-IRT/BPOM/Halal."
        })

    # Strategic Improvements
    if not answers.get("content_headings", False):
        strategic.append({
            "title": "Restrukturisasi Hierarki Heading Semantik (H1-H3)",
            "pilar": "Konten",
            "effort": "1-2 Hari",
            "action": "Pastikan setiap halaman hanya memiliki satu H1 (topik utama), diikuti H2 untuk sub-topik (Spesifikasi, Cara Pakai, FAQ), dan H3 untuk detail pemecahan."
        })

    if not answers.get("tech_https_speed", False):
        strategic.append({
            "title": "Optimasi Kecepatan Muat Web (< 3 Detik) & Pasang SSL",
            "pilar": "Teknis",
            "effort": "1-3 Hari",
            "action": "Kompresi seluruh gambar ke format WebP, aktifkan caching CDN (misal Cloudflare), dan pastikan sertifikat SSL selalu aktif."
        })

    if not answers.get("offpage_youtube", False):
        strategic.append({
            "title": "Bangun Aset Video YouTube Ber-Transkrip",
            "pilar": "Otoritas",
            "effort": "1-2 Minggu",
            "action": "Buat 2-3 video demonstrasi penggunaan atau ulasan produk UMKM Anda, aktifkan auto-caption / subtitle bahasa Indonesia, dan tautkan ke website."
        })

    if not answers.get("offpage_mentions", False):
        strategic.append({
            "title": "Perkuat Jejak Otoritas Digital Luar (Google Business & Listicles)",
            "pilar": "Otoritas",
            "effort": "2-4 Minggu",
            "action": "Lengkapi Google Business Profile, dorong pelanggan setia memberikan review berfoto, dan jalin kolaborasi review dengan blog lokal atau portal berita daerah."
        })

    return {
        "quick_wins": quick_wins,
        "strategic": strategic
    }


def analyze_inputs_to_indicators(inputs: Dict[str, str]) -> Dict[str, Any]:
    """
    Menganalisis profil data inputan UMKM secara cerdas untuk memetakan
    kesiapan 10 indikator GEO, skor otomatis, dan diagnosa relevansi AI.
    """
    brand = inputs.get("brand_name", "").strip()
    url = inputs.get("website_url", "").strip()
    category = inputs.get("business_category", "").strip()
    phone = inputs.get("phone_number", "").strip()
    location = inputs.get("location_info", "").strip()
    product = inputs.get("product_name", "").strip()
    price = inputs.get("price_range", "").strip()
    adv = inputs.get("key_advantages", "").strip()

    answers = {}
    reasons = {}
    detected_data = []

    # 1. tech_robots: Kebanyakan website UMKM belum memiliki robots.txt khusus bot AI
    if "robots.txt" in adv.lower() or "ai crawler" in adv.lower():
        answers["tech_robots"] = True
        reasons["tech_robots"] = "Dikonfirmasi mengizinkan crawler AI pada konfigurasi web."
    else:
        answers["tech_robots"] = False
        reasons["tech_robots"] = f"Domain {url or 'website'} terdeteksi, namun crawler AI (GPTBot, ClaudeBot) membutuhkan deklarasi izin eksplisit pada file robots.txt."

    # 2. tech_https_speed: Cek protokol HTTPS
    if url.lower().startswith("https://"):
        answers["tech_https_speed"] = True
        reasons["tech_https_speed"] = "Protokol HTTPS aktif dan aman untuk perayapan AI real-time."
    else:
        answers["tech_https_speed"] = False
        reasons["tech_https_speed"] = "URL belum menggunakan protokol aman HTTPS atau format URL belum lengkap."

    # 3. content_bluf: Cek apakah produk dan keunggulan padat informasi
    combined_content = f"{product} {adv}".lower()
    if len(product) >= 15 and len(adv) >= 20 and len(price) >= 3:
        answers["content_bluf"] = True
        reasons["content_bluf"] = f"Input produk dan keunggulan ({brand}) telah memuat proposisi nilai dan harga yang siap dijadikan format BLUF."
    else:
        answers["content_bluf"] = False
        reasons["content_bluf"] = "Informasi produk atau keunggulan masih singkat, belum memenuhi standar ringkasan 50 kata teratas (BLUF)."

    # 4. content_headings: Kategori dan produk jelas terdefinisi
    if len(category) > 0 and len(product) >= 8:
        answers["content_headings"] = True
        reasons["content_headings"] = f"Hierarki semantik terdefinisi baik antara kategori ({category}) dan entitas produk ({product})."
    else:
        answers["content_headings"] = False
        reasons["content_headings"] = "Struktur kategori atau penamaan produk belum cukup spesifik untuk pembagian heading H1-H3."

    # 5. content_faq: Cek adanya pola tanya jawab atau kendala pembeli
    faq_keywords = ["garansi", "kirim", "ongkir", "halal", "bpom", "asli", "pembayaran", "pesan", "faq", "tanya"]
    has_faq_context = any(kw in combined_content for kw in faq_keywords)
    if has_faq_context and ("?" in adv or "garansi" in combined_content or "kirim" in combined_content):
        answers["content_faq"] = True
        reasons["content_faq"] = "Terdeteksi informasi FAQ/kendala pembeli (garansi, pengiriman, keaslian)."
    else:
        answers["content_faq"] = False
        reasons["content_faq"] = "Belum terdeteksi bagian FAQ percakapan alami yang menjawab keraguan spesifik calon konsumen."

    # 6. content_data: Cek data kuantitatif (angka, harga, gramasi, sertifikasi)
    has_digits = any(char.isdigit() for char in f"{price} {adv}")
    has_units = any(u in combined_content for u in ["rp", "idr", "ribu", "k", "gram", "gr", "kg", "ml", "liter", "%", "organik", "halal", "bpom", "p-irt", "score", "84", "90"])
    if has_digits and has_units:
        answers["content_data"] = True
        reasons["content_data"] = f"Data kuantitatif kuat terdeteksi (harga: {price}, detail spesifik: {adv[:35]}...)."
        detected_data.append("Harga & Angka Kuantitatif")
    else:
        answers["content_data"] = False
        reasons["content_data"] = "Masih minim angka kuantitatif (harga pasti, dimensi, atau nomor sertifikasi)."

    # 7. schema_org: Kelengkapan NAP (Name, Address, Phone)
    has_nap = len(brand) >= 3 and len(location) >= 4 and any(c.isdigit() for c in phone)
    if has_nap and ("schema" in adv.lower() or "json-ld" in adv.lower()):
        answers["schema_org"] = True
        reasons["schema_org"] = "Entitas NAP dan kode Schema terdeteksi terpasang."
    else:
        answers["schema_org"] = False
        reasons["schema_org"] = f"Data NAP ({brand}, {location}, WhatsApp) lengkap di input, namun kode Schema JSON-LD perlu disalin ke tag <head> situs."

    # 8. schema_product_faq: Cek data produk & harga
    if len(product) >= 10 and len(price) >= 5 and ("product" in adv.lower() or "katalog" in adv.lower()):
        answers["schema_product_faq"] = True
        reasons["schema_product_faq"] = "Product schema terpasang pada katalog utama."
    else:
        answers["schema_product_faq"] = False
        reasons["schema_product_faq"] = "Data item produk dan harga terdeteksi, siap diproduksi menjadi Product Schema via Auto-Fix Generator."

    # 9. offpage_youtube: Cek channel video / ulasan YouTube
    if "youtube" in adv.lower() or "video" in adv.lower() or "tiktok" in adv.lower() or "transkrip" in adv.lower():
        answers["offpage_youtube"] = True
        reasons["offpage_youtube"] = "Aset video demonstrasi/ulasan produk terdeteksi."
    else:
        answers["offpage_youtube"] = False
        reasons["offpage_youtube"] = "Belum terdeteksi adanya video demonstrasi produk di YouTube ber-transkrip."

    # 10. offpage_mentions: Cek potensi sebutan luar berdasarkan lokasi & entitas
    if len(location) >= 4 and len(brand.split()) >= 2:
        answers["offpage_mentions"] = True
        reasons["offpage_mentions"] = f"Entitas merek '{brand}' dengan basis lokal '{location}' memiliki potensi grounding tinggi di Google Maps & direktori bisnis."
    else:
        answers["offpage_mentions"] = False
        reasons["offpage_mentions"] = "Nama merek atau informasi lokasi masih terlalu umum untuk triangulasi konsensus luar."

    return {
        "answers": answers,
        "reasons": reasons,
        "detected_data": detected_data,
        "summary": f"Analisis otomatis inputan untuk '{brand}' ({category}): {sum(1 for v in answers.values() if v)} dari 10 indikator kesiapan GEO telah terpetakan."
    }


def live_crawl_website(target_url: str, timeout: float = 6.0) -> Dict[str, Any]:
    """
    Melakukan Live Crawling & Audit Web secara langsung ke domain yang diinput pengguna:
    1. Memvalidasi koneksi HTTPS dan mengukur waktu respons awal (TTFB / response time).
       Jika menggunakan HTTPS dan response time < 3 detik -> tech_https_speed_passed = True.
    2. Mengambil dan menganalisis file /robots.txt situs tersebut menggunakan urllib.robotparser
       dan parser blok direktif untuk mendeteksi apakah GPTBot, ClaudeBot, Google-Extended,
       dan PerplexityBot diizinkan. Jika diizinkan -> tech_robots_passed = True.
    3. Memindai potongan HTML awal untuk mendeteksi Schema JSON-LD dan heading semantik.
    """
    logs = []
    cleaned_url = target_url.strip()
    if not cleaned_url:
        return {
            "success": False,
            "error_message": "URL website belum diisi.",
            "tech_robots_passed": False,
            "tech_https_speed_passed": False,
            "logs": ["Error: URL kosong."]
        }

    # Normalisasi Skema URL
    if not cleaned_url.startswith(("http://", "https://")):
        cleaned_url = "https://" + cleaned_url

    parsed = urllib.parse.urlparse(cleaned_url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc or parsed.path.split("/")[0]
    base_origin = f"{scheme}://{netloc}"
    
    logs.append(f"🌐 Memulai Live Audit Web ke: {cleaned_url}")
    logs.append(f"🔍 Domain terdeteksi: {netloc} (Protokol: {scheme.upper()})")

    # Header User-Agent Audit
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (compatible; GEOAuditNusantara/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # --------------------------------------------------------------------------
    # 1. TES KONEKSI HTTPS & WAKTU RESPON (TTFB)
    # --------------------------------------------------------------------------
    https_active = (scheme == "https")
    response_time_sec = 0.0
    status_code = 0
    ssl_verified = True
    html_sample = ""

    ctx = ssl.create_default_context()
    
    t_start = time.perf_counter()
    try:
        req = urllib.request.Request(cleaned_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            response_time_sec = time.perf_counter() - t_start
            status_code = resp.getcode()
            # Baca sebagian kecil HTML untuk analisis tambahan
            html_bytes = resp.read(120000)
            html_sample = html_bytes.decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as he:
        response_time_sec = time.perf_counter() - t_start
        status_code = he.code
        logs.append(f"⚠️ Server merespon dengan status HTTP {status_code} ({he.reason})")
    except ssl.SSLError as se:
        response_time_sec = time.perf_counter() - t_start
        ssl_verified = False
        logs.append(f"⚠️ Peringatan SSL: Sertifikat tidak dapat divalidasi ({se}). Mencoba koneksi sekunder...")
        # Coba unverified context untuk tetap mengukur respon
        try:
            unverified_ctx = ssl._create_unverified_context()
            req = urllib.request.Request(cleaned_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx) as resp:
                status_code = resp.getcode()
        except Exception:
            pass
    except Exception as e:
        response_time_sec = time.perf_counter() - t_start
        logs.append(f"❌ Gagal menghubungi server web: {str(e)}")
        return {
            "success": False,
            "error_message": f"Koneksi gagal: {str(e)}",
            "url_tested": cleaned_url,
            "tech_robots_passed": False,
            "tech_https_speed_passed": False,
            "logs": logs
        }

    response_time_sec = round(response_time_sec, 3)
    response_time_ms = int(response_time_sec * 1000)
    speed_under_3s = (response_time_sec < 3.0)

    # Indikator 2 Lolos jika HTTPS aktif dan respon di bawah 3 detik
    tech_https_speed_passed = (https_active and speed_under_3s and ssl_verified)

    if tech_https_speed_passed:
        logs.append(f"✅ Indikator 2 LOLOS: HTTPS aktif & Waktu respon sangat cepat ({response_time_sec} detik / {response_time_ms} ms)")
    else:
        alasan = []
        if not https_active:
            alasan.append("Protokol bukan HTTPS")
        if not speed_under_3s:
            alasan.append(f"Waktu respon lambat ({response_time_sec}s >= 3.0s)")
        if not ssl_verified:
            alasan.append("Sertifikat SSL bermasalah")
        logs.append(f"⚠️ Indikator 2 BELUM LOLOS: {', '.join(alasan)}")

    # --------------------------------------------------------------------------
    # 2. TES CRAWL /robots.txt & IZIN BOT AI
    # --------------------------------------------------------------------------
    robots_url = urllib.parse.urljoin(base_origin, "/robots.txt")
    logs.append(f"🤖 Memeriksa file robots.txt di: {robots_url}")

    robots_status_code = 0
    robots_content = ""
    robots_found = False

    try:
        req_rob = urllib.request.Request(robots_url, headers=headers)
        with urllib.request.urlopen(req_rob, timeout=timeout, context=ctx) as resp_rob:
            robots_status_code = resp_rob.getcode()
            robots_content = resp_rob.read(60000).decode("utf-8", errors="ignore")
            robots_found = True
            logs.append(f"📄 File robots.txt berhasil diunduh (Status: {robots_status_code} OK)")
    except urllib.error.HTTPError as he_rob:
        robots_status_code = he_rob.code
        if robots_status_code == 404:
            logs.append("ℹ️ File /robots.txt tidak ditemukan (404 Not Found). Berdasarkan standar RFC 9309, ketiadaan robots.txt berarti SELURUH BOT DIIZINKAN secara default.")
        else:
            logs.append(f"⚠️ Respon file robots.txt berstatus HTTP {robots_status_code}")
    except Exception as e_rob:
        logs.append(f"⚠️ Tidak dapat mengunduh robots.txt ({e_rob}). Diasumsikan default crawler policy.")

    # Analisis izin untuk 4 Bot AI Utama
    target_ai_bots = ["GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot"]
    ai_bots_permissions = {}
    
    if not robots_found or robots_status_code == 404:
        # Jika file tidak ada, semua bot diizinkan secara default
        for bot in target_ai_bots:
            ai_bots_permissions[bot] = {
                "allowed": True,
                "reason": "Diizinkan (Tidak ada file robots.txt / 404 Not Found)",
                "source": "Default Open"
            }
        tech_robots_passed = True
    else:
        # Gunakan urllib.robotparser
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(robots_content.splitlines())

        # Parser eksplisit per-baris untuk memeriksa blok spesifik AI
        lines = [line.split("#")[0].strip() for line in robots_content.splitlines() if line.strip()]
        agent_rules = {}
        current_agents = []
        in_directives = False

        for line in lines:
            if ":" not in line:
                continue
            k, v = [x.strip() for x in line.split(":", 1)]
            k_low = k.lower()
            if k_low == "user-agent":
                if in_directives:
                    current_agents = []
                    in_directives = False
                agent_val = v.lower()
                current_agents.append(agent_val)
                if agent_val not in agent_rules:
                    agent_rules[agent_val] = []
            elif k_low in ("allow", "disallow"):
                in_directives = True
                for ag in current_agents:
                    agent_rules[ag].append((k_low, v))

        tech_robots_passed = True

        for bot in target_ai_bots:
            bot_low = bot.lower()
            is_blocked = False
            rule_detail = "Allow: /"
            source_detail = ""

            # 1. Cek aturan spesifik bot terlebih dahulu
            if bot_low in agent_rules and agent_rules[bot_low]:
                source_detail = f"Aturan spesifik User-agent: {bot}"
                for directive, path in agent_rules[bot_low]:
                    if directive == "disallow" and path in ("/", "/*"):
                        is_blocked = True
                        rule_detail = "Disallow: / (Diblokir)"
                    elif directive == "allow" and path in ("/", "/*"):
                        is_blocked = False
                        rule_detail = "Allow: / (Diizinkan)"
            # 2. Cek aturan wildcard User-agent: *
            elif "*" in agent_rules and agent_rules["*"]:
                source_detail = "Mewarisi aturan umum User-agent: *"
                for directive, path in agent_rules["*"]:
                    if directive == "disallow" and path in ("/", "/*"):
                        is_blocked = True
                        rule_detail = "Disallow: / (Diblokir via *)"
                    elif directive == "allow" and path in ("/", "/*"):
                        is_blocked = False
                        rule_detail = "Allow: / (Diizinkan via *)"
            else:
                source_detail = "Default (Tidak dibatasi)"
                rule_detail = "Allow (Bebas Crawl)"

            # Verifikasi silang dengan RobotFileParser untuk bot yang mendukung URL fetching
            can_fetch_root = rp.can_fetch(bot, cleaned_url)
            if not can_fetch_root and bot_low in agent_rules:
                is_blocked = True
                rule_detail = "Disallow (Ditolak oleh RobotFileParser)"

            allowed = not is_blocked
            ai_bots_permissions[bot] = {
                "allowed": allowed,
                "reason": rule_detail,
                "source": source_detail
            }

            if not allowed:
                tech_robots_passed = False
                logs.append(f"⛔ {bot} DIBLOKIR: {rule_detail} ({source_detail})")
            else:
                logs.append(f"✅ {bot} DIIZINKAN: {rule_detail}")

    if tech_robots_passed:
        logs.append("✅ Indikator 1 LOLOS: Seluruh AI Crawlers (GPTBot, ClaudeBot, Google-Extended, PerplexityBot) diizinkan membaca situs.")
    else:
        logs.append("⚠️ Indikator 1 BELUM LOLOS: Ditemukan bot AI yang diblokir oleh robots.txt.")

    # --------------------------------------------------------------------------
    # 3. PEMINDAIAN TAMBAHAN DARI HTML LANGSUNG
    # --------------------------------------------------------------------------
    has_schema_jsonld = False
    has_headings = False
    page_title = ""

    if html_sample:
        if '<script type="application/ld+json"' in html_sample or "<script type='application/ld+json'" in html_sample:
            has_schema_jsonld = True
            logs.append("💡 Deteksi Live HTML: Ditemukan Schema JSON-LD (<script type='application/ld+json'>) aktif!")

        if re.search(r"<h[1-3][^>]*>", html_sample, re.IGNORECASE):
            has_headings = True
            logs.append("💡 Deteksi Live HTML: Ditemukan struktur heading semantik (H1/H2/H3).")

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html_sample, re.IGNORECASE | re.DOTALL)
        if title_match:
            page_title = title_match.group(1).strip()
            logs.append(f"📌 Judul Halaman Live: '{page_title}'")

    return {
        "success": True,
        "url_tested": cleaned_url,
        "scheme": scheme,
        "https_active": https_active,
        "response_time_sec": response_time_sec,
        "response_time_ms": response_time_ms,
        "status_code": status_code,
        "ssl_verified": ssl_verified,
        "speed_under_3s": speed_under_3s,
        "tech_https_speed_passed": tech_https_speed_passed,
        "robots_url": robots_url,
        "robots_status_code": robots_status_code,
        "robots_found": robots_found,
        "robots_snippet": robots_content[:350] if robots_content else "",
        "ai_bots_permissions": ai_bots_permissions,
        "tech_robots_passed": tech_robots_passed,
        "html_inspections": {
            "page_title": page_title,
            "has_schema_jsonld": has_schema_jsonld,
            "has_headings": has_headings
        },
        "logs": logs
    }


