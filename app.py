"""
GEO Audit App Nusantara
Aplikasi Web Interaktif Audit Kesiapan Generative Engine Optimization (GEO) untuk UMKM Indonesia.
"""

import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import modul internal
from geo_engine import (
    GEO_PILLARS,
    calculate_geo_score,
    analyze_citation_gaps,
    get_prioritized_recommendations,
    analyze_inputs_to_indicators,
    live_crawl_website
)
from autofix_generators import (
    generate_organization_schema,
    generate_faq_schema,
    generate_product_schema,
    generate_bluf_draft,
    generate_robots_txt,
    generate_conversational_faqs
)
from ai_testing_engine import (
    AI_ENGINES,
    CITATION_CATEGORIES,
    build_benchmark_queries,
    detect_brand_mentions,
    detect_brand_mentions_strict,
    run_5x_sampling_audit,
    generate_5x_simulated_rag_responses,
    fetch_live_ai_completion_5x,
    extract_and_categorize_citations,
    analyze_citation_gap_matrix,
    generate_simulated_ai_response,
    run_full_simulation_benchmark,
    fetch_live_ai_completion,
    export_audit_to_json,
    export_audit_to_csv
)

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="GEO Audit App Nusantara | Kesiapan AI untuk UMKM",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Khusus untuk Tampilan Premium & Modern Nusantara
st.markdown("""
<style>
    /* Font & Global Styling */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header & Branding Banner */
    .hero-container {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
        color: white;
        padding: 2.2rem 2.5rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #d1fae5;
        line-height: 1.6;
        max-width: 900px;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }

    /* Kartu Metrik & Pilar */
    .pilar-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .pilar-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }
    .pilar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    .pilar-badge-weight {
        background: #f1f5f9;
        color: #0f172a;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }

    /* Score Box Highlight */
    .score-card {
        text-align: center;
        padding: 2rem 1.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .score-number {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        margin: 0.5rem 0;
    }
    .score-label {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
    }

    /* Citation Gap Box */
    .gap-card {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 1rem;
    }
    .gap-card-critical {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem 1.2rem;
        border-radius: 0 10px 10px 0;
        margin-bottom: 1rem;
    }

    /* Recommendation Pill */
    .recom-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.8rem;
    }
    .recom-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 0.5rem;
    }
    .pill-quick {
        background: #dcfce7;
        color: #15803d;
    }
    .pill-strat {
        background: #e0f2fe;
        color: #0369a1;
    }

    /* Code Container */
    .code-box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #1e293b;
        color: #f8fafc;
        padding: 0.6rem 1rem;
        border-radius: 8px 8px 0 0;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* AI Testing & Audit Component Styles */
    .ai-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #065f46 100%);
        color: white;
        padding: 1.5rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    .mention-badge-card {
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .snippet-box {
        background: #f8fafc;
        border-left: 4px solid #0d9488;
        padding: 0.85rem 1.1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.6rem;
        font-size: 0.88rem;
        color: #1e293b;
        font-style: italic;
    }
    .citation-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .insight-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# INISIALISASI SESSION STATE
# ==============================================================================
if "brand_name" not in st.session_state:
    st.session_state["brand_name"] = "Kopi Arabika Toraja Baji"
if "website_url" not in st.session_state:
    st.session_state["website_url"] = "https://kopitorajabaji.id"
if "business_category" not in st.session_state:
    st.session_state["business_category"] = "Kuliner & Minuman"
if "phone_number" not in st.session_state:
    st.session_state["phone_number"] = "+62 812-9876-5432"
if "location_info" not in st.session_state:
    st.session_state["location_info"] = "Makale, Tana Toraja, Sulawesi Selatan"
if "product_name" not in st.session_state:
    st.session_state["product_name"] = "Kopi Toraja Single Origin Specialty Grade 250g"
if "price_range" not in st.session_state:
    st.session_state["price_range"] = "Rp 85.000 - Rp 165.000"
if "key_advantages" not in st.session_state:
    st.session_state["key_advantages"] = "100% Organik dari Petani Lokal, Sertifikat Halal & Cupping Score 84+"

# State untuk 10 Indikator Checklist
DEFAULT_CHECKS = {
    "tech_robots": False,
    "tech_https_speed": True,
    "content_bluf": False,
    "content_headings": True,
    "content_faq": False,
    "content_data": False,
    "schema_org": False,
    "schema_product_faq": False,
    "offpage_youtube": False,
    "offpage_mentions": True
}

for k, v in DEFAULT_CHECKS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# State untuk Modul AI Testing & Audit
if "brand_aliases" not in st.session_state:
    st.session_state["brand_aliases"] = "kopitorajabaji.id, Kopi Toraja Baji, Toraja Baji"
if "ai_test_mode" not in st.session_state:
    st.session_state["ai_test_mode"] = "Mode Simulasi (Demo)"
if "ai_test_selected_engine" not in st.session_state:
    st.session_state["ai_test_selected_engine"] = "chatgpt"
if "ai_test_api_key" not in st.session_state:
    st.session_state["ai_test_api_key"] = ""
if "ai_test_api_provider" not in st.session_state:
    st.session_state["ai_test_api_provider"] = "OpenAI (ChatGPT)"
if "ai_test_manual_text" not in st.session_state:
    st.session_state["ai_test_manual_text"] = ""
if "ai_test_benchmark_results" not in st.session_state:
    st.session_state["ai_test_benchmark_results"] = None
if "ai_test_competitors" not in st.session_state:
    st.session_state["ai_test_competitors"] = "Kopi Kenangan, Otten Coffee, Anomali Coffee, Kapal Api Specialty"
if "ai_test_5x_prompt" not in st.session_state:
    st.session_state["ai_test_5x_prompt"] = ""
if "ai_test_5x_responses" not in st.session_state:
    st.session_state["ai_test_5x_responses"] = None
if "ai_test_5x_scenario" not in st.session_state:
    st.session_state["ai_test_5x_scenario"] = "🟢 AI-Ready (4-5 dari 5 Run Ditemukan)"


def set_demo_data():
    """Mengisi data contoh UMKM kopi nusantara yang realistis."""
    st.session_state["brand_name"] = "Kopi Arabika Toraja Baji"
    st.session_state["website_url"] = "https://kopitorajabaji.id"
    st.session_state["business_category"] = "Kuliner & Minuman"
    st.session_state["phone_number"] = "+62 812-9876-5432"
    st.session_state["location_info"] = "Makale, Tana Toraja, Sulawesi Selatan"
    st.session_state["product_name"] = "Kopi Toraja Single Origin Specialty Grade 250g"
    st.session_state["price_range"] = "Rp 85.000 - Rp 165.000"
    st.session_state["key_advantages"] = "100% Organik dari Petani Lokal, Sertifikat Halal & Cupping Score 84+"
    st.session_state["tech_robots"] = False
    st.session_state["tech_https_speed"] = True
    st.session_state["content_bluf"] = False
    st.session_state["content_headings"] = True
    st.session_state["content_faq"] = False
    st.session_state["content_data"] = False
    st.session_state["schema_org"] = False
    st.session_state["schema_product_faq"] = False
    st.session_state["offpage_youtube"] = False
    st.session_state["offpage_mentions"] = True


def reset_all_checks():
    """Mengosongkan semua indikator ke False."""
    for k in DEFAULT_CHECKS.keys():
        st.session_state[k] = False


# ==============================================================================
# SIDEBAR: PROFIL DATA UMKM
# ==============================================================================
with st.sidebar:
    st.markdown("### 🧭 Profil Data UMKM")
    st.caption("Data ini digunakan untuk menghitung konteks audit dan memproduksi kode Auto-Fix.")

    if st.button("🌐 Jalankan Live Audit Web", type="primary", use_container_width=True, help="Fetch langsung URL website, cek robots.txt AI, ukur TTFB server, dan analisis seluruh kesiapan GEO secara real-time"):
        inputs_data = {
            "brand_name": st.session_state["brand_name"],
            "website_url": st.session_state["website_url"],
            "business_category": st.session_state["business_category"],
            "phone_number": st.session_state["phone_number"],
            "location_info": st.session_state["location_info"],
            "product_name": st.session_state["product_name"],
            "price_range": st.session_state["price_range"],
            "key_advantages": st.session_state["key_advantages"]
        }
        target_site = st.session_state["website_url"].strip()
        if not target_site:
            st.sidebar.error("Silakan masukkan URL website terlebih dahulu.")
        else:
            with st.spinner(f"🔍 Menghubungi server live {target_site} dan memindai robots.txt..."):
                # 1. Analisis Heuristik Konten, Data, dan Profil Merek
                analysis_res = analyze_inputs_to_indicators(inputs_data)
                for ind_k, ind_v in analysis_res["answers"].items():
                    st.session_state[ind_k] = ind_v
                st.session_state["last_analysis_summary"] = analysis_res["summary"]
                st.session_state["last_detected_tags"] = analysis_res["detected_data"]
                st.session_state["last_analysis_reasons"] = analysis_res["reasons"]

                # 2. Live Web Crawl (Server TTFB, HTTPS SSL, robots.txt untuk 4 AI Bots)
                crawl_res = live_crawl_website(target_site)
                if crawl_res["success"]:
                    st.session_state["tech_robots"] = crawl_res["tech_robots_passed"]
                    st.session_state["tech_https_speed"] = crawl_res["tech_https_speed_passed"]
                    if crawl_res.get("html_inspections", {}).get("has_schema_jsonld"):
                        st.session_state["schema_org"] = True
                        st.session_state["schema_product_faq"] = True
                    if crawl_res.get("html_inspections", {}).get("has_headings"):
                        st.session_state["content_headings"] = True
                    st.session_state["last_live_crawl"] = crawl_res
                    st.toast("✅ Live Audit Web Selesai! Seluruh 10 indikator GEO telah terisi otomatis.", icon="🌐")
                else:
                    st.sidebar.warning(f"⚠️ Live Crawl: {crawl_res.get('error_message')}")
                    st.toast("⚠️ Evaluasi selesai dengan data inputan lokal.", icon="⚠️")
                st.rerun()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📋 Preset Demo", use_container_width=True, help="Muat data contoh UMKM Kopi Toraja"):
            set_demo_data()
            inputs_data = {
                "brand_name": st.session_state["brand_name"],
                "website_url": st.session_state["website_url"],
                "business_category": st.session_state["business_category"],
                "phone_number": st.session_state["phone_number"],
                "location_info": st.session_state["location_info"],
                "product_name": st.session_state["product_name"],
                "price_range": st.session_state["price_range"],
                "key_advantages": st.session_state["key_advantages"]
            }
            analysis_res = analyze_inputs_to_indicators(inputs_data)
            for ind_k, ind_v in analysis_res["answers"].items():
                st.session_state[ind_k] = ind_v
            st.session_state["last_analysis_summary"] = analysis_res["summary"]
            st.session_state["last_detected_tags"] = analysis_res["detected_data"]
            st.rerun()
    with col_btn2:
        if st.button("🔄 Kosongkan Cek", use_container_width=True, help="Kosongkan semua checklist"):
            reset_all_checks()
            if "last_analysis_summary" in st.session_state:
                del st.session_state["last_analysis_summary"]
            if "last_live_crawl" in st.session_state:
                del st.session_state["last_live_crawl"]
            st.rerun()

    st.markdown("---")

    brand_input = st.text_input(
        "🏷️ Nama Merek / UMKM",
        value=st.session_state["brand_name"],
        help="Nama resmi brand yang ingin diaudit kesiapannya di AI."
    )
    st.session_state["brand_name"] = brand_input

    url_input = st.text_input(
        "🌐 URL Website / Landing Page",
        value=st.session_state["website_url"],
        help="Alamat situs web utama atau landing page produk Anda."
    )
    st.session_state["website_url"] = url_input

    categories = [
        "Kuliner & Minuman",
        "Fashion & Tekstil",
        "Kriya & Kerajinan Tangan",
        "Jasa Profesional & Konsultan",
        "Pertanian & Agribisnis",
        "Pariwisata & Perhotelan",
        "Kecantikan & Perawatan Diri",
        "Herbal & Kesehatan",
        "Teknologi & Digital",
        "Lainnya"
    ]
    cur_cat_idx = categories.index(st.session_state["business_category"]) if st.session_state["business_category"] in categories else 0
    cat_input = st.selectbox(
        "📦 Kategori Bisnis / Niche",
        categories,
        index=cur_cat_idx
    )
    st.session_state["business_category"] = cat_input

    phone_input = st.text_input(
        "💬 Kontak WhatsApp Bisnis",
        value=st.session_state["phone_number"],
        help="Nomor WhatsApp aktif untuk konversi pemesanan langsung."
    )
    st.session_state["phone_number"] = phone_input

    location_input = st.text_input(
        "📍 Lokasi (Kota / Provinsi)",
        value=st.session_state["location_info"],
        help="Basis operasional untuk penegasan Local SEO & AI Geo-Grounding."
    )
    st.session_state["location_info"] = location_input

    st.markdown("#### Detail Produk untuk Auto-Fix:")
    prod_input = st.text_input("Produk Unggulan", value=st.session_state["product_name"])
    st.session_state["product_name"] = prod_input

    price_input = st.text_input("Rentang Harga", value=st.session_state["price_range"])
    st.session_state["price_range"] = price_input

    adv_input = st.text_area("Keunggulan Kompetitif", value=st.session_state["key_advantages"], height=70)
    st.session_state["key_advantages"] = adv_input

    st.markdown("---")
    st.caption("💡 **GEO (Generative Engine Optimization)** adalah strategi optimasi website agar mudah dipahami, direkomendasikan, dan disitasi oleh AI Search seperti ChatGPT, Perplexity, Claude, dan Gemini.")


# ==============================================================================
# HEADER UTAMA
# ==============================================================================
st.markdown(f"""
<div class="hero-container">
    <span class="hero-badge">🇮🇩 Generative Engine Optimization Audit</span>
    <div class="hero-title">
        <span>🧭</span> GEO Audit App Nusantara
    </div>
    <div class="hero-subtitle">
        Alat audit mandiri untuk mengukur seberapa siap website <strong>{st.session_state['brand_name']}</strong> 
        direkomendasikan dan disitasi oleh mesin pencari AI generasi baru (ChatGPT Search, Perplexity AI, Claude, Gemini, dan Google AI Overviews).
    </div>
</div>
""", unsafe_allow_html=True)

# Tampilkan Banner Hasil Analisis Otomatis jika sudah dijalankan
if st.session_state.get("last_analysis_summary"):
    tags_html = "".join([
        f'<span style="background: white; border: 1px solid #a7f3d0; color: #065f46; font-size: 0.78rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-right: 0.3rem;">✓ {t}</span>'
        for t in st.session_state.get("last_detected_tags", [])
    ])
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border: 1.5px solid #6ee7b7; border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 1.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
            <span style="background: #059669; color: white; font-size: 0.75rem; font-weight: 800; padding: 2px 8px; border-radius: 999px;">AI SCANNER COMPLETED</span>
            <strong style="color: #065f46; font-size: 1.05rem;">Hasil Pemindaian Otomatis: {st.session_state['brand_name']} ({st.session_state['business_category']})</strong>
        </div>
        <p style="color: #047857; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.5rem;">
            {st.session_state['last_analysis_summary']} Seluruh 10 indikator audit, skor kematangan, kesenjangan kutipan, modul Auto-Fix, dan panduan edukasi telah disesuaikan secara real-time.
        </p>
        <div>{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# LOGIKA HITUNG SKOR SECARA REAL-TIME
# ==============================================================================
current_answers = {k: st.session_state.get(k, False) for k in DEFAULT_CHECKS.keys()}
score_data = calculate_geo_score(current_answers)
citation_gaps = analyze_citation_gaps(current_answers)
recom_data = get_prioritized_recommendations(current_answers)

total_score = score_data["total_score"]
tier_badge = score_data["tier_badge"]
tier_name = score_data["tier_name"]
tier_color = score_data["tier_color"]
tier_description = score_data["tier_description"]
pillar_results = score_data["pillar_results"]


# ==============================================================================
# 5 TAB UTAMA INTERFACE
# ==============================================================================
tab_audit, tab_dashboard, tab_testing, tab_autofix, tab_guide = st.tabs([
    "📋 1. Checklist Audit (10 Indikator)",
    "📊 2. Dasbor Skor & Kesenjangan Kutipan",
    "🤖 3. Automated AI Testing & Audit",
    "⚡ 4. Auto-Fix Generator",
    "📖 5. Panduan Edukasi GEO"
])


# ==============================================================================
# TAB 1: CHECKLIST AUDIT (10 INDIKATOR DALAM 4 PILAR)
# ==============================================================================
with tab_audit:
    st.markdown("### 📋 Evaluasi Kesiapan GEO (10 Indikator Kunci)")
    st.write(
        "Centang setiap pernyataan di bawah ini yang sudah benar-benar diterapkan pada website dan kehadiran digital merek Anda. "
        "Skor dan analisis kesenjangan akan terhitung secara otomatis secara instan."
    )

    # Indikator ringkasan skor kecil di atas
    col_score_mini, col_stat_mini = st.columns([1, 3])
    with col_score_mini:
        st.metric(
            label="Skor GEO Saat Ini",
            value=f"{total_score} / 100",
            delta=f"{tier_badge} {tier_name.split('(')[0].strip()}"
        )
    with col_stat_mini:
        checked_total = sum(1 for v in current_answers.values() if v)
        st.info(f"**Progres:** {checked_total} dari 10 indikator tercentang. Kategori status: **{tier_name}**")

    st.markdown("---")

    # KOTAK AKSI & HASIL LIVE WEB CRAWLER
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 1.2rem 1.4rem; margin-bottom: 1.2rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                        <span style="font-size: 1.2rem;">🌐</span>
                        <strong style="color: #0f172a; font-size: 1.05rem;">Live Crawler Otomatis: Fetch URL & Analisis robots.txt AI</strong>
                        <span style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">REAL-TIME INSPECTION</span>
                    </div>
                    <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0; line-height: 1.5;">
                        Pindai langsung server website Anda secara real-time: Mendeteksi apakah <code>/robots.txt</code> mengizinkan <strong>GPTBot, ClaudeBot, Google-Extended, dan PerplexityBot</strong>, memvalidasi enkripsi HTTPS, serta mengukur waktu respons (TTFB).
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            st.caption(f"Target URL: `{st.session_state['website_url']}` (Ubah di sidebar jika ingin menguji domain lain)")
        with col_run2:
            if st.button("🚀 Jalankan Live Audit Web", type="primary", use_container_width=True, key="btn_run_live_tab1"):
                target_url = st.session_state["website_url"].strip()
                if not target_url:
                    st.error("Silakan masukkan URL website di sidebar.")
                else:
                    with st.spinner(f"🔍 Menghubungi server live {target_url} dan memeriksa robots.txt..."):
                        # 1. Analisis Heuristik Konten, Data, dan Profil Merek
                        inputs_data = {
                            "brand_name": st.session_state["brand_name"],
                            "website_url": st.session_state["website_url"],
                            "business_category": st.session_state["business_category"],
                            "phone_number": st.session_state["phone_number"],
                            "location_info": st.session_state["location_info"],
                            "product_name": st.session_state["product_name"],
                            "price_range": st.session_state["price_range"],
                            "key_advantages": st.session_state["key_advantages"]
                        }
                        analysis_res = analyze_inputs_to_indicators(inputs_data)
                        for ind_k, ind_v in analysis_res["answers"].items():
                            st.session_state[ind_k] = ind_v
                        st.session_state["last_analysis_summary"] = analysis_res["summary"]
                        st.session_state["last_detected_tags"] = analysis_res["detected_data"]
                        st.session_state["last_analysis_reasons"] = analysis_res["reasons"]

                        # 2. Live Web Crawl
                        crawl_res = live_crawl_website(target_url)
                        if crawl_res["success"]:
                            st.session_state["tech_robots"] = crawl_res["tech_robots_passed"]
                            st.session_state["tech_https_speed"] = crawl_res["tech_https_speed_passed"]
                            if crawl_res.get("html_inspections", {}).get("has_schema_jsonld"):
                                st.session_state["schema_org"] = True
                                st.session_state["schema_product_faq"] = True
                            if crawl_res.get("html_inspections", {}).get("has_headings"):
                                st.session_state["content_headings"] = True
                            st.session_state["last_live_crawl"] = crawl_res
                            st.toast("✅ Live Audit Berhasil! Seluruh 10 indikator GEO telah terisi otomatis.", icon="🌐")
                            st.rerun()
                        else:
                            st.error(f"❌ {crawl_res.get('error_message')}")

    # JIKA SUDAH ADA HASIL LIVE CRAWL, TAMPILKAN PANEL STATUS KAYA
    if st.session_state.get("last_live_crawl"):
        crawl = st.session_state["last_live_crawl"]
        bot_perms = crawl.get("ai_bots_permissions", {})
        
        st.markdown(f"""
        <div style="background: white; border: 1.5px solid #10b981; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <div>
                    <span style="background: #10b981; color: white; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 6px; text-transform: uppercase;">Live Server Inspection Passed</span>
                    <strong style="color: #064e3b; font-size: 1rem; margin-left: 0.5rem;">{crawl['url_tested']}</strong>
                </div>
                <span style="font-size: 0.8rem; color: #64748b; font-weight: 600;">HTTP Status: {crawl['status_code']}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.8rem; margin-bottom: 0.8rem;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem 1rem; border-radius: 10px;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700;">Kecepatan Respon (TTFB)</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: {'#059669' if crawl['speed_under_3s'] else '#dc2626'};">
                        ⚡ {crawl['response_time_sec']}s ({crawl['response_time_ms']} ms)
                    </div>
                    <div style="font-size: 0.75rem; color: {'#059669' if crawl['speed_under_3s'] else '#dc2626'}; font-weight: 600;">
                        {'✓ Lolos standar GEO (< 3.0s)' if crawl['speed_under_3s'] else '⚠️ Respon lambat (>= 3.0s)'}
                    </div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem 1rem; border-radius: 10px;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700;">Protokol Enkripsi</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: {'#059669' if crawl['https_active'] else '#dc2626'};">
                        🔒 {'HTTPS Aktif' if crawl['https_active'] else 'HTTP Tidak Aman'}
                    </div>
                    <div style="font-size: 0.75rem; color: #059669; font-weight: 600;">
                        {'✓ Sertifikat SSL Terverifikasi' if crawl['ssl_verified'] else '⚠️ Sertifikat SSL tidak valid'}
                    </div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem 1rem; border-radius: 10px;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700;">File /robots.txt</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">
                        📄 {'Ditemukan (200 OK)' if crawl['robots_found'] else 'Default Open (404)'}
                    </div>
                    <div style="font-size: 0.75rem; color: {'#059669' if crawl['tech_robots_passed'] else '#dc2626'}; font-weight: 600;">
                        {'✓ Seluruh Bot AI Diizinkan' if crawl['tech_robots_passed'] else '⚠️ Ada Bot AI Diblokir'}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Matriks Izin 4 Bot AI
        st.markdown("##### 🤖 Status Izin Crawler AI Berdasarkan robots.txt:")
        bot_cols = st.columns(4)
        for i, (bot_name, b_info) in enumerate(bot_perms.items()):
            with bot_cols[i % 4]:
                if b_info["allowed"]:
                    st.success(f"**{bot_name}**\n\n🟢 Diizinkan\n\n_{b_info['reason']}_")
                else:
                    st.error(f"**{bot_name}**\n\n🔴 Diblokir\n\n_{b_info['reason']}_")

        with st.expander("📋 Lihat Catatan Log Live Audit & Cuplikan robots.txt"):
            st.markdown(f"**URL robots.txt:** `{crawl['robots_url']}`")
            if crawl.get("robots_snippet"):
                st.code(crawl["robots_snippet"], language="plaintext")
            st.markdown("**Catatan Eksekusi Crawler:**")
            for log_line in crawl.get("logs", []):
                st.write(f"- {log_line}")

        st.markdown("---")

    # Render 4 Pilar
    for p_key, p_val in GEO_PILLARS.items():
        p_res = pillar_results[p_key]
        with st.container():
            st.markdown(f"""
            <div class="pilar-card">
                <div class="pilar-header">
                    <div>
                        <span style="font-size: 1.3rem; margin-right: 0.4rem;">{p_val['icon']}</span>
                        <strong style="font-size: 1.15rem; color: #0f172a;">{p_val['title']}</strong>
                    </div>
                    <span class="pilar-badge-weight">Bobot: {int(p_val['weight']*100)}% | Skor: {p_res['earned_score']:.1f}/{p_res['max_score']}</span>
                </div>
                <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">{p_val['description']}</p>
            """, unsafe_allow_html=True)

            # Checkbox per indikator
            for ind in p_val["indicators"]:
                ind_id = ind["id"]
                col_chk, col_exp = st.columns([4, 1])
                with col_chk:
                    is_checked = st.checkbox(
                        label=f"**{ind['label']}** (+{ind['weight_total']}%)",
                        value=st.session_state[ind_id],
                        key=f"chk_{ind_id}",
                        help=ind["help"]
                    )
                    # Sinkronkan ke session_state utama jika berubah
                    if is_checked != st.session_state[ind_id]:
                        st.session_state[ind_id] = is_checked
                        st.rerun()

                    st.markdown(f"<span style='color: #64748b; font-size: 0.85rem; margin-left: 1.8rem; display: block;'>{ind['sublabel']}</span>", unsafe_allow_html=True)
                
                with col_exp:
                    if st.session_state[ind_id]:
                        st.success("✅ Terpenuhi")
                    else:
                        st.warning("⚠️ Belum Ada")

            st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: DASBOR SKOR & ANALISIS KESENJANGAN KUTIPAN
# ==============================================================================
with tab_dashboard:
    st.markdown("### 📊 Dasbor Skor & Kesenjangan Kutipan (Citation Gap)")
    
    # Hero Score Box
    st.markdown(f"""
    <div class="score-card" style="background: linear-gradient(135deg, {tier_color} 0%, #1e293b 100%);">
        <div style="text-transform: uppercase; font-size: 0.9rem; letter-spacing: 0.1em; opacity: 0.9;">Total GEO Readiness Score</div>
        <div class="score-number">{total_score}<span style="font-size: 2rem; opacity: 0.7;">/100</span></div>
        <div class="score-label">{tier_badge} {tier_name}</div>
        <p style="max-width: 750px; margin: 1rem auto 0 auto; font-size: 0.95rem; opacity: 0.95; line-height: 1.6;">
            {tier_description}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Dua Grafik Plotly: Radar Chart & Bar Chart
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 🕸️ Radar Keseimbangan 4 Pilar GEO")
        # Data untuk Radar Chart
        categories_radar = [
            "Aksesibilitas Teknis (20%)",
            "Struktur Konten & BLUF (30%)",
            "Schema JSON-LD (20%)",
            "Otoritas Off-Page (30%)"
        ]
        values_radar = [
            pillar_results["pilar_1"]["percentage"],
            pillar_results["pilar_2"]["percentage"],
            pillar_results["pilar_3"]["percentage"],
            pillar_results["pilar_4"]["percentage"]
        ]
        # Tutup polygon radar
        categories_radar_closed = categories_radar + [categories_radar[0]]
        values_radar_closed = values_radar + [values_radar[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_radar_closed,
            theta=categories_radar_closed,
            fill='toself',
            fillcolor='rgba(15, 118, 110, 0.3)',
            line=dict(color='#0F766E', width=3),
            marker=dict(size=8, color='#047857'),
            name='Tingkat Kesiapan'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    ticksuffix="%",
                    tickfont=dict(size=10)
                )
            ),
            showlegend=False,
            height=360,
            margin=dict(l=40, r=40, t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_chart2:
        st.markdown("#### 📊 Ketercapaian Skor vs Bobot Maksimal")
        # Bar chart perolehan nilai vs max nilai
        pilar_names = ["Teknis (20%)", "Konten BLUF (30%)", "Schema (20%)", "Otoritas (30%)"]
        earned_vals = [pillar_results[p]["earned_score"] for p in ["pilar_1", "pilar_2", "pilar_3", "pilar_4"]]
        max_vals = [pillar_results[p]["max_score"] for p in ["pilar_1", "pilar_2", "pilar_3", "pilar_4"]]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name='Skor Diraih',
            x=pilar_names,
            y=earned_vals,
            marker_color='#059669',
            text=[f"{v} pt" for v in earned_vals],
            textposition='auto'
        ))
        fig_bar.add_trace(go.Bar(
            name='Bobot Maksimal',
            x=pilar_names,
            y=max_vals,
            marker_color='#e2e8f0',
            opacity=0.75
        ))
        fig_bar.update_layout(
            barmode='overlay',
            height=360,
            yaxis=dict(range=[0, 35], title="Poin Skor"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=20, t=30, b=30)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Analisis Kesenjangan Kutipan (Citation Gap Analysis)
    st.markdown("### ⚠️ Analisis Kesenjangan Kutipan (Citation Gap Analysis)")
    st.write(
        "Kesenjangan kutipan (*Citation Gap*) terjadi ketika AI mengenali query calon pembeli, "
        "namun menolak atau ragu menyebutkan merek Anda karena ketiadaan bukti data terstruktur atau grounding fakta."
    )

    if not citation_gaps:
        st.success("🎉 **Luar Biasa! Tidak Ditemukan Kesenjangan Kutipan yang Kritis.** Website dan merek Anda telah memenuhi seluruh 10 indikator dasar GEO.")
    else:
        for gap in citation_gaps:
            card_class = "gap-card-critical" if "Kritis" in gap["impact"] or "Tinggi" in gap["impact"] else "gap-card"
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <strong style="color: #0f172a; font-size: 1.05rem;">{gap['gap_title']}</strong>
                    <span style="font-size: 0.75rem; font-weight: 700; background: {gap['impact_color']}; color: white; padding: 2px 8px; border-radius: 4px;">Dampak: {gap['impact']}</span>
                </div>
                <p style="color: #475569; font-size: 0.9rem; margin-bottom: 0.4rem;">{gap['explanation']}</p>
                <div style="font-size: 0.85rem; color: #047857; font-weight: 600;">
                    💡 Rekomendasi Solusi: {gap['fix_summary']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Rekomendasi Perbaikan Berbasis Jawaban (Quick Wins vs Strategic)
    st.markdown("### 🎯 Rencana Aksi Perbaikan Berdasarkan Prioritas")
    col_rec1, col_rec2 = st.columns(2)

    with col_rec1:
        st.markdown("#### ⚡ Quick Wins (< 1 Hari Pengerjaan)")
        st.caption("Langkah praktis yang dapat langsung diterapkan hari ini tanpa biaya tambahan.")
        if not recom_data["quick_wins"]:
            st.success("Semua Quick Wins sudah Anda selesaikan! 🚀")
        else:
            for item in recom_data["quick_wins"]:
                st.markdown(f"""
                <div class="recom-box">
                    <div>
                        <span class="recom-pill pill-quick">{item['pilar']}</span>
                        <strong style="color: #0f172a;">{item['title']}</strong>
                        <span style="float: right; font-size: 0.75rem; color: #64748b;">⏱️ {item['effort']}</span>
                    </div>
                    <p style="color: #475569; font-size: 0.85rem; margin-top: 0.5rem; margin-bottom: 0;">{item['action']}</p>
                </div>
                """, unsafe_allow_html=True)

    with col_rec2:
        st.markdown("#### 🏆 Strategic Improvements (1-4 Minggu)")
        st.caption("Pembangunan aset digital berkelanjutan untuk memenangkan sitasi jangka panjang.")
        if not recom_data["strategic"]:
            st.success("Semua fondasi strategis telah terpasang dengan baik! 🌟")
        else:
            for item in recom_data["strategic"]:
                st.markdown(f"""
                <div class="recom-box">
                    <div>
                        <span class="recom-pill pill-strat">{item['pilar']}</span>
                        <strong style="color: #0f172a;">{item['title']}</strong>
                        <span style="float: right; font-size: 0.75rem; color: #64748b;">⏱️ {item['effort']}</span>
                    </div>
                    <p style="color: #475569; font-size: 0.85rem; margin-top: 0.5rem; margin-bottom: 0;">{item['action']}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Fitur Ekspor Ringkasan Laporan Audit
    st.markdown("#### 📥 Unduh Dokumen Ringkasan Audit GEO")
    report_markdown = f"""# LAPORAN AUDIT KESIAPAN GEO (GENERATIVE ENGINE OPTIMIZATION)
Tanggal Audit: {datetime.now().strftime('%d %B %Y')}
Aplikasi: GEO Audit App Nusantara

## 1. IDENTITAS UMKM
- Nama Merek: {st.session_state['brand_name']}
- Website: {st.session_state['website_url']}
- Kategori Bisnis: {st.session_state['business_category']}
- Lokasi: {st.session_state['location_info']}
- WhatsApp: {st.session_state['phone_number']}

## 2. HASIL SKOR AUDIT
- Total Skor GEO: {total_score} / 100
- Kategori Kematangan: {tier_badge} {tier_name}
- Deskripsi Status: {tier_description}

### Rincian Ketercapaian Pilar:
1. Aksesibilitas Teknis & AI Crawlers (20%): {pillar_results['pilar_1']['earned_score']} / {pillar_results['pilar_1']['max_score']} pt ({pillar_results['pilar_1']['percentage']}%)
2. Kejelasan Struktur Konten & BLUF (30%): {pillar_results['pilar_2']['earned_score']} / {pillar_results['pilar_2']['max_score']} pt ({pillar_results['pilar_2']['percentage']}%)
3. Data Terstruktur / Schema JSON-LD (20%): {pillar_results['pilar_3']['earned_score']} / {pillar_results['pilar_3']['max_score']} pt ({pillar_results['pilar_3']['percentage']}%)
4. Otoritas Merek & Sebutan Luar (30%): {pillar_results['pilar_4']['earned_score']} / {pillar_results['pilar_4']['max_score']} pt ({pillar_results['pilar_4']['percentage']}%)

## 3. KESENJANGAN KUTIPAN (CITATION GAPS)
"""
    for g in citation_gaps:
        report_markdown += f"- [{g['impact']}] {g['gap_title']}: {g['fix_summary']}\n"

    report_markdown += f"""
## 4. REKOMENDASI PRIORITAS
### Quick Wins:
"""
    for q in recom_data["quick_wins"]:
        report_markdown += f"- {q['title']} ({q['effort']}): {q['action']}\n"

    report_markdown += f"""
### Strategic Improvements:
"""
    for s in recom_data["strategic"]:
        report_markdown += f"- {s['title']} ({s['effort']}): {s['action']}\n"

    report_markdown += """
---
Dibuat secara otomatis oleh GEO Audit App Nusantara
Solusi AI-Ready untuk UMKM Indonesia Naik Kelas
"""

    st.download_button(
        label="📄 Unduh Laporan Lengkap (.md / Markdown)",
        data=report_markdown,
        file_name=f"GEO_Audit_{st.session_state['brand_name'].replace(' ', '_')}.md",
        mime="text/markdown",
        help="Unduh file laporan hasil audit untuk arsip atau dikirimkan ke klien/manajemen."
    )


# ==============================================================================
# TAB 3: AUTOMATED AI TESTING & AUDIT (STRICT MATCHING & 5-TIME SAMPLING)
# ==============================================================================
with tab_testing:
    # Banner Pengantar Modul
    st.markdown("""
    <div class="ai-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 0.75rem; font-weight: 800; padding: 3px 10px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em;">AI Search RAG Simulator &amp; Probabilistic Auditor</span>
                <h2 style="font-size: 1.65rem; font-weight: 800; margin: 0.5rem 0 0.4rem 0; color: white;">
                    🤖 Automated AI Testing &amp; Audit (5-Time Sampling)
                </h2>
                <p style="color: #94a3b8; font-size: 0.92rem; margin: 0; line-height: 1.6; max-width: 950px;">
                    Uji keterpanggilan merek UMKM Anda secara probabilistik ke mesin AI RAG menggunakan <strong>Strict Matching RegEx (<code>\\b</code>)</strong> 
                    dan <strong>5-Time Independent Sampling</strong> per kueri untuk mengukur konsistensi visibilitas nyata generasi model bahasa.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. KOMPONEN INPUT MEREK & ALIAS
    col_inp1, col_inp2 = st.columns([1, 1])
    with col_inp1:
        cur_brand_name = st.text_input(
            "Nama Merek Utama:",
            value=st.session_state.get("brand_name", "Kopi Arabika Toraja Baji"),
            key="ai_input_brand_name",
            help="Nama merek utama yang akan dicocokkan secara ketat dengan batas kata (\\b)."
        )
        if cur_brand_name != st.session_state.get("brand_name"):
            st.session_state["brand_name"] = cur_brand_name
            st.session_state["ai_test_5x_responses"] = None

    with col_inp2:
        default_alias_str = st.session_state.get(
            "brand_aliases",
            f"{st.session_state.get('website_url', 'kopitorajabaji.id').replace('https://','').replace('http://','').replace('/','')}, Kopi Toraja Baji, Toraja Baji"
        )
        cur_aliases_input = st.text_input(
            "Daftar Alias / Variasi Merek (pisahkan koma):",
            value=default_alias_str,
            key="ai_input_brand_aliases",
            help="Domain website, akronim, variasi ejaan resmi, atau nama tanpa spasi yang juga sah dianggap sebagai sebutan merek Anda."
        )
        if cur_aliases_input != st.session_state.get("brand_aliases"):
            st.session_state["brand_aliases"] = cur_aliases_input
            st.session_state["ai_test_5x_responses"] = None

    # Parse daftar alias bersih
    active_aliases = [a.strip() for a in cur_aliases_input.split(",") if a.strip()]

    # 2. AREA TEKS KUERI PROMPT PENGUJIAN
    default_prompt_text = f"Rekomendasikan {st.session_state.get('business_category', 'Kuliner & Minuman')} terbaik dari {st.session_state.get('location_info', 'Makale, Toraja').split(',')[0]} yang berkualitas tinggi dan cocok untuk oleh-oleh."
    
    col_pr1, col_pr2 = st.columns([3, 1])
    with col_pr1:
        cur_query_prompt = st.text_area(
            "Kueri Prompt Pengujian:",
            value=st.session_state.get("ai_test_5x_prompt", default_prompt_text) or default_prompt_text,
            height=78,
            key="ai_input_query_prompt",
            help="Pertanyaan atau kueri pencarian percakapan yang diujikan 5 kali secara berurutan ke model AI RAG."
        )
        if cur_query_prompt != st.session_state.get("ai_test_5x_prompt"):
            st.session_state["ai_test_5x_prompt"] = cur_query_prompt
            st.session_state["ai_test_5x_responses"] = None

    with col_pr2:
        st.markdown("**Preset Kueri Cepat:**")
        benchmark_presets = build_benchmark_queries(
            brand_name=cur_brand_name,
            product_name=st.session_state.get("product_name", ""),
            category=st.session_state.get("business_category", ""),
            location=st.session_state.get("location_info", "")
        )
        preset_names = ["(Gunakan Teks Kueri Manual)"] + [f"{p['type']}" for p in benchmark_presets]
        preset_sel = st.selectbox("Pilih Kueri Benchmark:", preset_names, label_visibility="collapsed")
        if preset_sel != "(Gunakan Teks Kueri Manual)":
            for p in benchmark_presets:
                if p["type"] == preset_sel:
                    st.session_state["ai_test_5x_prompt"] = p["prompt"]
                    st.session_state["ai_test_5x_responses"] = None
                    st.rerun()

    # 3. RADIO BUTTON PILIHAN MODA PENGUJIAN
    test_mode = st.radio(
        "Pilihan Moda Pengujian:",
        ["Mode Simulasi (Demo)", "Mode Tempel Manual / API Key"],
        horizontal=True,
        key="ai_test_mode_selector"
    )

    # Inisialisasi Data Sampling 5x Jika Belum Ada
    if st.session_state.get("ai_test_5x_responses") is None:
        st.session_state["ai_test_5x_responses"] = generate_5x_simulated_rag_responses(
            query_prompt=cur_query_prompt,
            brand_name=cur_brand_name,
            product_name=st.session_state.get("product_name", ""),
            category=st.session_state.get("business_category", ""),
            location=st.session_state.get("location_info", ""),
            website_url=st.session_state.get("website_url", ""),
            aliases=active_aliases,
            scenario="ai_ready"
        )

    # KONTROL & AKSI PENGUJIAN SESUAI MODA
    if test_mode == "Mode Simulasi (Demo)":
        with st.container():
            col_sc1, col_sc2 = st.columns([2, 1])
            with col_sc1:
                scenario_choice = st.selectbox(
                    "Skenario Konsistensi Visibilitas Simulasi:",
                    [
                        "🟢 AI-Ready (4-5 dari 5 Run Ditemukan)",
                        "🟡 Variable Visibility (3 dari 5 Run Ditemukan)",
                        "🔴 Invisible to AI (1 dari 5 Run Ditemukan)"
                    ],
                    key="sel_sim_scenario"
                )
            with col_sc2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🚀 Jalankan 5x Sampling Audit (Simulasi RAG)", type="primary", use_container_width=True):
                    sc_code = "ai_ready"
                    if "Variable" in scenario_choice:
                        sc_code = "variable"
                    elif "Invisible" in scenario_choice:
                        sc_code = "invisible"

                    with st.spinner("Menjalankan 5x sampling independen terhadap kueri..."):
                        st.session_state["ai_test_5x_responses"] = generate_5x_simulated_rag_responses(
                            query_prompt=cur_query_prompt,
                            brand_name=cur_brand_name,
                            product_name=st.session_state.get("product_name", ""),
                            category=st.session_state.get("business_category", ""),
                            location=st.session_state.get("location_info", ""),
                            website_url=st.session_state.get("website_url", ""),
                            aliases=active_aliases,
                            scenario=sc_code
                        )
                        st.success("5x Sampling berhasil dijalankan!")
                        st.rerun()

    else:
        # Mode Tempel Manual / API Key
        st.markdown("##### 🛠️ Masukan Manual / Eksternal API:")
        sub_tab_manual, sub_tab_api = st.tabs(["📝 Tempel Manual 5 Respons AI", "⚡ Jalankan 5x Sampling Live via API Key"])

        with sub_tab_manual:
            st.caption("Tempelkan 5 respons jawaban hasil generasi ChatGPT / Perplexity / Gemini untuk kueri yang sama:")
            manual_responses = []
            for run_i in range(1, 6):
                sample_val = st.session_state["ai_test_5x_responses"][run_i - 1] if st.session_state.get("ai_test_5x_responses") else ""
                val_text = st.text_area(
                    f"Respons AI untuk Sampling #{run_i}:",
                    value=sample_val,
                    height=95,
                    key=f"manual_paste_sample_{run_i}"
                )
                manual_responses.append(val_text)

            if st.button("🔍 Analisis 5 Respons yang Ditempel", type="primary", use_container_width=True):
                st.session_state["ai_test_5x_responses"] = manual_responses
                st.success("Analisis 5 respons berhasil diperbarui!")
                st.rerun()

        with sub_tab_api:
            st.info("⚡ Masukkan API Key untuk melakukan 5 kali pemanggilan sekuensial secara langsung ke server OpenAI atau Perplexity.")
            col_ap1, col_ap2, col_ap3 = st.columns([1, 2, 1])
            with col_ap1:
                api_provider = st.selectbox("Provider API:", ["OpenAI (ChatGPT)", "Perplexity AI"], key="api_5x_provider")
            with col_ap2:
                api_key_val = st.text_input("API Key:", type="password", value=st.session_state.get("ai_test_api_key", ""), key="api_5x_key_input")
                st.session_state["ai_test_api_key"] = api_key_val
            with col_ap3:
                model_tag = "sonar" if "Perplexity" in api_provider else "gpt-4o-mini"
                st.caption(f"Model: `{model_tag}` (Temp: 0.7)")

            if st.button("🚀 Jalankan 5x Sampling Live via API", type="primary", use_container_width=True):
                if not api_key_val.strip():
                    st.error("Silakan masukkan API Key Anda.")
                else:
                    with st.spinner("Mengirimkan 5 kueri sekuensial ke server API..."):
                        p_code = "perplexity" if "Perplexity" in api_provider else "openai"
                        live_res = fetch_live_ai_completion_5x(
                            provider=p_code,
                            api_key=api_key_val,
                            prompt=cur_query_prompt,
                            model=model_tag
                        )
                        if live_res["success"]:
                            st.session_state["ai_test_5x_responses"] = live_res["sample_responses"]
                            st.success("5x Sampling live API berhasil diselesaikan!")
                            st.rerun()
                        else:
                            st.error(f"Gagal memanggil API: {live_res.get('errors')}")

    # ==========================================================================
    # DASBOR HASIL AUDIT 5-TIME SAMPLING
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📊 Dasbor Hasil Audit 5-Time Sampling")

    current_samples = st.session_state.get("ai_test_5x_responses") or [""] * 5
    audit_data = run_5x_sampling_audit(
        query_prompt=cur_query_prompt,
        brand_name=cur_brand_name,
        aliases=active_aliases,
        sample_responses=current_samples
    )

    prob_score = audit_data["probability_score"]
    found_runs = audit_data["found_count"]
    tier_badge = audit_data["consistency_badge"]
    tier_desc = audit_data["consistency_description"]

    col_res1, col_res2 = st.columns([1, 2])
    with col_res1:
        st.metric(
            label="🎯 Skor Probabilitas Sitasi",
            value=f"{prob_score}%",
            delta=f"{found_runs}/5 Run Ditemukan",
            delta_color="normal" if prob_score >= 60 else "inverse"
        )

    with col_res2:
        st.markdown(f"""
        <div style="background: white; border: 1.5px solid {audit_data['consistency_color']}; border-radius: 12px; padding: 1rem 1.25rem; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                <strong style="color: #0f172a; font-size: 1.05rem;">{tier_badge}</strong>
                <span style="font-size: 0.75rem; font-weight: 700; background: {audit_data['consistency_color']}; color: white; padding: 2px 8px; border-radius: 4px;">
                    Strict RegEx Matching (\\b)
                </span>
            </div>
            <p style="color: #475569; font-size: 0.85rem; margin-bottom: 0.6rem; line-height: 1.5;">
                {tier_desc}
            </p>
        </div>
        """, unsafe_allow_html=True)
        # Visual Progress Bar
        st.progress(float(prob_score) / 100.0)
        st.caption(f"Tingkat Konsistensi: **{prob_score}%** (0% = Belum Siap, 50% = Cukup Siap, 100% = Sangat Siap GEO AI)")

    st.markdown("---")

    # TABEL RINGKASAN DATA PER SAMPLING (st.dataframe)
    st.markdown("##### 📋 Ringkasan Rincian per Sampling (#1 s.d. #5):")
    st.dataframe(audit_data["dataframe_rows"], use_container_width=True, height=220)

    # 4 SUBTAB RINCIAN
    st.markdown("---")
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🎯 1. Rincian Konteks Sebutan & Snippet Per-Run",
        "🔗 2. Citation Link Extractor (5 Run)",
        "🗺️ 3. Citation Gap Map & Share of Voice",
        "📄 4. Log & Teks Respons Mentah AI"
    ])

    # --------------------------------------------------------------------------
    # SUBTAB 1: RINCIAN DETEKSI PER RUN
    # --------------------------------------------------------------------------
    with subtab1:
        st.markdown(f"#### 🎯 Rincian Deteksi Strict Matching untuk: **{cur_brand_name}**")
        st.caption(f"Alias aktif yang didaftarkan: `{', '.join(active_aliases) if active_aliases else '(Hanya Nama Merek Utama)'}`")

        for r_item in audit_data["run_records"]:
            run_idx = r_item["run_index"]
            is_found = r_item["detected"]
            exp_title = f"{'🟢' if is_found else '🔴'} Sampling #{run_idx}: {r_item['status_icon']} — Posisi: {r_item['position']} | {r_item['match_count']}x Sebutan"

            with st.expander(exp_title, expanded=(run_idx == 1)):
                col_sub1, col_sub2, col_sub3 = st.columns([1, 1, 1])
                with col_sub1:
                    st.write(f"**Status:** {r_item['status_icon']}")
                    st.write(f"**Frekuensi:** {r_item['match_count']} kali")
                with col_sub2:
                    st.write(f"**Istilah Cocok:** `{r_item['matched_term']}`")
                    st.write(f"**Posisi Relatif:** {r_item['position_badge']}")
                with col_sub3:
                    st.write(f"**Sentimen:** {r_item['sentiment_label']}")
                    st.write(f"**Seluruh Istilah:** `{', '.join(r_item['matched_terms']) if r_item['matched_terms'] else '-'}`")

                st.markdown("**Cuplikan Konteks Teks:**")
                st.markdown(f'<div class="snippet-box">{r_item["snippet"]}</div>', unsafe_allow_html=True)

                with st.expander(f"Lihat Teks Lengkap Sampling #{run_idx}"):
                    st.text(r_item["full_response"])

    # --------------------------------------------------------------------------
    # SUBTAB 2: CITATION LINK EXTRACTOR
    # --------------------------------------------------------------------------
    with subtab2:
        st.markdown("#### 🔗 Ekstraksi Tautan Sitasi RAG (Akumulasi 5 Run)")
        combined_5x_text = "\n\n".join(current_samples)
        citations_5x = extract_and_categorize_citations(combined_5x_text, st.session_state.get("website_url", ""))

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric("Total Sitasi Diekstrak", f"{citations_5x['total_citations']} Tautan")
        with col_c2:
            st.metric("Tautan Aset Resmi Merek", f"{citations_5x['brand_citations_count']} URL", delta=f"{citations_5x['third_party_citations_count']} Sumber Pihak Ketiga")

        st.markdown("##### 🏷️ Distribusi Kategori Sumber:")
        cat_badge_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">'
        for cat_k, cat_count in citations_5x.get("category_distribution", {}).items():
            cat_obj = CITATION_CATEGORIES.get(cat_k, CITATION_CATEGORIES["other"])
            cat_badge_html += f"""
            <span style="background: {cat_obj['badge_color']}; color: white; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 700;">
                {cat_obj['icon']} {cat_obj['name']}: {cat_count} Sitasi
            </span>
            """
        cat_badge_html += '</div>'
        st.markdown(cat_badge_html, unsafe_allow_html=True)

        col_tbl_a, col_tbl_b = st.columns(2)
        with col_tbl_a:
            st.markdown("##### 🌐 Tautan Mengarah ke Aset Merek Anda:")
            brand_urls = [c for c in citations_5x["citations"] if c["is_brand_asset"]]
            if brand_urls:
                for b_u in brand_urls[:5]:
                    st.markdown(f"""
                    <div class="citation-card" style="border-left: 4px solid #059669;">
                        <strong style="color: #065f46; font-size: 0.92rem;">{b_u['title']}</strong><br/>
                        <a href="{b_u['url']}" target="_blank" style="color: #0284c7; font-size: 0.82rem; word-break: break-all;">{b_u['url']}</a>
                        <div style="margin-top: 0.3rem;">
                            <span style="background: #dcfce7; color: #15803d; font-size: 0.72rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">ASET RESMI UMKM</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Tidak ada tautan langsung ke website merek Anda yang disitasi.")

        with col_tbl_b:
            st.markdown("##### 🌍 Tautan Pihak Ketiga (Third-Party):")
            tp_urls = [c for c in citations_5x["citations"] if not c["is_brand_asset"]]
            if tp_urls:
                for t_u in tp_urls[:5]:
                    st.markdown(f"""
                    <div class="citation-card" style="border-left: 4px solid {t_u['badge_color']};">
                        <strong style="color: #0f172a; font-size: 0.92rem;">{t_u['title']}</strong><br/>
                        <a href="{t_u['url']}" target="_blank" style="color: #0284c7; font-size: 0.82rem; word-break: break-all;">{t_u['url']}</a>
                        <div style="margin-top: 0.3rem;">
                            <span style="background: {t_u['badge_color']}; color: white; font-size: 0.72rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">{t_u['category_icon']} {t_u['category_name']}</span>
                            <span style="color: #64748b; font-size: 0.75rem; margin-left: 0.5rem;">Domain: {t_u['domain']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Tidak ada tautan pihak ketiga.")

    # --------------------------------------------------------------------------
    # SUBTAB 3: CITATION GAP MAP & SHARE OF VOICE
    # --------------------------------------------------------------------------
    with subtab3:
        st.markdown("#### 🗺️ Peta Kesenjangan Kutipan (Citation Gap Map)")
        raw_comp_str = st.session_state.get("ai_test_competitors", "Kopi Kenangan, Otten Coffee, Anomali Coffee, Kapal Api Specialty")
        active_comp_list = [c.strip() for c in raw_comp_str.split(",") if c.strip()]

        sim_5x_records = []
        for i, s_txt in enumerate(current_samples, 1):
            sim_5x_records.append({
                "prompt": f"Sampling #{i} - {cur_query_prompt[:45]}...",
                "response_text": s_txt,
                "engine_name": f"Sampling Run #{i}"
            })

        gap_data_5x = analyze_citation_gap_matrix(sim_5x_records, cur_brand_name, active_comp_list)

        col_gv1, col_gv2 = st.columns(2)
        with col_gv1:
            st.markdown("##### 📊 Share of Voice (%) Merek vs Kompetitor")
            sov_names = list(gap_data_5x["sov_breakdown"].keys())
            sov_vals = list(gap_data_5x["sov_breakdown"].values())
            colors_bar = ["#059669" if name == cur_brand_name else "#94a3b8" for name in sov_names]

            fig_sov = go.Figure()
            fig_sov.add_trace(go.Bar(
                x=sov_vals,
                y=sov_names,
                orientation='h',
                marker_color=colors_bar,
                text=[f"{v}%" for v in sov_vals],
                textposition='outside'
            ))
            fig_sov.update_layout(
                height=300,
                xaxis=dict(title="Share of Voice (%)", range=[0, max(sov_vals + [40]) + 15]),
                yaxis=dict(autorange="reversed"),
                margin=dict(l=20, r=20, t=20, b=30)
            )
            st.plotly_chart(fig_sov, use_container_width=True)

        with col_gv2:
            st.markdown("##### 💡 Auto-Actionable Insights")
            for ins in gap_data_5x["insights"][:2]:
                st.markdown(f"""
                <div class="insight-card" style="border-left: 4px solid {ins['color']};">
                    <strong style="color: #0f172a; font-size: 0.95rem;">{ins['icon']} {ins['title']}</strong>
                    <p style="color: #334155; font-size: 0.85rem; margin: 0.3rem 0 0 0; line-height: 1.5;">{ins['recommendation']}</p>
                </div>
                """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # SUBTAB 4: RAW RESPONSE
    # --------------------------------------------------------------------------
    with subtab4:
        st.markdown("#### 📄 Teks Mentah Respons 5x Sampling")
        sel_raw_run = st.selectbox("Pilih Sampling untuk Ditampilkan:", [f"Sampling #{i}" for i in range(1, 6)])
        run_idx_raw = int(sel_raw_run.split("#")[1]) - 1
        st.code(current_samples[run_idx_raw], language="markdown")

    st.markdown("---")

    # FITUR EKSPOR
    st.markdown("#### 📥 Unduh Laporan Automated AI Testing & Audit (5-Time Sampling)")
    col_x1, col_x2, col_x3 = st.columns(3)

    csv_data = export_audit_to_csv(gap_data_5x["matrix_rows"])
    json_data = export_audit_to_json(cur_brand_name, st.session_state.get("website_url", ""), gap_data_5x, citations_5x, sim_5x_records)

    with col_x1:
        st.download_button(
            label="📊 Unduh Laporan (CSV / Excel)",
            data=csv_data,
            file_name=f"AI_Audit_5xSampling_{cur_brand_name.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_x2:
        st.download_button(
            label="📦 Unduh Laporan (JSON)",
            data=json_data,
            file_name=f"AI_Audit_5xSampling_{cur_brand_name.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True
        )

    with col_x3:
        md_summary = f"""# LAPORAN 5-TIME SAMPLING AI TESTING & AUDIT
Merek: {cur_brand_name}
Alias: {cur_aliases_input}
Tanggal: {datetime.now().strftime('%d %B %Y')}

## 1. HASIL SKOR PROBABILITAS
- Skor Probabilitas Sitasi: {prob_score}% ({found_runs}/5 Run Ditemukan)
- Kategori Konsistensi: {tier_badge}
- Deskripsi: {tier_desc}

## 2. RINCIAN 5-TIME SAMPLING
"""
        for r in audit_data["run_records"]:
            md_summary += f"- Sampling #{r['run_index']}: {r['status_icon']} | Istilah: {r['matched_term']} | Posisi: {r['position']} | Sebutan: {r['match_count']}x\n"

        st.download_button(
            label="📄 Unduh Ringkasan (Markdown)",
            data=md_summary,
            file_name=f"AI_Audit_Summary_{cur_brand_name.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )


# ==============================================================================
# TAB 4: FITUR UNGGULAN: AUTO-FIX GENERATOR
# ==============================================================================
with tab_autofix:
    st.markdown("### ⚡ Auto-Fix Generator Instan")
    st.write(
        "Modul ini memproduksi kode dan konten terstruktur siap pakai yang disesuaikan secara otomatis "
        "dengan data UMKM Anda di sidebar. Salin langsung ke website Anda untuk menutup celah kesenjangan kutipan!"
    )

    gen_tab1, gen_tab2, gen_tab3, gen_tab4 = st.tabs([
        "🏷️ Schema JSON-LD Generator",
        "📝 Draf Teks BLUF",
        "🤖 AI robots.txt",
        "💬 Conversational FAQ Generator"
    ])

    # 1. Schema JSON-LD Generator
    with gen_tab1:
        st.markdown("#### Generator Schema.org JSON-LD Valid")
        st.caption("Pilih jenis Schema yang ingin dipasang ke website Anda:")
        
        schema_type = st.radio(
            "Pilih Jenis Schema:",
            ["LocalBusiness / Organization (Identitas Brand)", "FAQPage (Pertanyaan Calon Konsumen)", "Product (Detail Produk & Harga)"],
            horizontal=True
        )

        if "LocalBusiness" in schema_type:
            code_result = generate_organization_schema(
                brand_name=st.session_state["brand_name"],
                url=st.session_state["website_url"],
                category=st.session_state["business_category"],
                phone=st.session_state["phone_number"],
                location=st.session_state["location_info"]
            )
            st.info("📌 **Cara Pasang:** Salin kode di bawah ini dan letakkan di dalam tag `<head> ... </head>` atau di pengaturan Header Script website/WordPress/Shopify Anda.")
        elif "FAQPage" in schema_type:
            code_result = generate_faq_schema(
                brand_name=st.session_state["brand_name"],
                category=st.session_state["business_category"],
                location=st.session_state["location_info"]
            )
            st.info("📌 **Cara Pasang:** Letakkan kode FAQPage ini di halaman utama (Home) atau di halaman /faq Anda.")
        else:
            code_result = generate_product_schema(
                brand_name=st.session_state["brand_name"],
                url=st.session_state["website_url"],
                product_name=st.session_state["product_name"],
                price_val=st.session_state["price_range"],
                description=st.session_state["key_advantages"],
                category=st.session_state["business_category"]
            )
            st.info("📌 **Cara Pasang:** Letakkan kode Product ini di halaman katalog atau landing page produk utama Anda.")

        st.code(code_result, language="html")

        st.download_button(
            label="💾 Unduh Kode Schema (.html / .json)",
            data=code_result,
            file_name=f"schema_{st.session_state['brand_name'].lower().replace(' ', '_')}.html",
            mime="text/html"
        )

    # 2. Draf Teks BLUF
    with gen_tab2:
        st.markdown("#### Generator Draf Paragraf BLUF (Bottom Line Up Front)")
        st.write(
            "AI crawler mengekstrak chunk teks pertama di sebuah halaman web. Format **BLUF** memastikan dalam "
            "50 kata pertama, pembaca dan bot AI langsung mengetahui siapa Anda, apa produk Anda, apa keunggulannya, berapa harganya, dan ke mana harus menghubungi."
        )

        bluf_code = generate_bluf_draft(
            brand_name=st.session_state["brand_name"],
            category=st.session_state["business_category"],
            product_name=st.session_state["product_name"],
            price_range=st.session_state["price_range"],
            key_advantages=st.session_state["key_advantages"],
            location=st.session_state["location_info"],
            phone=st.session_state["phone_number"]
        )

        st.markdown("##### Preview Tampilan Konten BLUF:")
        st.markdown(f"""
        > **{st.session_state['brand_name']}** adalah produsen dan penyedia **{st.session_state['business_category']}** terkemuka asal **{st.session_state['location_info']}**, yang menghadirkan **{st.session_state['product_name']}** berkualitas tinggi dengan *{st.session_state['key_advantages']}*. Seluruh produk dapat dipesan secara langsung dengan harga mulai dari **{st.session_state['price_range']}**, didukung jaminan pengiriman cepat ke seluruh Indonesia dan layanan konsultasi ramah via WhatsApp di **{st.session_state['phone_number']}**.
        >
        > - **Kategori & Spesialisasi:** {st.session_state['business_category']} ({st.session_state['product_name']})
        > - **Standar Kualitas & Keunggulan:** {st.session_state['key_advantages']}
        > - **Transparansi Harga:** {st.session_state['price_range']} (Tanpa biaya tersembunyi)
        > - **Pusat Operasional:** {st.session_state['location_info']}
        > - **Kanal Pemesanan Cepat:** WhatsApp {st.session_state['phone_number']}
        """)

        st.markdown("##### Kode HTML / Markdown Siap Copas:")
        st.code(bluf_code, language="html")

    # 3. AI robots.txt Generator
    with gen_tab3:
        st.markdown("#### Generator robots.txt Ramah Crawler AI")
        st.write(
            "Banyak pemilik website secara tidak sengaja memblokir bot AI atau menggunakan template default "
            "yang belum mengizinkan GPTBot, ClaudeBot, dan PerplexityBot. Gunakan konfigurasi ini di root domain Anda."
        )
        robots_text = generate_robots_txt()
        st.code(robots_text, language="plaintext")

        st.download_button(
            label="💾 Unduh File robots.txt",
            data=robots_text,
            file_name="robots.txt",
            mime="text/plain",
            help="Simpan dan unggah file ini ke root directory public_html hosting Anda."
        )

    # 4. Conversational FAQ Generator
    with gen_tab4:
        st.markdown("#### Generator 5 FAQ Percakapan Teroptimasi RAG")
        st.write(
            "Pertanyaan calon konsumen ke ChatGPT atau Perplexity bersifat percakapan (*conversational*). "
            "Berikut 5 pertanyaan dan jawaban yang siap Anda salin ke bagian bawah landing page Anda:"
        )

        faq_items = generate_conversational_faqs(
            brand_name=st.session_state["brand_name"],
            category=st.session_state["business_category"],
            product_name=st.session_state["product_name"],
            price_range=st.session_state["price_range"],
            location=st.session_state["location_info"]
        )

        for f in faq_items:
            with st.expander(f"❓ {f['q']}", expanded=True):
                st.write(f"💡 **Jawaban Optimal AI:** {f['a']}")

        # Format markdown siap salin
        faq_md_export = "## Pertanyaan yang Sering Diajukan (FAQ)\n\n"
        for f in faq_items:
            faq_md_export += f"### {f['q']}\n{f['a']}\n\n"

        st.download_button(
            label="💾 Unduh Seluruh FAQ (.md)",
            data=faq_md_export,
            file_name=f"FAQ_{st.session_state['brand_name'].replace(' ', '_')}.md",
            mime="text/markdown"
        )


# ==============================================================================
# TAB 4: PANDUAN EDUKASI GEO NUSANTARA
# ==============================================================================
with tab_guide:
    st.markdown("### 📖 Panduan Lengkap GEO (Generative Engine Optimization) untuk UMKM")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("""
        #### 🔄 Apa Perbedaan SEO Tradisional vs GEO?
        
        | Aspek | SEO Tradisional (Google 2010-2023) | GEO (Generative Engine Optimization 2024+) |
        | :--- | :--- | :--- |
        | **Target Mesin** | Algoritma perayap kata kunci (Keyword Rank) | Model Bahasa Besar RAG (ChatGPT, Perplexity, Gemini) |
        | **Tujuan Akhir** | Mendapat Klik & Ranking 1 di 10 tautan biru | Menjadi **Sumber Jawaban yang Disitasi & Direkomendasikan** |
        | **Format Konten** | Artikel panjang 2000 kata dengan keyword density | Format **BLUF**, angka kuantitatif, dan chunk modular |
        | **Identitas Mesin** | Backlink anchor text | **Schema JSON-LD** & Konsensus Entitas Multi-sumber |
        | **Dampak AI** | Pengunjung berkurang karena AI Overviews | Pengunjung langsung yang memiliki **intensitas beli tinggi** |
        """)

    with col_g2:
        st.markdown("""
        #### ⚙️ Bagaimana Cara Kerja AI RAG Saat Merekomendasikan Merek?
        
        1. **Query Masuk**: Pengguna bertanya ke AI: *"Rekomendasikan kopi lokal aromatik dari Sulawesi untuk oleh-oleh yang harganya di bawah 150 ribu."*
        2. **Retrieval**: AI mencari informasi di web secara real-time via search index bot (GPTBot / PerplexityBot).
        3. **Semantic Chunking**: AI membaca potongan teks berformat BLUF yang memiliki heading jelas dan angka kuantitatif.
        4. **Grounding & Entity Validation**: AI mengecek Schema JSON-LD dan ulasan di Google Business Profile untuk memverifikasi keaslian bisnis.
        5. **Sintesis & Sitasi**: AI menyusun jawaban: *"Salah satu pilihan unggulan adalah **Kopi Toraja Baji** asal Makale, dengan harga Rp 85.000..."* lengkap dengan tautan sumber ke situs Anda!
        """)

    st.markdown("---")
    
    # Panduan Dinamis Sesuai Kategori UMKM
    cur_cat = st.session_state.get("business_category", "Kuliner & Minuman")
    niche_tips = {
        "Kuliner & Minuman": [
            "Wajib mencantumkan nomor sertifikasi Halal dan izin edar BPOM / P-IRT di bagian paling atas halaman.",
            "Deskripsikan profil rasa dengan data kuantitatif spesifik (misal: 'Tingkat keasaman 2/5, 100% Arabika, masa simpan 6 bulan').",
            "Pastikan Google Business Profile memiliki foto tempat usaha dan 15+ ulasan autentik untuk grounding lokal."
        ],
        "Fashion & Tekstil": [
            "Sertakan komposisi bahan terukur (misal: '100% Katun Combed 24s gramasi 180-190 gsm').",
            "Sediakan tabel panduan ukuran (size chart) dalam satuan sentimeter (cm) yang rapi untuk mempermudah AI menjawab pertanyaan ukuran pembeli.",
            "Unggah video YouTube berdurasi singkat yang memperlihatkan fitting dan tekstur jahitan kain."
        ],
        "Kriya & Kerajinan Tangan": [
            "Jelaskan asal daerah pengrajin untuk memperkuat nilai keaslian entitas kultural (cultural entity grounding).",
            "Cantumkan dimensi fisik (P x L x T dalam cm) dan bobot gramasi untuk kalkulasi ongkos kirim AI.",
            "Sertakan jaminan kemasan aman dan garansi penggantian barang pecah belah."
        ],
        "Jasa Profesional & Konsultan": [
            "Tampilkan kredensial resmi, nomor registrasi asosiasi profesi, dan tautan profil LinkedIn terverifikasi.",
            "Gunakan format BLUF untuk menjelaskan lingkup konsultasi, durasi pengerjaan, dan estimasi biaya di paragraf awal.",
            "Sediakan tombol panggilan konsultasi atau WhatsApp 1-on-1 langsung."
        ],
        "Pertanian & Agribisnis": [
            "Cantumkan sertifikasi organik, kadar air %, dan varietas komoditas unggulan.",
            "Tampilkan cerita keterlibatan kelompok tani lokal (Direct Trade) untuk memenuhi kriteria relevansi sosial AI.",
            "Sediakan perbandingan harga eceran vs partai besar/kontrak pasokan rutin."
        ],
        "Pariwisata & Perhotelan": [
            "Cantumkan jarak tempuh presisi ke destinasi terdekat dan alamat lengkap standar NAP.",
            "Buat daftar fasilitas kamar/paket dalam format bullet yang jelas dan transparan.",
            "Tautkan ulasan video tur akomodasi di YouTube."
        ],
        "Kecantikan & Perawatan Diri": [
            "Wajib mencantumkan nomor notifikasi BPOM resmi untuk lolos kurasi keselamatan AI.",
            "Sebutkan kecocokan jenis kulit (misal: 'Aman untuk kulit berjerawat dan sensitif').",
            "Lengkapi dengan testimoni klinis atau uji kepuasan pengguna dengan persentase angka."
        ],
        "Herbal & Kesehatan": [
            "Cantumkan nomor registrasi BPOM TR (Obat Tradisional) dan sertifikasi Halal.",
            "Sebutkan persentase bahan alami dan petunjuk dosis harian yang jelas.",
            "Sediakan FAQ terkait kontraindikasi dan garansi keaslian bahan."
        ],
        "Teknologi & Digital": [
            "Tampilkan tabel perbandingan fitur paket berlangganan dengan harga transparan.",
            "Gunakan Schema SoftwareApplication untuk penegasan entitas produk digital.",
            "Jelaskan standar keamanan enkripsi data dan SLA ketersediaan server."
        ]
    }
    cat_points = niche_tips.get(cur_cat, niche_tips["Kuliner & Minuman"])

    st.markdown(f"""
    <div style="background: #f0fdf4; border-left: 4px solid #059669; border-radius: 0 12px 12px 0; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong style="color: #065f46; font-size: 1.05rem;">🎯 Strategi Khusus GEO untuk Kategori: {cur_cat}</strong>
            <span style="background: #059669; color: white; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">DISESUAIKAN DARI INPUT</span>
        </div>
        <ul style="margin-left: 1.25rem; color: #1e293b; font-size: 0.9rem; line-height: 1.7;">
            {''.join([f'<li style="margin-bottom: 0.3rem;">{pt}</li>' for pt in cat_points])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    #### 💡 Kamus Istilah Kunci GEO:
    - **BLUF (Bottom Line Up Front)**: Praktik menuliskan poin terpenting, kesimpulan, spesifikasi, dan harga pada paragraf terdepan sebelum detail pendukung.
    - **RAG (Retrieval-Augmented Generation)**: Teknologi AI di mana model bahasa mengambil data langsung dari internet untuk melengkapi pengetahuannya sebelum menjawab pengguna.
    - **Schema JSON-LD**: Format bahasa mesin standar dunia (Schema.org) yang menjelaskan data bisnis secara terstruktur tanpa bias kata.
    - **NAP Consistency (Name, Address, Phone)**: Kesamaan penulisan Nama, Alamat, dan Nomor Telepon di seluruh platform digital.
    - **Citation Gap**: Celah informasi yang membuat mesin AI enggan mencantumkan tautan ke website Anda.
    """)

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1rem 0;">
    <strong>GEO Audit App Nusantara</strong> &mdash; Inisiatif Kesiapan AI untuk UMKM Indonesia Naik Kelas.<br/>
    Dirancang berbasis prinsip <em>Generative Engine Optimization</em> &bull; Dibangun dengan Python &amp; Streamlit.
</div>
""", unsafe_allow_html=True)
