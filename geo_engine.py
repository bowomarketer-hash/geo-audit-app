"""
GEO Engine - Modul Kalkulasi, Analisis, dan Rekomendasi
untuk GEO Audit App Nusantara (3 Pilar GEO Riil & Revenue Impact Engine).
"""

from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error
import urllib.parse
import urllib.robotparser
import ssl
import time
import re


# ==============================================================================
# DEFINISI 3 PILAR GEO RIIL (BOBOT TOTAL 100%)
# ==============================================================================
GEO_PILLARS = {
    "pilar_1": {
        "id": "pilar_1",
        "title": "Crawlability & Machine-Readability",
        "weight": 0.30,  # 30%
        "description": "Memastikan mesin dan crawler AI membaca identitas bisnis dengan pasti melalui Schema.org JSON-LD, Open Graph, llms.txt, dan izin robots.txt.",
        "icon": "🤖",
        "indicators": [
            {
                "id": "schema_org",
                "label": "Validasi Schema.org JSON-LD (LocalBusiness / Organization / Product)",
                "sublabel": "Metadata terstruktur Knowledge Graph yang menegaskan nama merek, produk, harga, dan NAP secara pasti.",
                "weight_in_pilar": 0.334,
                "weight_total": 10.0,
                "help": "Model AI RAG membaca JSON-LD untuk memvalidasi atribut harga, legalitas, dan entitas tanpa harus menebak teks mentah."
            },
            {
                "id": "content_metadata_og",
                "label": "Open Graph (OG Tags) & Struktur Konten Semantik (BLUF / Heading)",
                "sublabel": "Tag og:title, og:description, dan hierarki H1-H3 dengan ringkasan proposisi nilai di 50 kata teratas (BLUF).",
                "weight_in_pilar": 0.333,
                "weight_total": 10.0,
                "help": "AI parser memecah dokumen berdasarkan heading dan membaca meta tag untuk menyusun cuplikan jawaban RAG."
            },
            {
                "id": "tech_robots_llmstxt",
                "label": "Aksesibilitas AI Crawlers di robots.txt & Keberadaan berkas /llms.txt",
                "sublabel": "Mengizinkan bot AI (GPTBot, ClaudeBot, PerplexityBot) serta menyediakan ringkasan terstruktur via berkas llms.txt.",
                "weight_in_pilar": 0.333,
                "weight_total": 10.0,
                "help": "Standar baru pemformatan ringkas llms.txt dan robots.txt terbuka adalah syarat mutlak agar situs diindeks mesin pencari generatif."
            }
        ]
    },
    "pilar_2": {
        "id": "pilar_2",
        "title": "Share of Model (AI Visibility)",
        "weight": 0.40,  # 40%
        "description": "Mengukur seberapa sering merek Anda secara konsisten dipanggil dan direkomendasikan AI pada kueri non-branded intent.",
        "icon": "🎯",
        "indicators": [
            {
                "id": "ai_high_intent_visibility",
                "label": "Keterpanggilan pada Non-Branded High-Intent Queries (Siap Beli)",
                "sublabel": "Merek muncul saat calon pembeli mencari: 'Rekomendasi [kategori] terbaik di [lokasi] yang berkualitas/siap pesan'.",
                "weight_in_pilar": 0.50,
                "weight_total": 20.0,
                "help": "Kueri transaksional adalah sumber konversi langsung. Jika brand tidak muncul di sini, terjadi 'Potential Lost Revenue'."
            },
            {
                "id": "ai_exploratory_visibility",
                "label": "Keterpanggilan pada Exploratory & Problem-Solving Queries (Eksplorasi)",
                "sublabel": "Merek muncul saat pengguna menanyakan solusi kendala spesifik atau perbandingan keunggulan produk di niche terkait.",
                "weight_in_pilar": 0.50,
                "weight_total": 20.0,
                "help": "Kueri eksplorasi membangun brand discovery di puncak funnel (top-of-funnel) sebelum keputusan pembelian."
            }
        ]
    },
    "pilar_3": {
        "id": "pilar_3",
        "title": "Grounding & Citations",
        "weight": 0.30,  # 30%
        "description": "Mengukur kehadiran tautan domain resmi sebagai sitasi rujukan terverifikasi serta jejak konsensus pihak ketiga.",
        "icon": "🔗",
        "indicators": [
            {
                "id": "citation_official_domain",
                "label": "Rasio Grounding Domain Resmi Website (Official URL Citations)",
                "sublabel": "Domain website resmi UMKM tercantum sebagai tautan sitasi aktif (markdown link / footnote) dalam jawaban AI.",
                "weight_in_pilar": 0.50,
                "weight_total": 15.0,
                "help": "Sitasi domain resmi membuktikan grounding faktual: AI tidak sekadar menyebut nama, tapi mengarahkan pembeli langsung ke situs Anda."
            },
            {
                "id": "citation_multi_source",
                "label": "Jejak Konsensus Eksternal & Multi-Source Mentions",
                "sublabel": "Nama merek diperkuat oleh ulasan pelanggan, profil Google Business Profile terverifikasi, atau artikel direktori lokal.",
                "weight_in_pilar": 0.50,
                "weight_total": 15.0,
                "help": "AI melakukan triangulasi data lintas platform. Jika merek hanya ada di web sendiri tanpa jejak luar, tingkat keyakinan AI akan rendah."
            }
        ]
    }
}


def normalize_answers(answers: Dict[str, bool]) -> Dict[str, bool]:
    """
    Menyelaraskan kunci indikator dari state checklist lama maupun baru
    ke dalam format 3 pilar yang terstandar.
    """
    norm = {}

    # Pilar 1
    norm["schema_org"] = bool(answers.get("schema_org") or answers.get("schema_product_faq"))
    norm["content_metadata_og"] = bool(answers.get("content_metadata_og") or answers.get("content_bluf") or answers.get("content_headings"))
    norm["tech_robots_llmstxt"] = bool(answers.get("tech_robots_llmstxt") or answers.get("tech_robots"))

    # Pilar 2
    norm["ai_high_intent_visibility"] = bool(answers.get("ai_high_intent_visibility") or answers.get("content_faq") or answers.get("content_data"))
    norm["ai_exploratory_visibility"] = bool(answers.get("ai_exploratory_visibility") or answers.get("offpage_youtube"))

    # Pilar 3
    norm["citation_official_domain"] = bool(answers.get("citation_official_domain") or answers.get("tech_https_speed"))
    norm["citation_multi_source"] = bool(answers.get("citation_multi_source") or answers.get("offpage_mentions"))

    return norm


def calculate_geo_score(
    answers: Dict[str, bool],
    sampling_data: Optional[Dict[str, Any]] = None,
    citation_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Menghitung skor total GEO (skala 0-100 transparan) berbasis 3 Pilar:
    - Pilar 1: Crawlability & Machine-Readability (30 Poin)
    - Pilar 2: Share of Model / AI Visibility (40 Poin)
    - Pilar 3: Grounding & Citations (30 Poin)
    
    Jika data sampling AI (sampling_data) tersedia, skor Pilar 2 akan dihitung
    secara real-time berdasarkan Citation Probability Score (5-Time Sampling).
    """
    norm_answers = normalize_answers(answers)
    pillar_results = {}
    total_score = 0.0

    for p_id, p_info in GEO_PILLARS.items():
        p_total_indicators = len(p_info["indicators"])
        p_weight = p_info["weight"]
        checked_count = 0
        p_earned_score = 0.0

        if p_id == "pilar_2" and sampling_data and "probability_score" in sampling_data:
            # Kalkulasi dinamis Pilar 2 dari hasil sampling nyata
            prob = float(sampling_data.get("probability_score", 0.0))
            p_earned_score = round((prob / 100.0) * (p_weight * 100.0), 1)
            p_percentage = prob
            checked_count = int(round((prob / 100.0) * p_total_indicators))
        else:
            for ind in p_info["indicators"]:
                ind_id = ind["id"]
                if norm_answers.get(ind_id, False):
                    checked_count += 1
                    p_earned_score += ind["weight_total"]
            p_percentage = (checked_count / p_total_indicators) * 100 if p_total_indicators > 0 else 0.0

        p_earned_score = min(p_earned_score, round(p_weight * 100.0, 1))
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

    total_score = min(round(total_score, 1), 100.0)

    # Kategori Kematangan (Maturity Tiers)
    if total_score >= 80.0:
        tier_key = "ai_ready"
        tier_name = "AI-Ready (Sangat Siap)"
        tier_color = "#10B981"  # Emerald Green
        tier_badge = "🟢"
        tier_description = (
            "Luar biasa! Website dan merek Anda memiliki fondasi GEO yang sangat prima (80-100). "
            "Mesin pencari AI berbasis RAG (ChatGPT, Perplexity, Gemini, Claude) dapat mengindeks data Anda, "
            "memvalidasi entitas bisnis, dan secara konsisten merekomendasikannya sebagai rujukan utama."
        )
    elif total_score >= 50.0:
        tier_key = "needs_optimization"
        tier_name = "Needs Optimization (Cukup Siap)"
        tier_color = "#F59E0B"  # Amber
        tier_badge = "🟡"
        tier_description = (
            "Website Anda sudah memiliki beberapa elemen penting, namun masih terdapat celah visibilitas (50-79). "
            "Sering kali AI ragu menyebutkan merek Anda pada kueri siap beli karena minimnya Schema harga atau llms.txt. "
            "Selesaikan rekomendasi Quick Wins untuk mengamankan peluang transaksi."
        )
    else:
        tier_key = "invisible"
        tier_name = "Invisible to AI (Belum Siap)"
        tier_color = "#EF4444"  # Red
        tier_badge = "🔴"
        tier_description = (
            "Peringatan: Merek Anda saat ini berisiko 'tidak terlihat' (invisible) oleh mesin AI generasi baru (0-49). "
            "Ketika calon pembeli menanyakan rekomendasi produk di bidang Anda, AI akan merekomendasikan kompetitor "
            "karena ketiadaan data terstruktur dan aksesibilitas mesin."
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


def analyze_revenue_impact_and_weaknesses(
    brand_name: str,
    category: str,
    product_name: str,
    location: str,
    answers: Dict[str, bool],
    sampling_audit: Optional[Dict[str, Any]] = None,
    competitors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Menganalisis korelasi bisnis, deteksi kelemahan spesifik LLM,
    serta potensi kehilangan omzet (Potential Lost Revenue) berdasarkan Buyer Intent.
    """
    b_name = brand_name.strip() or "Merek Anda"
    cat = category.strip() or "Produk & Layanan"
    prod = product_name.strip() or f"Produk Unggulan {b_name}"
    loc = location.strip() or "Indonesia"
    comps = competitors or ["Kompetitor Utama"]
    main_comp = comps[0] if comps else "Kompetitor Pasar"

    norm_answers = normalize_answers(answers)
    specific_weaknesses = []

    # 1. Deteksi Kelemahan Spesifik
    if not norm_answers.get("schema_org", False):
        specific_weaknesses.append({
            "code": "missing_schema",
            "category": "Data Terstruktur",
            "title": "Ketiadaan Schema.org JSON-LD (Product & LocalBusiness)",
            "impact": "Kritis",
            "impact_color": "#EF4444",
            "explanation": (
                "AI tidak dapat membaca entitas bisnis, rentang harga, atau nomor izin edar secara terstruktur. "
                f"Akibatnya, saat calon pembeli menanyakan harga pasti {prod}, AI memilih merujuk katalog {main_comp}."
            ),
            "solution": "Salin kode Schema Product & LocalBusiness dari tab Auto-Fix Generator ke tag <head> web Anda."
        })

    if not norm_answers.get("tech_robots_llmstxt", False):
        specific_weaknesses.append({
            "code": "missing_llmstxt",
            "category": "Aksesibilitas Mesin",
            "title": "Ketiadaan Berkas llms.txt & Potensi Pemblokiran Bot AI",
            "impact": "Tinggi",
            "impact_color": "#F59E0B",
            "explanation": (
                "Crawler AI (GPTBot, ClaudeBot, PerplexityBot) tidak memiliki dokumen ringkasan machine-readable resmi. "
                "Hal ini menyebabkan AI rawan berhalusinasi atau mengabaikan web Anda dalam retrieval RAG."
            ),
            "solution": "Unggah berkas /llms.txt standar di root domain dan pastikan robots.txt mengizinkan bot AI."
        })

    if not norm_answers.get("content_metadata_og", False):
        specific_weaknesses.append({
            "code": "missing_bluf_og",
            "category": "Struktur Konten",
            "title": "Format Proposisi Nilai Belum Menerapkan BLUF",
            "impact": "Tinggi",
            "impact_color": "#EF4444",
            "explanation": (
                "Proposisi nilai, harga, dan keunggulan terkubur di bagian tengah/bawah halaman. "
                "Parser chunking AI hanya mengambil potongan teks teratas dokumen dan menganggap web Anda kurang relevan."
            ),
            "solution": "Letakkan ringkasan 50 kata pertama (BLUF) berisi nama merek, keunggulan, dan harga di bagian paling atas."
        })

    if not norm_answers.get("citation_multi_source", False):
        specific_weaknesses.append({
            "code": "low_grounding",
            "category": "Otoritas & Grounding",
            "title": "Minimnya Jejak Konsensus Pihak Ketiga (Off-Page Grounding)",
            "impact": "Sedang",
            "impact_color": "#F59E0B",
            "explanation": (
                f"AI melakukan validasi silang data di internet. Jika nama {b_name} hanya muncul di situs sendiri tanpa "
                f"ulasan Google Business Profile atau direktori lokal {loc}, skor kepercayaan AI akan menurun."
            ),
            "solution": f"Lengkapi Google Business Profile di {loc}, minta 15+ ulasan autentik, dan daftar ke kurasi bisnis lokal."
        })

    # 2. Klasifikasi Buyer Intent & Evaluasi Visibilitas
    prob_score = sampling_audit.get("probability_score", 0.0) if sampling_audit else (
        80.0 if norm_answers.get("ai_high_intent_visibility") else 20.0
    )

    high_intent_mentioned = prob_score >= 60.0
    exploratory_mentioned = prob_score >= 40.0

    intent_breakdown = {
        "high_intent": {
            "type": "Non-Branded High-Intent (Siap Beli)",
            "query_example": f"Rekomendasikan {cat} terbaik asli dari {loc} yang berkualitas tinggi dan siap dipesan sekarang.",
            "intent_description": "Calon pembeli berdaya beli aktif yang berada di tahap akhir pertimbangan transaksi.",
            "is_mentioned": high_intent_mentioned,
            "status_label": "🟢 Direkomendasikan AI (Terkonversi)" if high_intent_mentioned else "🔴 Diabaikan AI (Peluang Lepas)",
            "has_lost_revenue": not high_intent_mentioned,
            "alert_title": "⚠️ POTENTIAL LOST REVENUE ALERT" if not high_intent_mentioned else "✅ Revenue Opportunity Secured",
            "alert_description": (
                f"Calon pembeli siap beli yang menanyakan {cat} di {loc} dialihkan AI ke kompetitor ({main_comp}). "
                f"Terjadi potensi kebocoran transaksi langsung bagi {b_name}!"
                if not high_intent_mentioned else
                f"Merek {b_name} berhasil masuk dalam daftar rekomendasi transaksi AI pada kueri komersial tinggi."
            )
        },
        "exploratory": {
            "type": "Exploratory & Problem-Solving (Pencarian Solusi)",
            "query_example": f"Apa solusi {cat} yang paling efisien, berkualitas, dan terpercaya untuk kebutuhan jangka panjang?",
            "intent_description": "Pengguna yang membandingkan alternatif solusi di puncak funnel (top-of-funnel).",
            "is_mentioned": exploratory_mentioned,
            "status_label": "🟢 Muncul dalam Komparasi" if exploratory_mentioned else "🔴 Belum Masuk Komparasi",
            "has_lost_revenue": False
        }
    }

    # 3. Tiga Langkah Aksi Prioritas (Action Steps)
    priority_action_steps = [
        {
            "priority": "1. Quick Win",
            "timeframe": "< 1 Hari",
            "badge_color": "#10B981",
            "title": "Salin Schema JSON-LD & Terapkan Format BLUF",
            "description": (
                "Buka tab Auto-Fix Generator. Salin kode Schema LocalBusiness dan Product serta draf BLUF, "
                "lalu tempelkan pada tag <head> dan baris pertama halaman utama website Anda."
            ),
            "expected_impact": "Mencegah kesalahan halusinasi harga dan membuat AI membaca entitas bisnis secara instan."
        },
        {
            "priority": "2. Medium-Term",
            "timeframe": "1 - 2 Minggu",
            "badge_color": "#3B82F6",
            "title": "Terbitkan Berkas /llms.txt & Conversational FAQ",
            "description": (
                f"Buat berkas /llms.txt di root domain Anda dan tambahkan 5 Tanya-Jawab percakapan yang membahas "
                f"spesifikasi {prod}, transparansi harga, dan cara pemesanan."
            ),
            "expected_impact": "Meningkatkan vector similarity saat pengguna bertanya dalam bahasa alami ke ChatGPT/Perplexity."
        },
        {
            "priority": "3. Strategic / Digital PR",
            "timeframe": "2 - 4 Minggu",
            "badge_color": "#8B5CF6",
            "title": "Bangun Grounding Konsensus Eksternal & GBP",
            "description": (
                f"Verifikasi Google Business Profile di {loc}, minta ulasan berkala berfoto dari pelanggan, "
                f"dan jalin publikasi kurasi listicle ulasan dengan media atau komunitas daerah."
            ),
            "expected_impact": "Memperkuat skor grounding multi-sumber sehingga AI merekomendasikan brand Anda di atas kompetitor."
        }
    ]

    return {
        "brand_name": b_name,
        "category": cat,
        "main_competitor": main_comp,
        "specific_weaknesses": specific_weaknesses,
        "intent_breakdown": intent_breakdown,
        "priority_action_steps": priority_action_steps,
        "has_lost_revenue_alert": intent_breakdown["high_intent"]["has_lost_revenue"]
    }


def analyze_citation_gaps(answers: Dict[str, bool]) -> List[Dict[str, str]]:
    """
    Menganalisis kesenjangan sitasi (Citation Gap Analysis)
    berdasarkan 3 Pilar GEO.
    """
    norm = normalize_answers(answers)
    gaps = []

    if not norm.get("schema_org", False):
        gaps.append({
            "pilar": "Crawlability & Machine-Readability",
            "gap_title": "Ketiadaan Schema.org JSON-LD Terstruktur",
            "impact": "Tinggi (Kritis)",
            "impact_color": "#EF4444",
            "explanation": "Mesin AI tidak memiliki data entitas pasti terkait nama produk, harga, dan NAP bisnis Anda.",
            "fix_summary": "Pasang kode Schema LocalBusiness & Product dari Auto-Fix Generator ke tag <head>."
        })

    if not norm.get("tech_robots_llmstxt", False):
        gaps.append({
            "pilar": "Crawlability & Machine-Readability",
            "gap_title": "Akses Bot AI Belum Terbuka / Ketiadaan llms.txt",
            "impact": "Tinggi",
            "impact_color": "#EF4444",
            "explanation": "Bot crawler AI (GPTBot, ClaudeBot, Perplexity) tidak diizinkan atau tidak menemukan ringkasan llms.txt.",
            "fix_summary": "Perbarui robots.txt dan pasang berkas /llms.txt di root domain."
        })

    if not norm.get("content_metadata_og", False):
        gaps.append({
            "pilar": "Crawlability & Machine-Readability",
            "gap_title": "Ketiadaan Open Graph & Ringkasan BLUF Teratas",
            "impact": "Sedang - Tinggi",
            "impact_color": "#F59E0B",
            "explanation": "Chunk awal web tidak memuat ringkasan harga dan keunggulan produk sehingga dilewati dalam RAG.",
            "fix_summary": "Terapkan format BLUF di 50 kata teratas dan pasang Open Graph meta tags."
        })

    if not norm.get("ai_high_intent_visibility", False):
        gaps.append({
            "pilar": "Share of Model (AI Visibility)",
            "gap_title": "Merek Absen pada Kueri Siap Beli (Potential Lost Revenue)",
            "impact": "Tinggi (Finansial)",
            "impact_color": "#EF4444",
            "explanation": "Calon pembeli berdaya beli tinggi yang bertanya rekomendasi ke AI saat ini dialihkan ke kompetitor.",
            "fix_summary": "Perkuat optimasi FAQ percakapan transaksional dan cantumkan harga transparan."
        })

    if not norm.get("citation_official_domain", False):
        gaps.append({
            "pilar": "Grounding & Citations",
            "gap_title": "Rasio Sitasi Tautan Domain Resmi Rendah",
            "impact": "Sedang",
            "impact_color": "#F59E0B",
            "explanation": "AI tidak mencantumkan URL website resmi sebagai rujukan, sehingga konversi klik langsung minim.",
            "fix_summary": "Perbaiki canonical tags dan perkuat konsistensi penulisan domain di seluruh kanal digital."
        })

    if not norm.get("citation_multi_source", False):
        gaps.append({
            "pilar": "Grounding & Citations",
            "gap_title": "Minimnya Jejak Otoritas Luar (Triangulasi Konsensus Lemah)",
            "impact": "Sedang - Tinggi",
            "impact_color": "#F59E0B",
            "explanation": "Ketiadaan ulasan pihak ketiga membuat AI ragu terhadap kredibilitas dan keaslian bisnis.",
            "fix_summary": "Lengkapi profil Google Business, kumpulkan ulasan berfoto, dan daftarkan situs ke direktori daerah."
        })

    return gaps


def get_prioritized_recommendations(answers: Dict[str, bool]) -> Dict[str, List[Dict[str, str]]]:
    """
    Menyusun rekomendasi perbaikan berbasis 3 Pilar GEO,
    dibagi menjadi Quick Wins (< 1 hari) dan Strategic Improvements (1-4 minggu).
    """
    norm = normalize_answers(answers)
    quick_wins = []
    strategic = []

    if not norm.get("schema_org", False):
        quick_wins.append({
            "title": "Pasang Schema JSON-LD LocalBusiness & Product",
            "pilar": "Crawlability",
            "effort": "20 Menit",
            "action": "Salin kode JSON-LD dari tab Auto-Fix Generator ke tag <head> halaman utama website Anda."
        })

    if not norm.get("content_metadata_og", False):
        quick_wins.append({
            "title": "Terapkan Paragraf BLUF di 50 Kata Teratas",
            "pilar": "Machine-Readability",
            "effort": "30 Menit",
            "action": "Letakkan ringkasan spesifikasi, harga, dan keunggulan pembeda di baris pertama halaman produk."
        })

    if not norm.get("tech_robots_llmstxt", False):
        quick_wins.append({
            "title": "Terbitkan robots.txt Terbuka & Berkas llms.txt",
            "pilar": "Crawlability",
            "effort": "20 Menit",
            "action": "Unggah berkas /llms.txt dan izinkan User-agent GPTBot, ClaudeBot, serta PerplexityBot."
        })

    if not norm.get("ai_high_intent_visibility", False):
        strategic.append({
            "title": "Optimasi Conversational FAQ untuk Kueri Siap Beli",
            "pilar": "AI Visibility",
            "effort": "1-2 Hari",
            "action": "Tambahkan Tanya-Jawab alami yang menjawab keraguan harga, legalitas garansi, dan pengiriman."
        })

    if not norm.get("citation_multi_source", False):
        strategic.append({
            "title": "Bangun Jejak Konsensus Multi-Platform & Google Business Profile",
            "pilar": "Grounding",
            "effort": "2-3 Minggu",
            "action": "Lengkapi Google Business Profile lokal, kumpulkan 15+ review asli, dan jalin kurasi media lokal."
        })

    return {
        "quick_wins": quick_wins,
        "strategic": strategic
    }


def analyze_inputs_to_indicators(inputs: Dict[str, str]) -> Dict[str, Any]:
    """
    Menganalisis profil data inputan UMKM secara cerdas untuk memetakan
    kesiapan 3 pilar GEO secara otomatis.
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

    combined_text = f"{brand} {product} {category} {adv} {location}".lower()

    # 1. schema_org
    has_nap = len(brand) >= 2 and len(location) >= 3 and any(c.isdigit() for c in phone)
    if has_nap and ("schema" in adv.lower() or "json-ld" in adv.lower()):
        answers["schema_org"] = True
        reasons["schema_org"] = "Entitas NAP dan deklarasi Schema terdeteksi."
    else:
        answers["schema_org"] = False
        reasons["schema_org"] = "Data NAP lengkap di input, namun kode Schema JSON-LD perlu disalin ke tag <head> situs."

    # 2. content_metadata_og
    if len(product) >= 8 and len(adv) >= 15 and len(price) >= 3:
        answers["content_metadata_og"] = True
        reasons["content_metadata_og"] = f"Input produk ({product}) dan keunggulan memenuhi kriteria draf BLUF & Open Graph."
        detected_data.append("Proposisi Nilai BLUF Siap Pasang")
    else:
        answers["content_metadata_og"] = False
        reasons["content_metadata_og"] = "Informasi produk atau keunggulan masih singkat untuk pembentukan BLUF komprehensif."

    # 3. tech_robots_llmstxt
    if "robots.txt" in adv.lower() or "llms.txt" in adv.lower():
        answers["tech_robots_llmstxt"] = True
        reasons["tech_robots_llmstxt"] = "Dikonfirmasi mengizinkan crawler AI pada konfigurasi web."
    else:
        answers["tech_robots_llmstxt"] = False
        reasons["tech_robots_llmstxt"] = "Crawler AI membutuhkan deklarasi izin eksplisit di robots.txt dan ringkasan di llms.txt."

    # 4. ai_high_intent_visibility
    has_price_digits = any(char.isdigit() for char in price)
    if has_price_digits and len(product) >= 5:
        answers["ai_high_intent_visibility"] = True
        reasons["ai_high_intent_visibility"] = f"Produk ({product}) memiliki harga transparan ({price}), siap dikonversi pada kueri siap beli."
        detected_data.append("Data Transaksi & Harga")
    else:
        answers["ai_high_intent_visibility"] = False
        reasons["ai_high_intent_visibility"] = "Harga atau spesifikasi produk belum transparan untuk kueri siap beli."

    # 5. ai_exploratory_visibility
    if len(adv) >= 20 and len(category) >= 3:
        answers["ai_exploratory_visibility"] = True
        reasons["ai_exploratory_visibility"] = "Keunggulan pembeda cukup kuat untuk kueri eksplorasi dan perbandingan."
    else:
        answers["ai_exploratory_visibility"] = False
        reasons["ai_exploratory_visibility"] = "Perlu memperkuat narasi pembeda unik dibanding kompetitor sejenis."

    # 6. citation_official_domain
    if url.lower().startswith("https://"):
        answers["citation_official_domain"] = True
        reasons["citation_official_domain"] = "Domain resmi menggunakan protokol HTTPS yang aman untuk sitasi rujukan AI."
    else:
        answers["citation_official_domain"] = False
        reasons["citation_official_domain"] = "URL resmi belum menggunakan HTTPS atau format URL belum lengkap."

    # 7. citation_multi_source
    if len(location) >= 4 and len(brand.split()) >= 1:
        answers["citation_multi_source"] = True
        reasons["citation_multi_source"] = f"Entitas merek '{brand}' di {location} siap digrounding ke Google Business & direktori lokal."
    else:
        answers["citation_multi_source"] = False
        reasons["citation_multi_source"] = "Nama merek atau informasi domisili masih terlalu umum untuk triangulasi konsensus luar."

    return {
        "answers": answers,
        "reasons": reasons,
        "detected_data": detected_data,
        "summary": f"Analisis otomatis untuk '{brand}' ({category}): Kesiapan 3 Pilar GEO terpetakan."
    }


def live_crawl_website(target_url: str, timeout: float = 6.0) -> Dict[str, Any]:
    """
    Melakukan Live Crawling & Audit Web secara langsung:
    1. Validasi HTTPS & waktu respons (TTFB).
    2. Unduh dan analisis /robots.txt untuk izin bot AI (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).
    3. Cek keberadaan berkas /llms.txt pada root server.
    4. Pindai tag Open Graph (og:title, og:description, og:image) dan Schema JSON-LD dari HTML live.
    """
    logs = []
    cleaned_url = target_url.strip()
    if not cleaned_url:
        return {
            "success": False,
            "error_message": "URL website belum diisi.",
            "tech_robots_passed": False,
            "tech_https_speed_passed": False,
            "has_llms_txt": False,
            "has_open_graph": False,
            "logs": ["Error: URL kosong."]
        }

    if not cleaned_url.startswith(("http://", "https://")):
        cleaned_url = "https://" + cleaned_url

    parsed = urllib.parse.urlparse(cleaned_url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc or parsed.path.split("/")[0]
    base_origin = f"{scheme}://{netloc}"

    logs.append(f"🌐 Memulai Live Audit Web ke: {cleaned_url}")
    logs.append(f"🔍 Domain terdeteksi: {netloc} (Protokol: {scheme.upper()})")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GEOAuditNusantara/2.0; +https://geoaudit.id)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # 1. TES HTTPS & WAKTU RESPON
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
            html_bytes = resp.read(120000)
            html_sample = html_bytes.decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as he:
        response_time_sec = time.perf_counter() - t_start
        status_code = he.code
        logs.append(f"⚠️ Server merespon dengan status HTTP {status_code} ({he.reason})")
    except ssl.SSLError as se:
        response_time_sec = time.perf_counter() - t_start
        ssl_verified = False
        logs.append(f"⚠️ Peringatan SSL: Sertifikat tidak valid ({se}). Mencoba koneksi sekunder...")
        try:
            unverified_ctx = ssl._create_unverified_context()
            req = urllib.request.Request(cleaned_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx) as resp:
                status_code = resp.getcode()
                html_sample = resp.read(60000).decode("utf-8", errors="ignore")
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
            "has_llms_txt": False,
            "has_open_graph": False,
            "logs": logs
        }

    response_time_sec = round(response_time_sec, 3)
    response_time_ms = int(response_time_sec * 1000)
    speed_under_3s = (response_time_sec < 3.0)
    tech_https_speed_passed = (https_active and speed_under_3s and ssl_verified)

    if tech_https_speed_passed:
        logs.append(f"✅ HTTPS & Kecepatan: Waktu respons prima ({response_time_sec}s / {response_time_ms} ms)")
    else:
        logs.append(f"⚠️ Kecepatan/Keamanan: Waktu respons {response_time_sec}s")

    # 2. TES /robots.txt
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
            logs.append(f"📄 robots.txt ditemukan (Status: {robots_status_code} OK)")
    except urllib.error.HTTPError as he_rob:
        robots_status_code = he_rob.code
        if robots_status_code == 404:
            logs.append("ℹ️ robots.txt tidak ditemukan (404). Default RFC 9309: Seluruh bot diizinkan.")
    except Exception as e_rob:
        logs.append(f"⚠️ Peringatan robots.txt: {str(e_rob)}")

    target_ai_bots = ["GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot"]
    ai_bots_permissions = {}
    tech_robots_passed = True

    if not robots_found or robots_status_code == 404:
        for bot in target_ai_bots:
            ai_bots_permissions[bot] = {"allowed": True, "reason": "Diizinkan secara default (404 Open)", "source": "RFC 9309"}
    else:
        # Pindai aturan Disallow untuk bot AI
        rob_lower = robots_content.lower()
        for bot in target_ai_bots:
            bot_tag = f"user-agent: {bot.lower()}"
            is_blocked = False
            if bot_tag in rob_lower:
                part = rob_lower.split(bot_tag)[1].split("user-agent:")[0]
                if "disallow: /" in part and "allow: /" not in part:
                    is_blocked = True
            elif "user-agent: *" in rob_lower:
                part = rob_lower.split("user-agent: *")[1].split("user-agent:")[0]
                if "disallow: /" in part and "allow: /" not in part:
                    is_blocked = True

            ai_bots_permissions[bot] = {
                "allowed": not is_blocked,
                "reason": "Disallow: /" if is_blocked else "Allow: /",
                "source": "robots.txt direktif"
            }
            if is_blocked:
                tech_robots_passed = False

    # 3. TES KEBERADAAN /llms.txt
    llms_url = urllib.parse.urljoin(base_origin, "/llms.txt")
    has_llms_txt = False
    llms_status_code = 0
    try:
        req_llm = urllib.request.Request(llms_url, headers=headers)
        with urllib.request.urlopen(req_llm, timeout=timeout, context=ctx) as resp_llm:
            llms_status_code = resp_llm.getcode()
            if llms_status_code == 200:
                has_llms_txt = True
                logs.append(f"✅ Deteksi llms.txt: Ditemukan berkas standar /llms.txt aktif di {llms_url}!")
    except Exception:
        logs.append(f"ℹ️ Berkas /llms.txt belum terdeteksi (Gunakan Auto-Fix Generator untuk membuatnya).")

    # 4. PEMINDAIAN TAG HTML (OPEN GRAPH & SCHEMA JSON-LD)
    has_schema_jsonld = False
    has_open_graph = False
    has_headings = False
    page_title = ""

    if html_sample:
        if '<script type="application/ld+json"' in html_sample or "<script type='application/ld+json'" in html_sample:
            has_schema_jsonld = True
            logs.append("💡 Deteksi Live HTML: Ditemukan Schema.org JSON-LD aktif!")

        if 'property="og:title"' in html_sample.lower() or 'property="og:description"' in html_sample.lower() or 'name="og:title"' in html_sample.lower():
            has_open_graph = True
            logs.append("💡 Deteksi Live HTML: Ditemukan Open Graph metadata tags (og:title / og:description)!")

        if re.search(r"<h[1-3][^>]*>", html_sample, re.IGNORECASE):
            has_headings = True

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
        "has_llms_txt": has_llms_txt,
        "has_open_graph": has_open_graph,
        "html_inspections": {
            "page_title": page_title,
            "has_schema_jsonld": has_schema_jsonld,
            "has_open_graph": has_open_graph,
            "has_headings": has_headings
        },
        "logs": logs
    }
