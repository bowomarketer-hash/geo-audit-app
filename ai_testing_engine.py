"""
ai_testing_engine.py
Modul Analisis & Pengujian AI Otomatis untuk GEO Audit App Nusantara.

Menyediakan:
1. Brand Mention Detector (Status, Frekuensi, Posisi, Sentimen)
2. Citation Link Extractor (Ekstraksi URL, Kategorisasi 5 Sumber, Deteksi Aset Merek)
3. Citation Gap Map (Matriks Kesenjangan, Share of Voice, Auto-Actionable Insights)
4. Simulasi RAG Multi-Mesin (ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews)
5. Live API Connector (OpenAI, Perplexity) via urllib.request
"""

import re
import json
import csv
import io
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple


# ==============================================================================
# 1. DEFINISI MESIN AI & BENCHMARK PRESETS
# ==============================================================================

AI_ENGINES = {
    "chatgpt": {
        "id": "chatgpt",
        "name": "ChatGPT (OpenAI SearchGPT / GPT-4o)",
        "icon": "🟢",
        "type": "Conversational RAG + Web Browsing",
        "provider": "OpenAI",
        "color": "#10a37f"
    },
    "perplexity": {
        "id": "perplexity",
        "name": "Perplexity AI (Sonar / Sonar Pro)",
        "icon": "🔵",
        "type": "Direct Answer Engine + Live Footnotes",
        "provider": "Perplexity",
        "color": "#22b8cf"
    },
    "claude": {
        "id": "claude",
        "name": "Claude (Anthropic 3.5 Sonnet)",
        "icon": "🟣",
        "type": "Long-context Synthesis + Citation Analysis",
        "provider": "Anthropic",
        "color": "#d97706"
    },
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini (1.5 Flash / Pro)",
        "icon": "✨",
        "type": "Multimodal Knowledge Graph + YouTube Grounding",
        "provider": "Google",
        "color": "#3b82f6"
    },
    "google_aio": {
        "id": "google_aio",
        "name": "Google AI Overviews (SGE Simulator)",
        "icon": "🌐",
        "type": "Zero-Click AI Snippet + Carousel Sources",
        "provider": "Google",
        "color": "#ea4335"
    }
}

CITATION_CATEGORIES = {
    "brand_website": {
        "id": "brand_website",
        "name": "Website Resmi Merek",
        "icon": "🌐",
        "badge_color": "#059669",
        "description": "Tautan langsung ke landing page atau domain resmi milik UMKM."
    },
    "youtube_video": {
        "id": "youtube_video",
        "name": "Video YouTube & Transkrip",
        "icon": "📹",
        "badge_color": "#dc2626",
        "description": "Video review, unboxing, atau tutorial dengan grounding transkrip teks."
    },
    "news_media": {
        "id": "news_media",
        "name": "Media News / Listicles Pihak Ketiga",
        "icon": "📰",
        "badge_color": "#2563eb",
        "description": "Artikel kurasi '10 Produk Terbaik', ulasan media berita lokal/nasional."
    },
    "community_forum": {
        "id": "community_forum",
        "name": "Forum Komunitas / Diskusi",
        "icon": "💬",
        "badge_color": "#7c3aed",
        "description": "Diskusi autentik di Reddit, Quora, Kaskus, atau Kompasiana."
    },
    "local_business": {
        "id": "local_business",
        "name": "Profil Bisnis Lokal (Google Business)",
        "icon": "📍",
        "badge_color": "#d97706",
        "description": "Peta lokasi NAP, Google Maps, dan ulasan pelanggan lokal."
    },
    "marketplace": {
        "id": "marketplace",
        "name": "Marketplace / E-Commerce",
        "icon": "📦",
        "badge_color": "#0284c7",
        "description": "Halaman produk di Shopee, Tokopedia, Blibli, atau TikTok Shop."
    },
    "other": {
        "id": "other",
        "name": "Web Pihak Ketiga Lainnya",
        "icon": "🔗",
        "badge_color": "#64748b",
        "description": "Blog independen, direktori umum, atau situs referensi sekunder."
    }
}


def build_benchmark_queries(brand_name: str, product_name: str, category: str, location: str) -> List[Dict[str, str]]:
    """
    Menghasilkan 5 kueri pencarian percakapan benchmark yang merefleksikan
    kebiasaan nyata calon pembeli saat bertanya ke mesin AI RAG.
    """
    b_name = brand_name.strip() or "Merek Anda"
    p_name = product_name.strip() or "Produk Unggulan"
    cat = category.strip() or "Produk Lokal"
    loc = location.split(",")[0].strip() if "," in location else (location.strip() or "Nusantara")

    return [
        {
            "id": "q_trans",
            "type": "Transaksional / Rekomendasi Pembelian",
            "prompt": f"Rekomendasikan {cat} terbaik asli dari {loc} yang berkualitas tinggi dan cocok untuk oleh-oleh atau konsumsi harian.",
            "intent": "AI mencari daftar produk terbaik berdasarkan reputasi dan ulasan."
        },
        {
            "id": "q_brand_compare",
            "type": "Komparasi Niche & Pembeda",
            "prompt": f"Apa keunggulan {b_name} dibanding kompetitor sejenis di bidang {cat}? Apakah sepadan dengan harganya?",
            "intent": "AI menguji pemahaman entitas spesifik terhadap nama merek Anda."
        },
        {
            "id": "q_trust_cert",
            "type": "Validasi Fakta, Harga, & Izin Legalitas",
            "prompt": f"Berapa kisaran harga {p_name} dan apakah produk {b_name} sudah tersertifikasi Halal/BPOM resmi?",
            "intent": "AI mencari data kuantitatif harga dan nomor sertifikasi resmi."
        },
        {
            "id": "q_local_store",
            "type": "Pencarian Lokal & Titik Beli (NAP)",
            "prompt": f"Di mana lokasi toko atau tempat memesan {b_name} terdekat di wilayah {loc}? Apakah ada kontak WhatsApp resminya?",
            "intent": "AI memvalidasi Name, Address, Phone (NAP) dan Google Business Profile."
        },
        {
            "id": "q_problem_solve",
            "type": "Solusi Kebutuhan / Pain Point",
            "prompt": f"Saya mencari {cat} yang aman untuk lambung, organik, dan diproses langsung oleh petani lokal. Adakah rekomendasi?",
            "intent": "AI mencocokkan format FAQ dan proposisi nilai BLUF terhadap masalah pengguna."
        }
    ]


# ==============================================================================
# 2. FITUR A: BRAND MENTION DETECTOR (STRICT MATCHING & ALIAS SUPPORT)
# ==============================================================================

# Kata leksikal untuk sentimen evaluasi produk AI
POSITIVE_LEXICON = {
    "terbaik", "rekomendasi", "direkomendasikan", "unggulan", "berkualitas",
    "kualitas tinggi", "istimewa", "sangat bagus", "populer", "favorit",
    "autentik", "organik", "terpercaya", "bersertifikat", "halal", "resmi",
    "juara", "sepadan", "puas", "aromatik", "spesial", "specialty",
    "enak", "nyaman", "keunggulan", "akurat", "lengkap", "murah berkualitas",
    "recommended", "best", "top", "excellent", "authentic", "premium"
}

NEGATIVE_LEXICON = {
    "kelemahan", "kekurangan", "mahal", "keluhan", "tidak jelas",
    "belum terdaftar", "belum bersertifikat", "belum terverifikasi",
    "sulit ditemukan", "lambat", "kualitas rendah", "kurang memuaskan",
    "risiko", "palsu", "kendala", "kecewa", "inferior", "buruk",
    "not recommended", "expensive", "poor", "unverified", "drawback"
}


def detect_brand_mentions_strict(
    ai_response_text: str,
    brand_name: str,
    aliases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Memindai teks respons AI secara ketat (Strict Matching) berbasis RegEx word boundary (\\b)
    untuk mencegah false positive (misal: kata 'Kopi' tidak akan keliru mencocokkan 'Kopiah').
    
    Mendukung:
    - Nama merek utama + daftar variasi/alias (domain website, akronim, tanpa spasi).
    - Status deteksi (True/False).
    - Istilah spesifik yang cocok (matched terms).
    - Jumlah total sebutan (match count).
    - Posisi relatif kemunculan merek dalam teks:
      * Paragraf Awal <= 25% (Chunk terdepan)
      * Bagian Tengah <= 75% (Penyebutan konteks)
      * Catatan Kaki > 75% (Alternatif / catatan bawah)
    - Analisis sentimen leksikal (Positif 🟢, Netral 🟡, Negatif 🔴).
    """
    if not ai_response_text or not ai_response_text.strip():
        return {
            "detected": False,
            "mentioned": False,
            "is_mentioned": False,
            "status_badge": "🔴 Not Mentioned",
            "badge_color": "#EF4444",
            "matched_terms": [],
            "matched_term": "-",
            "match_count": 0,
            "position": "Tidak Ditemukan",
            "position_badge": "⚪ Tidak Ditemukan",
            "relative_position": 0.0,
            "sentiment_label": "Netral ⚪",
            "sentiment_color": "#94A3B8",
            "sentiment_score": 0.0,
            "sentiment_keywords": [],
            "snippets": []
        }

    # 1. Bangun daftar seluruh istilah target (nama merek utama + seluruh alias)
    targets = []
    clean_b = brand_name.strip()
    if clean_b:
        targets.append(clean_b)

    if aliases:
        for a in aliases:
            clean_a = a.strip()
            if clean_a and clean_a not in targets:
                targets.append(clean_a)

    # Urutkan berdasarkan panjang teks secara menurun agar frasa majemuk dicocokkan lebih dulu
    targets = sorted([t for t in targets if len(t) >= 2], key=len, reverse=True)

    text_len = len(ai_response_text)
    matched_spans = []
    matched_terms_found = []
    snippets = []

    # 2. Strict RegEx matching dengan word boundary \b
    for term in targets:
        # Gunakan pattern r'\b' + re.escape(term) + r'\b' dengan re.IGNORECASE
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        for m in pattern.finditer(ai_response_text):
            start, end = m.span()

            # Cegah penghitungan ganda jika rentang karakter ini sudah dicocokkan oleh frasa yang lebih panjang
            is_overlap = any(s <= start and end <= e for (s, e, _) in matched_spans)
            if not is_overlap:
                matched_spans.append((start, end, term))
                matched_terms_found.append(term)

                # Ambil potongan cuplikan kalimat konteks (sekitar 60 karakter sebelum & sesudah)
                snip_start = max(0, start - 60)
                snip_end = min(text_len, end + 60)
                snippet = ai_response_text[snip_start:snip_end].replace("\n", " ").strip()
                snippets.append(f"...{snippet}...")

    # Urutkan berdasarkan posisi kemunculan pertama
    matched_spans.sort(key=lambda x: x[0])
    match_count = len(matched_spans)
    detected = match_count > 0

    # 3. Kalkulasi Posisi Relatif Kemunculan Merek
    # Aturan: Paragraf Awal <=25%, Bagian Tengah <=75%, Catatan Kaki >75%
    if detected:
        first_match_char = matched_spans[0][0]
        relative_pos = first_match_char / max(text_len, 1)

        if relative_pos <= 0.25:
            position_label = "Paragraf Awal"
            position_badge = "🟢 Paragraf Awal (<=25%)"
        elif relative_pos <= 0.75:
            position_label = "Bagian Tengah"
            position_badge = "🔵 Bagian Tengah (<=75%)"
        else:
            position_label = "Catatan Kaki"
            position_badge = "🟡 Catatan Kaki (>75%)"
    else:
        relative_pos = 0.0
        position_label = "Tidak Ditemukan"
        position_badge = "⚪ Tidak Ditemukan"

    # 4. Analisis Sentimen Leksikal
    sentiment_score = 0.0
    sentiment_keywords = []

    if detected:
        context_corpus = ""
        for span in matched_spans:
            s_idx = max(0, span[0] - 120)
            e_idx = min(text_len, span[1] + 120)
            context_corpus += " " + ai_response_text[s_idx:e_idx].lower()

        pos_hits = [pw for pw in POSITIVE_LEXICON if re.search(rf"\b{re.escape(pw)}\b", context_corpus)]
        neg_hits = [nw for nw in NEGATIVE_LEXICON if re.search(rf"\b{re.escape(nw)}\b", context_corpus)]

        sentiment_score = len(pos_hits) * 1.0 - len(neg_hits) * 1.5
        sentiment_keywords = list(set(pos_hits + neg_hits))

        if sentiment_score >= 1.0:
            sentiment_label = "Positif 🟢"
            sentiment_color = "#10B981"
        elif sentiment_score <= -1.0:
            sentiment_label = "Negatif 🔴"
            sentiment_color = "#EF4444"
        else:
            sentiment_label = "Netral 🟡"
            sentiment_color = "#F59E0B"
    else:
        sentiment_label = "Netral ⚪"
        sentiment_color = "#94A3B8"

    unique_matched_terms = list(dict.fromkeys(matched_terms_found))

    return {
        "detected": detected,
        "mentioned": detected,
        "is_mentioned": detected,
        "status_badge": "🟢 Mentioned" if detected else "🔴 Not Mentioned",
        "badge_color": "#10B981" if detected else "#EF4444",
        "matched_terms": unique_matched_terms,
        "matched_term": unique_matched_terms[0] if unique_matched_terms else "-",
        "match_count": match_count,
        "position": position_label,
        "position_badge": position_badge,
        "relative_position": round(relative_pos, 3),
        "sentiment_label": sentiment_label,
        "sentiment_color": sentiment_color,
        "sentiment_score": round(sentiment_score, 1),
        "sentiment_keywords": sentiment_keywords,
        "snippets": snippets[:4]
    }


def detect_brand_mentions(
    ai_response_text: str,
    brand_name: str,
    product_name: str = "",
    aliases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Wrapper fungsi deteksi merek dengan kompatibilitas penuh.
    Secara internal memanfaatkan detect_brand_mentions_strict.
    """
    combined_aliases = list(aliases or [])
    if product_name and product_name.strip() and product_name.strip() != brand_name.strip():
        combined_aliases.append(product_name.strip())

    return detect_brand_mentions_strict(ai_response_text, brand_name, combined_aliases)


# ==============================================================================
# 2B. LOGIKA 5-TIME SAMPLING & KALKULASI SKOR PROBABILITAS
# ==============================================================================

def run_5x_sampling_audit(
    query_prompt: str,
    brand_name: str,
    aliases: Optional[List[str]],
    sample_responses: List[str]
) -> Dict[str, Any]:
    """
    Menjalankan pengujian 5 kali sampling independen untuk kueri yang sama.
    
    Formulasi Skor Probabilitas:
      Skor Probabilitas Sitasi (%) = (Jumlah Run Merek Ditemukan / 5) * 100%
      
    Kategori Konsistensi Visibilitas:
      - 80% – 100%: 🟢 AI-Ready (Sangat Konsisten)
      - 40% – 60%:  🟡 Variable Visibility (Cukup Siap)
      - 0% – 20%:   🔴 Invisible to AI (Belum Siap)
    """
    if not sample_responses:
        sample_responses = [""] * 5

    # Pastikan tepat 5 sampel
    if len(sample_responses) < 5:
        sample_responses = list(sample_responses) + [""] * (5 - len(sample_responses))
    sample_responses = sample_responses[:5]

    run_records = []
    found_count = 0

    for idx, resp_text in enumerate(sample_responses, start=1):
        det_res = detect_brand_mentions_strict(resp_text, brand_name, aliases)
        is_detected = det_res["detected"]
        if is_detected:
            found_count += 1

        run_records.append({
            "run_index": idx,
            "run_label": f"Sampling #{idx}",
            "detected": is_detected,
            "status_icon": "✅ Ditemukan" if is_detected else "❌ Tidak Ditemukan",
            "matched_term": det_res["matched_term"],
            "matched_terms": det_res["matched_terms"],
            "match_count": det_res["match_count"],
            "position": det_res["position"],
            "position_badge": det_res["position_badge"],
            "snippet": det_res["snippets"][0] if det_res["snippets"] else "(Merek tidak disebut dalam run ini)",
            "sentiment_label": det_res["sentiment_label"],
            "full_response": resp_text
        })

    prob_score = round((found_count / 5.0) * 100.0, 1)

    # Kategori Konsistensi Visibilitas
    if prob_score >= 80.0:
        tier_badge = "🟢 AI-Ready (Sangat Konsisten)"
        tier_color = "#10B981"
        tier_desc = (
            "Luar biasa! Merek muncul secara stabil di hampir setiap generasi jawaban AI (80% - 100%). "
            "Fondasi GEO Anda sangat kuat dan dipercaya oleh algoritma RAG."
        )
    elif prob_score >= 40.0:
        tier_badge = "🟡 Variable Visibility (Cukup Siap)"
        tier_color = "#F59E0B"
        tier_desc = (
            "Merek kadang muncul dan kadang diabaikan oleh mesin AI (40% - 60%). "
            "Dibutuhkan optimasi pada paragraf pembuka (BLUF) dan Schema JSON-LD untuk menstabilkan pemanggilan."
        )
    else:
        tier_badge = "🔴 Invisible to AI (Belum Siap)"
        tier_color = "#EF4444"
        tier_desc = (
            "Peringatan: Merek tidak pernah atau sangat jarang disebut oleh AI (0% - 20%). "
            "Sistem pencarian generatif lebih memprioritaskan kompetitor karena minimnya data terstruktur."
        )

    # Siapkan data ringkasan untuk st.dataframe
    dataframe_rows = []
    for r in run_records:
        dataframe_rows.append({
            "Sampling Run": r["run_label"],
            "Status Deteksi": r["status_icon"],
            "Istilah Cocok": r["matched_term"],
            "Jumlah Sebutan": f"{r['match_count']}x" if r["detected"] else "0x",
            "Posisi Teks": r["position"],
            "Potongan Snippet Jawaban": r["snippet"]
        })

    return {
        "query_prompt": query_prompt,
        "brand_name": brand_name,
        "aliases": aliases or [],
        "found_count": found_count,
        "runs_found": found_count,
        "total_runs": 5,
        "probability_score": prob_score,
        "consistency_badge": tier_badge,
        "tier_label": tier_badge,
        "consistency_color": tier_color,
        "consistency_description": tier_desc,
        "run_records": run_records,
        "dataframe_rows": dataframe_rows
    }


def generate_5x_simulated_rag_responses(
    query_prompt: str,
    brand_name: str,
    product_name: str = "",
    category: str = "",
    location: str = "",
    website_url: str = "",
    aliases: Optional[List[str]] = None,
    scenario: str = "ai_ready"  # "ai_ready" (4-5 hits), "variable" (3 hits), "invisible" (1 hit)
) -> List[str]:
    """
    Menghasilkan 5 variasi teks respons simulasi RAG untuk kueri yang sama
    yang merefleksikan variasi probabilistik generasi model bahasa alami.
    """
    b_name = brand_name.strip() or "Kopi Arabika Toraja Baji"
    p_name = product_name.strip() or "Kopi Toraja Single Origin Specialty Grade 250g"
    cat = category.strip() or "Kuliner & Minuman"
    loc = location.split(",")[0].strip() if "," in location else (location.strip() or "Makale, Toraja")
    url = website_url.strip() or "https://kopitorajabaji.id"
    alias_term = aliases[0].strip() if aliases and aliases[0].strip() else b_name

    responses = []

    # Run 1: Sebutan di awal paragraf dengan detail produk & sitasi resmi
    if scenario == "invisible":
        r1 = (
            f"Berdasarkan tinjauan kurasi kuliner {loc}, rekomendasi utama untuk {cat} saat ini didominasi oleh "
            f"**Otten Coffee** dan **Excelso**. Kedua produsen memiliki jaringan gerai retail nasional dan ulasan ribuan konsumen."
        )
    else:
        r1 = (
            f"Salah satu rekomendasi {cat} terbaik dari {loc} adalah **{b_name}** ({p_name}). "
            f"Biji kopi dipetik merah dari petani dataran tinggi dengan cupping score 84+ dan telah memiliki sertifikasi Halal resmi. "
            f"Karakter aromanya kaya akan rempah dan dark chocolate yang elegan.\n\n"
            f"Referensi Sumber:\n"
            f"• Website Resmi: [{b_name}]({url}/produk)\n"
            f"• Liputan Media: [Kompas Travel](https://travel.kompas.com/read/kopi-toraja-unggulan)\n\n"
            f"Pilihan kompetitor lain di kelas ini meliputi Otten Coffee Toraja Sapan dan Anomali Coffee."
        )
    responses.append(r1)

    # Run 2: Sebutan di bagian tengah paragraf dalam daftar komparasi
    if scenario == "invisible":
        r2 = (
            f"Untuk oleh-oleh khas {loc}, wisatawan umumnya memilih produk berperingkat tinggi di platform e-commerce:\n\n"
            f"1. **Otten Coffee Specialty** - Varian single origin dengan roasting terstandar.\n"
            f"2. **Anomali Coffee** - Brand kurasi lokal dengan kemasan premium.\n"
            f"3. **Kopi Kenangan Nusantara** - Pilihan praktis yang banyak tersedia di bandara dan stasiun."
        )
    else:
        r2 = (
            f"Berdasarkan preferensi konsumen dan tren ulasan kuliner di {loc}, berikut 3 pilihan utama:\n\n"
            f"1. **Otten Coffee Toraja** - Sangat populer dengan fasilitas roasting modern dan kemasan one-way valve.\n"
            f"2. **{b_name}** - Unggul dalam keaslian single origin langsung dari kelompok tani binaan di {loc}, diproses organik dengan harga terjangkau di [{url}]({url}).\n"
            f"3. **Kapal Api Specialty** - Alternatif komersial yang mudah ditemukan di pasar swalayan."
        )
    responses.append(r2)

    # Run 3: Menggunakan variasi alias merek atau fokus FAQ harga & sertifikasi
    if scenario == "invisible":
        r3 = (
            f"Untuk kebutuhan {cat} di {loc}, pasar saat ini didominasi oleh **Otten Coffee** dan **Kopi Kenangan**. "
            f"Keduanya memiliki jaringan distribusi luas dan ulasan konsumen yang masif di Shopee dan Tokopedia."
        )
    else:
        r3 = (
            f"Mengenai kueri '{query_prompt}':\n"
            f"Produk unggulan dari **{alias_term}** dibanderol pada kisaran Rp 85.000 hingga Rp 165.000 per kemasan. "
            f"Seluruh produk telah melewati kurasi ketat dan terdaftar izin edar resmi. Rujukan lengkap dapat diakses via [{url}]({url}) "
            f"serta ulasan komunitas di [Quora Indonesia](https://id.quora.com/kopi-toraja)."
        )
    responses.append(r3)

    # Run 4: Skenario berbasis lokasi NAP atau kompetitor
    if scenario in ("variable", "invisible"):
        r4 = (
            f"Rekomendasi gerai {cat} terpopuler: **Otten Coffee Store** dan **Anomali Coffee** menyediakan fasilitas pembelian langsung. "
            f"Ulasan pengunjung dapat dilihat di [Google Maps](https://maps.google.com)."
        )
    else:
        r4 = (
            f"Untuk pembelian langsung di wilayah {loc}, gerai **{b_name}** berlokasi strategis dengan jam operasional 08.00 - 21.00. "
            f"Pemesanan online melayani pengiriman ke seluruh Nusantara melalui website [{url}]({url}) dan kontak WhatsApp bisnis terverifikasi di Google Maps."
        )
    responses.append(r4)

    # Run 5: Skenario catatan kaki / alternatif bawah
    if scenario in ("variable", "invisible"):
        if scenario == "invisible":
            r5 = (
                f"Beberapa produsen terkemuka di sektor ini mencakup Otten Coffee dan Anomali Coffee.\n\n"
                f"Catatan Alternatif: Sejumlah pembeli juga menyebutkan opsi lokal skala kecil seperti **{b_name}**, "
                f"namun ketersediaan stok produk ini di marketplace umum masih sangat terbatas."
            )
        else:
            r5 = (
                f"Pilihan produk {cat} yang paling banyak direkomendasikan adalah **Otten Coffee** dan **Kopi Kenangan** "
                f"karena kemudahan akses retail dan promosi rutin di platform digital. "
                f"Sumber: [YouTube Food Review](https://youtube.com/watch?v=kopi-review) dan [Detik Food](https://food.detik.com)."
            )
    else:
        r5 = (
            f"Beberapa produsen terkemuka di sektor ini mencakup Otten Coffee dan Anomali Coffee.\n\n"
            f"Catatan Alternatif: Bagi Anda yang mencari varian organik lokal dengan komitmen direct-trade berkelanjutan, "
            f"merek **{b_name}** merupakan opsi yang sangat layak dipertimbangkan melalui katalog [{url}]({url})."
        )
    responses.append(r5)

    return responses


def fetch_live_ai_completion_5x(
    provider: str,
    api_key: str,
    prompt: str,
    system_prompt: str = "",
    model: str = ""
) -> Dict[str, Any]:
    """
    Menjalankan 5 kali pemanggilan berurutan ke API AI (OpenAI / Perplexity)
    dengan temperature=0.7 untuk menghasilkan 5 sampel independen secara live.
    """
    sample_responses = []
    errors = []

    for run_i in range(1, 6):
        res = fetch_live_ai_completion(
            provider=provider,
            api_key=api_key,
            prompt=prompt,
            system_prompt=system_prompt,
            model=model
        )
        if res["success"]:
            sample_responses.append(res["response_text"])
        else:
            errors.append(f"Run #{run_i}: {res.get('error', 'Unknown error')}")
            # Fallback jika ada kegagalan koneksi di tengah run
            sample_responses.append("")

    return {
        "success": len([r for r in sample_responses if r]) > 0,
        "sample_responses": sample_responses,
        "errors": errors
    }


# ==============================================================================
# 3. FITUR B: CITATION LINK EXTRACTOR
# ==============================================================================

def extract_and_categorize_citations(
    ai_response_text: str,
    brand_domain: str = ""
) -> Dict[str, Any]:
    """
    Mengekstrak seluruh URL, hyperlink markdown, dan domain sumber yang
    digunakan oleh RAG AI, lalu mengelompokkannya ke dalam 5+ kategori sumber
    serta mengidentifikasi tautan aset resmi milik UMKM pengguna.
    """
    if not ai_response_text:
        return {
            "total_citations": 0,
            "citations": [],
            "brand_citations_count": 0,
            "third_party_citations_count": 0,
            "category_distribution": {},
            "has_brand_asset_citation": False
        }

    clean_domain = ""
    if brand_domain:
        parsed = urllib.parse.urlparse(brand_domain if "://" in brand_domain else f"https://{brand_domain}")
        clean_domain = parsed.netloc.lower().replace("www.", "")

    raw_citations = []
    seen_urls = set()

    # 1. Ekstraksi Markdown Hyperlinks: [Anchor Title](https://example.com/path)
    md_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", re.IGNORECASE)
    for match in md_pattern.finditer(ai_response_text):
        title = match.group(1).strip()
        url = match.group(2).strip()
        if url not in seen_urls:
            seen_urls.add(url)
            raw_citations.append({"url": url, "title": title, "source_format": "Markdown Link"})

    # 2. Ekstraksi Footnote style: [1] https://... atau [1]: https://...
    fn_pattern = re.compile(r"\[\d+\]:?\s*(https?://[^\s\)]+)", re.IGNORECASE)
    for match in fn_pattern.finditer(ai_response_text):
        url = match.group(1).strip()
        if url not in seen_urls:
            seen_urls.add(url)
            raw_citations.append({"url": url, "title": "Footnote Citation", "source_format": "Footnote URL"})

    # 3. Ekstraksi Bare URLs: https://domain.com/path
    bare_pattern = re.compile(r"(https?://[^\s\)\],\"'<>]+)", re.IGNORECASE)
    for match in bare_pattern.finditer(ai_response_text):
        url = match.group(1).strip()
        url = re.sub(r"[\.,;]$", "", url)
        if url not in seen_urls:
            seen_urls.add(url)
            raw_citations.append({"url": url, "title": "", "source_format": "Direct URL"})

    categorized_citations = []
    brand_citations_count = 0
    cat_counts = {k: 0 for k in CITATION_CATEGORIES.keys()}

    for item in raw_citations:
        url = item["url"]
        title = item["title"]
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower().replace("www.", "")

        if not title:
            path_sample = parsed.path.strip("/").replace("-", " ").replace("_", " ")
            if path_sample:
                title = f"{netloc} - {path_sample[:35].title()}"
            else:
                title = netloc

        is_brand_asset = False
        cat_key = "other"

        if clean_domain and clean_domain in netloc:
            cat_key = "brand_website"
            is_brand_asset = True
        elif any(yt in netloc for yt in ["youtube.com", "youtu.be"]):
            cat_key = "youtube_video"
        elif any(news in netloc for news in [
            "kompas.com", "detik.com", "tempo.co", "kumparan.com", "tribunnews.com",
            "idntimes.com", "bisnis.com", "liputan6.com", "jawapos.com", "republika.co.id",
            "cnnindonesia.com", "tirto.id", "antaranews.com"
        ]):
            cat_key = "news_media"
        elif any(forum in netloc for forum in [
            "reddit.com", "quora.com", "kaskus.co.id", "kompasiana.com", "medium.com",
            "threads.net", "facebook.com", "x.com", "twitter.com"
        ]):
            cat_key = "community_forum"
        elif any(loc in netloc for loc in [
            "google.com/maps", "maps.google.com", "maps.app.goo.gl", "business.google.com",
            "tripadvisor.com", "pergikuliner.com", "zomato.com"
        ]) or "maps" in parsed.path:
            cat_key = "local_business"
        elif any(mp in netloc for mp in [
            "shopee.co.id", "tokopedia.com", "lazada.co.id", "blibli.com", "tiktok.com", "bukalapak.com"
        ]):
            cat_key = "marketplace"
        else:
            cat_key = "other"

        cat_info = CITATION_CATEGORIES[cat_key]
        cat_counts[cat_key] = cat_counts.get(cat_key, 0) + 1

        if is_brand_asset:
            brand_citations_count += 1

        categorized_citations.append({
            "url": url,
            "title": title,
            "domain": netloc,
            "category_id": cat_key,
            "category_name": cat_info["name"],
            "category_icon": cat_info["icon"],
            "badge_color": cat_info["badge_color"],
            "is_brand_asset": is_brand_asset,
            "source_format": item["source_format"]
        })

    total_citations = len(categorized_citations)
    third_party_count = total_citations - brand_citations_count
    active_distribution = {k: v for k, v in cat_counts.items() if v > 0}

    return {
        "total_citations": total_citations,
        "citations": categorized_citations,
        "brand_citations_count": brand_citations_count,
        "third_party_citations_count": third_party_count,
        "category_distribution": active_distribution,
        "has_brand_asset_citation": brand_citations_count > 0
    }


# ==============================================================================
# 4. FITUR C: CITATION GAP MAP & SHARE OF VOICE
# ==============================================================================

def analyze_citation_gap_matrix(
    test_results: List[Dict[str, Any]],
    brand_name: str,
    default_competitors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Memetakan kueri di mana AI merekomendasikan produk Pesaing/Kompetitor,
    menghitung Share of Voice (Pangsa Suara), serta menghasilkan
    Auto-Actionable Insights untuk merebut posisi sitasi.
    """
    b_name = brand_name.strip() or "Merek Anda"
    competitors = default_competitors or ["Kopi Kenangan", "Otten Coffee", "Anomali Coffee", "Kapal Api Specialty"]

    matrix_rows = []
    brand_mention_total = 0
    competitor_mentions = {comp: 0 for comp in competitors}
    competitor_domains_cited = {comp: [] for comp in competitors}
    insights = []

    for item in test_results:
        query_prompt = item.get("prompt", "Kueri Tidak Diketahui")
        ai_resp = item.get("response_text", "")
        engine_name = item.get("engine_name", "AI Engine")

        # Cek sebutan merek user
        brand_check = detect_brand_mentions(ai_resp, b_name)
        brand_status = brand_check["mentioned"]
        if brand_status:
            brand_mention_total += 1

        # Cek sebutan kompetitor
        comps_present = []
        for comp in competitors:
            c_check = detect_brand_mentions(ai_resp, comp)
            if c_check["mentioned"]:
                comps_present.append(comp)
                competitor_mentions[comp] = competitor_mentions.get(comp, 0) + 1

        # Ekstrak domain sitasi
        citation_check = extract_and_categorize_citations(ai_resp)
        all_domains = list({c["domain"] for c in citation_check["citations"]})
        comp_domains = [d for d in all_domains if not (b_name.lower().replace(" ", "") in d)]

        for c_name in comps_present:
            competitor_domains_cited[c_name].extend(comp_domains)

        gap_status = "Aman (Disebut)" if brand_status else ("Celah Kritis (Pesaing Muncul)" if comps_present else "Netral (Keduanya Absen)")

        matrix_rows.append({
            "engine": engine_name,
            "query": query_prompt,
            "brand_status": brand_status,
            "brand_status_icon": "✅" if brand_status else "❌",
            "competitors_found": comps_present if comps_present else ["(Tidak ada)"],
            "competitors_text": ", ".join(comps_present) if comps_present else "-",
            "cited_domains": comp_domains[:3],
            "cited_domains_text": ", ".join(comp_domains[:3]) if comp_domains else "-",
            "gap_status": gap_status,
            "has_gap": (not brand_status and len(comps_present) > 0)
        })

    total_tests = max(len(test_results), 1)

    all_entity_mentions = brand_mention_total + sum(competitor_mentions.values())
    all_entity_mentions = max(all_entity_mentions, 1)

    brand_sov = round((brand_mention_total / all_entity_mentions) * 100, 1)
    sov_breakdown = {b_name: brand_sov}

    for comp, cnt in competitor_mentions.items():
        sov_breakdown[comp] = round((cnt / all_entity_mentions) * 100, 1)

    critical_gaps = [r for r in matrix_rows if r["has_gap"]]

    if critical_gaps:
        all_gap_domains = []
        for r in critical_gaps:
            all_gap_domains.extend(r["cited_domains"])
        all_gap_domains = list(set(all_gap_domains))

        has_yt = any("youtube" in d for d in all_gap_domains)
        has_news = any(n in d for d in all_gap_domains for n in ["kompas", "detik", "tempo", "kumparan", "idntimes"])
        has_maps = any("maps" in d or "google" in d for d in all_gap_domains)
        has_forum = any("reddit" in d or "quora" in d or "kaskus" in d for d in all_gap_domains)

        top_comp = max(competitor_mentions.items(), key=lambda x: x[1])[0]

        if has_yt:
            insights.append({
                "title": f"Perebutan Sitasi YouTube ({top_comp})",
                "badge": "Prioritas Video",
                "color": "#DC2626",
                "icon": "📹",
                "recommendation": (
                    f"Pesaing utama **{top_comp}** disitasi AI melalui video YouTube. "
                    f"Segera buat video ulasan/demonstrasi produk **{b_name}** di YouTube dengan transkrip subtitle lengkap "
                    f"dan kata kunci spesifik agar AI Overviews & Gemini mengindeks entitas Anda."
                )
            })

        if has_news:
            insights.append({
                "title": f"Kurasi Media & Listicles Pihak Ketiga",
                "badge": "Otoritas Media",
                "color": "#2563EB",
                "icon": "📰",
                "recommendation": (
                    f"Pesaing sering muncul dari artikel listicle portal berita ('10 Rekomendasi Terbaik'). "
                    f"Jalin kerja sama publikasi konten/press release dengan blog kuliner/lifestyle daerah untuk "
                    f"mencantumkan **{b_name}** ke dalam daftar kurasi eksternal."
                )
            })

        if has_maps:
            insights.append({
                "title": "Grounding Lokal & Google Business Profile",
                "badge": "Lokal NAP",
                "color": "#D97706",
                "icon": "📍",
                "recommendation": (
                    f"AI RAG memeriksa verifikasi Google Maps saat menjawab pertanyaan kueri lokal. "
                    f"Pastikan Google Business Profile **{b_name}** telah mengumpulkan 15+ ulasan autentik, "
                    f"jam operasional akurat, dan tautan ke website resmi."
                )
            })

        if has_forum:
            insights.append({
                "title": "Konsensus Komunitas (Quora & Forum)",
                "badge": "Social Proof",
                "color": "#7C3AED",
                "icon": "💬",
                "recommendation": (
                    f"Mesin AI seperti Perplexity memprioritaskan rekomendasi dari thread Quora/Reddit. "
                    f"Aktiflah berpartisipasi dalam diskusi seputar kopi/produk lokal dengan membagikan edukasi objektif tentang **{b_name}**."
                )
            })

        insights.append({
            "title": f"Terapkan BLUF & Schema Product di Halaman Utama",
            "badge": "On-Page GEO",
            "color": "#059669",
            "icon": "🏷️",
            "recommendation": (
                f"Kesenjangan kutipan pada kueri '{critical_gaps[0]['query'][:40]}...' dapat dipulihkan secara instan "
                f"dengan menempatkan ringkasan harga dan keunggulan di 50 kata pertama serta memasang Schema JSON-LD Product."
            )
        })
    else:
        insights.append({
            "title": "Dominasi Posisi Sitasi Terjaga",
            "badge": "GEO Champion",
            "color": "#10B981",
            "icon": "🏆",
            "recommendation": (
                f"Hebat! **{b_name}** berhasil disebut dan disitasi dengan baik di seluruh pengujian. "
                f"Pertahankan konsistensi pembaruan konten dan pantau perubahan algoritma RAG secara berkala."
            )
        })

    return {
        "matrix_rows": matrix_rows,
        "total_tests": total_tests,
        "brand_mention_total": brand_mention_total,
        "brand_mention_rate": round((brand_mention_total / total_tests) * 100, 1),
        "brand_share_of_voice": brand_sov,
        "sov_breakdown": sov_breakdown,
        "competitor_mentions": competitor_mentions,
        "critical_gaps_count": len(critical_gaps),
        "insights": insights
    }


# ==============================================================================
# 5. SIMULASI RAG MULTI-MESIN REALISTIS (OFFLINE / DEFAULT MODE)
# ==============================================================================

def generate_simulated_ai_response(
    engine_id: str,
    query_item: Dict[str, str],
    brand_name: str,
    product_name: str,
    category: str,
    location: str,
    website_url: str
) -> Dict[str, Any]:
    """
    Menghasilkan respons simulasi RAG AI multi-mesin yang realistis
    lengkap dengan sitasi URL, perbandingan kompetitor, dan variasi sentimen.
    """
    b_name = brand_name.strip() or "Kopi Arabika Toraja Baji"
    p_name = product_name.strip() or "Kopi Toraja Single Origin Specialty 250g"
    cat = category.strip() or "Kuliner & Minuman"
    loc = location.strip() or "Makale, Tana Toraja"
    url = website_url.strip() or "https://kopitorajabaji.id"

    qid = query_item.get("id", "q_trans")
    prompt = query_item.get("prompt", "")

    if qid == "q_trans":
        if engine_id in ("chatgpt", "perplexity"):
            response_text = (
                f"Berdasarkan kurasi data ulasan dan ulasan konsumen terpercaya, berikut adalah rekomendasi {cat} unggulan dari {loc}:\n\n"
                f"1. **{b_name}** - Salah satu pilihan specialty grade terbaik yang bersumber langsung dari petani lokal Makale. "
                f"Memiliki profil rasa aromatik dengan cupping score 84+, serta telah tersertifikasi Halal. Sangat direkomendasikan untuk oleh-oleh premium.\n"
                f"   - Sumber: [{b_name} Official]({url}/produk) dan ulasan [Kompas Travel](https://travel.kompas.com/read/rekomendasi-kopi-toraja-terbaik)\n\n"
                f"2. **Otten Coffee Toraja Sapan** - Varietas kopi populer dengan tingkat keasaman seimbang dan kemasan modern.\n"
                f"   - Sumber: [Otten Coffee Store](https://ottencoffee.co.id/toraja) | [Review YouTube Kopi Mania](https://youtube.com/watch?v=kopi-toraja-review)\n\n"
                f"3. **Anomali Coffee Toraja** - Kopi sangrai dengan karakter herbal dan dark chocolate pekat.\n"
                f"   - Sumber: [Detik Food](https://food.detik.com/read/rekomendasi-kopi-nusantara)"
            )
        elif engine_id == "google_aio":
            response_text = (
                f"**Ringkasan AI Overviews:** Untuk {cat} terbaik di wilayah {loc}, pertimbangkan:\n"
                f"• **{b_name}**: Produk {p_name} diproses secara organik dengan sertifikat resmi dan harga transparan.\n"
                f"• **Otten Coffee**: Memiliki pilihan roasting light hingga medium.\n"
                f"• **Kopi Kenangan**: Opsi praktis siap minum.\n\n"
                f"Tautan Terkait: [{url}]({url}) | [Google Maps Profile](https://maps.google.com/?cid=12345678) | [YouTube Unboxing](https://youtube.com/watch?v=review-toraja-baji)"
            )
        else:
            response_text = (
                f"Dalam mencari {cat} berkualitas dari daerah {loc}, terdapat beberapa produsen terkemuka:\n\n"
                f"Sebagai rekomendasi utama, **{b_name}** ({p_name}) menawarkan keaslian cita rasa single origin "
                f"dengan proses ramah lingkungan. Dikutip dari [{b_name} Web]({url}), produk ini menggunakan biji pilihan petani binaan.\n\n"
                f"Sebagai alternatif komparasi, Anda juga dapat mempertimbangkan **Anomali Coffee** dan **Otten Coffee** yang dapat dibeli melalui [Shopee Official](https://shopee.co.id/kopi-toraja)."
            )

    elif qid == "q_brand_compare":
        response_text = (
            f"**Perbandingan Keunggulan {b_name} vs Kompetitor:**\n\n"
            f"**{b_name}** memiliki keunggulan utama pada keaslian *single origin* langsung dari dataran tinggi {loc}, "
            f"di mana biji kopi dipetik merah (full wash) dan memiliki sertifikasi Halal serta skor uji rasa di atas 84 poin. "
            f"Jika dibandingkan dengan merek seperti **Otten Coffee** atau **Kapal Api Specialty**, {b_name} lebih fokus pada "
            f"pemberdayaan petani lokal dan transparansi rantai pasok (direct trade).\n\n"
            f"Menurut diskusi komunitas di [Quora Indonesia](https://id.quora.com/kopi-toraja-terbaik), harganya tergolong sangat sepadan "
            f"dengan kualitas specialty yang disajikan.\n\n"
            f"Kutipan Sumber:\n"
            f"[1] Profil Resmi: [{url}]({url})\n"
            f"[2] Liputan Daerah: [Tribun Timur Makassar](https://makassar.tribunnews.com/kuliner-toraja)\n"
            f"[3] Thread Forum: [Kaskus Lounge Kopi Nusantara](https://kaskus.co.id/thread/kopi-toraja)"
        )

    elif qid == "q_trust_cert":
        response_text = (
            f"Informasi harga dan legalitas produk **{b_name}**:\n\n"
            f"1. **Kisaran Harga**: Produk {p_name} dibanderol pada rentang Rp 85.000 hingga Rp 165.000 per kemasan 250 gram, tergantung varian proses (Wash / Natural / Honey).\n"
            f"2. **Legalitas & Sertifikasi**: Produk ini telah memiliki sertifikat Halal resmi dari BPJPH Kemenag serta nomor izin edar P-IRT Dinas Kesehatan yang sah.\n\n"
            f"Data ini diverifikasi melalui landing page resmi [{b_name}]({url}) dan pangkalan data sertifikasi UMKM lokal."
        )

    elif qid == "q_local_store":
        response_text = (
            f"Untuk membeli produk **{b_name}** secara langsung di daerah {loc}:\n\n"
            f"📍 **Alamat Gerai**: {loc}, Sulawesi Selatan.\n"
            f"📞 **Kontak Pemesanan / WhatsApp**: Layanan pelanggan dapat dihubungi melalui nomor WhatsApp bisnis resmi yang tertera di website.\n"
            f"🌐 **Pemesanan Online**: Tersedia di [{url}]({url}) dan pengiriman ke seluruh Indonesia.\n\n"
            f"Lokasi dapat ditelusuri di [Google Maps - {b_name}](https://maps.google.com/?q={urllib.parse.quote(b_name)}) dan ulasan pengunjung di [TripAdvisor](https://tripadvisor.com/toraja-coffee)."
        )

    else:
        if engine_id in ("perplexity", "claude"):
            response_text = (
                f"Untuk kebutuhan {cat} yang ramah lambung (low acidity) dan organik, beberapa pilihan yang banyak direkomendasikan adalah:\n\n"
                f"1. **Otten Coffee Specialty Cold Brew** - Sangat terkenal di kalangan penikmat kopi yang sensitif lambung karena proses ekstraksi dingin.\n"
                f"   - Referensi: [Review Video YouTube Foodie](https://youtube.com/watch?v=kopi-aman-lambung) | [Tempo Media](https://tempo.co/read/kopi-organik)\n\n"
                f"2. **Kopi Kenangan Organik Blend** - Menggunakan biji arabika pilihan dengan *roasting* khusus.\n\n"
                f"Catatan: Merek lokal seperti **{b_name}** juga menyediakan varian Arabika Toraja yang diproses secara alami dan minim residu kimia, namun informasi spesifik mengenai uji tingkat keasaman perlu dicek lebih lanjut di katalog resmi mereka [{url}]({url})."
            )
        else:
            response_text = (
                f"Berdasarkan preferensi kopi ramah lambung dan organik, **{b_name}** adalah salah satu kandidat unggul karena 100% menggunakan biji Arabika Toraja Specialty "
                f"yang dipetik dari perkebunan dataran tinggi 1.400 mdpl. Arabika memiliki kandungan kafein alami yang lebih rendah dibanding Robusta sehingga lebih bersahabat untuk pencernaan.\n\n"
                f"Rujukan:\n"
                f"• [{b_name} Detail Kopi]({url}/faq)\n"
                f"• [Panduan Kopi Sehat di Detik Health](https://health.detik.com/kopi-aman-lambung)"
            )

    return {
        "engine_id": engine_id,
        "engine_name": AI_ENGINES.get(engine_id, {}).get("name", engine_id.title()),
        "engine_icon": AI_ENGINES.get(engine_id, {}).get("icon", "🤖"),
        "query_id": qid,
        "prompt": prompt,
        "response_text": response_text
    }


def run_full_simulation_benchmark(
    brand_name: str,
    product_name: str,
    category: str,
    location: str,
    website_url: str,
    selected_engines: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Menjalankan simulasi pengujian otomatis benchmark multi-mesin
    (5 kueri percakapan x seluruh mesin AI terpilih).
    """
    engines_to_run = selected_engines or list(AI_ENGINES.keys())
    benchmark_queries = build_benchmark_queries(brand_name, product_name, category, location)

    results = []
    for eng_id in engines_to_run:
        for q in benchmark_queries:
            resp_data = generate_simulated_ai_response(
                engine_id=eng_id,
                query_item=q,
                brand_name=brand_name,
                product_name=product_name,
                category=category,
                location=location,
                website_url=website_url
            )
            results.append(resp_data)

    return results


# ==============================================================================
# 6. LIVE API CONNECTOR (REAL-TIME API MODE)
# ==============================================================================

def fetch_live_ai_completion(
    provider: str,
    api_key: str,
    prompt: str,
    system_prompt: str = "",
    model: str = ""
) -> Dict[str, Any]:
    """
    Memanggil API LLM / Search RAG resmi secara real-time via urllib standar.
    Mendukung OpenAI (ChatGPT) dan Perplexity AI.
    """
    api_key = api_key.strip()
    if not api_key:
        return {"success": False, "error": "API Key belum diisi."}

    if not system_prompt:
        system_prompt = (
            "You are an AI Search and Information Retrieval Engine. "
            "Answer the user query accurately in Indonesian with specific brand mentions, facts, "
            "and cite realistic web sources, URLs, or markdown hyperlinks where appropriate."
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if provider.lower() == "perplexity":
        endpoint = "https://api.perplexity.ai/chat/completions"
        target_model = model or "sonar"
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
    else:
        endpoint = "https://api.openai.com/v1/chat/completions"
        target_model = model or "gpt-4o-mini"
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            answer_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "success": True,
                "provider": provider,
                "model": target_model,
                "response_text": answer_text,
                "raw_data": data
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        return {"success": False, "error": f"HTTP Error {e.code}: {err_msg}"}
    except Exception as ex:
        return {"success": False, "error": f"Koneksi Gagal: {str(ex)}"}


# ==============================================================================
# 7. FITUR EKSPOR (CSV, JSON, MARKDOWN)
# ==============================================================================

def export_audit_to_json(
    brand_name: str,
    website_url: str,
    matrix_data: Dict[str, Any],
    citations_data: Dict[str, Any],
    test_results: List[Dict[str, Any]]
) -> str:
    """Menghasilkan struktur JSON lengkap laporan audit AI testing."""
    payload = {
        "metadata": {
            "application": "GEO Audit App Nusantara",
            "module": "Automated AI Testing & Audit",
            "brand_name": brand_name,
            "website_url": website_url,
            "total_queries_tested": len(test_results)
        },
        "brand_mention_metrics": {
            "mention_rate_pct": matrix_data.get("brand_mention_rate", 0),
            "share_of_voice_pct": matrix_data.get("brand_share_of_voice", 0),
            "sov_breakdown": matrix_data.get("sov_breakdown", {}),
            "critical_gaps_count": matrix_data.get("critical_gaps_count", 0)
        },
        "citation_metrics": {
            "total_citations_found": citations_data.get("total_citations", 0),
            "brand_assets_cited": citations_data.get("brand_citations_count", 0),
            "third_party_cited": citations_data.get("third_party_citations_count", 0),
            "category_distribution": citations_data.get("category_distribution", {})
        },
        "citation_gap_matrix": matrix_data.get("matrix_rows", []),
        "actionable_insights": matrix_data.get("insights", []),
        "all_citations_extracted": citations_data.get("citations", [])
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def export_audit_to_csv(matrix_rows: List[Dict[str, Any]]) -> str:
    """Menghasilkan string CSV dari Matriks Kesenjangan Kutipan (Gap Table)."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Mesin AI",
        "Kueri / Prompt Pengujian",
        "Status Merek Anda",
        "Merek Pesaing yang Muncul",
        "Domain Sumber Pesaing",
        "Status Kesenjangan (Gap)"
    ])

    for row in matrix_rows:
        writer.writerow([
            row.get("engine", ""),
            row.get("query", ""),
            "Disebut (✅)" if row.get("brand_status") else "Tidak Disebut (❌)",
            row.get("competitors_text", "-"),
            row.get("cited_domains_text", "-"),
            row.get("gap_status", "")
        ])

    return output.getvalue()
