"""
GEO Audit App Nusantara
Aplikasi Web Interaktif Audit Kesiapan Generative Engine Optimization (GEO) untuk UMKM Indonesia.
"""

import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import modul internal dengan safe fallback untuk kelancaran deployment Streamlit Cloud
try:
    from geo_engine import (
        GEO_PILLARS,
        calculate_geo_score,
        analyze_citation_gaps,
        get_prioritized_recommendations,
        analyze_inputs_to_indicators,
        analyze_revenue_impact_and_weaknesses,
        normalize_answers,
        live_crawl_website
    )
except (ImportError, AttributeError):
    import geo_engine
    GEO_PILLARS = getattr(geo_engine, "GEO_PILLARS", {})
    _calc_geo_orig = getattr(geo_engine, "calculate_geo_score", None)
    def calculate_geo_score(current_answers=None, sampling_data=None, answers=None, *args, **kwargs):
        ans = current_answers if current_answers is not None else answers
        if ans is None and args:
            ans = args[0]
        if ans is None:
            ans = kwargs.get("current_answers", kwargs.get("answers", {}))
        if not isinstance(ans, dict):
            ans = {}
        if _calc_geo_orig is not None:
            try:
                return _calc_geo_orig(current_answers=ans, sampling_data=sampling_data)
            except TypeError:
                try:
                    return _calc_geo_orig(ans, sampling_data=sampling_data)
                except TypeError:
                    try:
                        return _calc_geo_orig(ans)
                    except TypeError:
                        pass
        p1 = 30.0 if ans.get("schema_org", False) or ans.get("tech_robots_llmstxt", False) else 0.0
        p2 = float(sampling_data.get("probability_score", 0.0)) * 0.4 if (sampling_data and "probability_score" in sampling_data) else (20.0 if ans.get("brand_identity", False) else 0.0)
        p3 = 30.0 if ans.get("citation_official_domain", False) else 0.0
        tot = round(min(p1 + p2 + p3, 100.0), 1)
        return {
            "total_score": tot,
            "tier_key": "ai_ready" if tot >= 80 else ("needs_optimization" if tot >= 50 else "invisible"),
            "tier_name": "AI-Ready (Sangat Siap)" if tot >= 80 else ("Needs Optimization (Cukup Siap)" if tot >= 50 else "Invisible to AI (Belum Siap)"),
            "tier_color": "#10B981" if tot >= 80 else ("#F59E0B" if tot >= 50 else "#EF4444"),
            "tier_badge": "🟢" if tot >= 80 else ("🟡" if tot >= 50 else "🔴"),
            "tier_description": f"Skor GEO saat ini: {tot}/100.",
            "pillar_results": {
                "pilar_1": {"title": "Crawlability & Machine-Readability", "icon": "🤖", "weight": 0.3, "weight_pct": 30, "checked_count": 1 if p1 > 0 else 0, "total_count": 2, "percentage": round(p1 / 0.3, 1), "earned_score": p1, "max_score": 30.0},
                "pilar_2": {"title": "Share of Model / AI Visibility", "icon": "🔍", "weight": 0.4, "weight_pct": 40, "checked_count": 1 if p2 > 0 else 0, "total_count": 2, "percentage": round(p2 / 0.4, 1), "earned_score": p2, "max_score": 40.0},
                "pilar_3": {"title": "Grounding & Citations", "icon": "🌐", "weight": 0.3, "weight_pct": 30, "checked_count": 1 if p3 > 0 else 0, "total_count": 2, "percentage": round(p3 / 0.3, 1), "earned_score": p3, "max_score": 30.0}
            }
        }
    analyze_citation_gaps = getattr(geo_engine, "analyze_citation_gaps", lambda a: [])
    get_prioritized_recommendations = getattr(geo_engine, "get_prioritized_recommendations", lambda a: {"quick_wins": [], "strategic": []})
    analyze_inputs_to_indicators = getattr(geo_engine, "analyze_inputs_to_indicators", None)
    live_crawl_website = getattr(geo_engine, "live_crawl_website", None)
    normalize_answers = getattr(geo_engine, "normalize_answers", lambda ans: ans)

    def analyze_revenue_impact_and_weaknesses(
        brand_name: str,
        category: str,
        product_name: str,
        location: str,
        answers: dict,
        sampling_audit: dict = None,
        competitors: list = None
    ):
        b_name = brand_name.strip() or "Merek Anda"
        cat = category.strip() or "Produk & Layanan"
        prod = product_name.strip() or f"Produk Unggulan {b_name}"
        loc = location.strip() or "Indonesia"
        comps = competitors or ["Kompetitor Utama"]
        main_comp = comps[0] if comps else "Kompetitor Pasar"
        norm_answers = normalize_answers(answers)
        specific_weaknesses = []

        if not norm_answers.get("schema_org", False):
            specific_weaknesses.append({
                "code": "missing_schema",
                "category": "Data Terstruktur",
                "title": "Ketiadaan Schema.org JSON-LD (Product & LocalBusiness)",
                "impact": "Kritis",
                "impact_color": "#EF4444",
                "explanation": f"AI tidak dapat membaca entitas bisnis atau harga secara terstruktur. AI memilih merujuk katalog {main_comp}.",
                "solution": "Salin kode Schema Product & LocalBusiness dari tab Auto-Fix Generator ke tag <head> web Anda."
            })
        if not norm_answers.get("tech_robots_llmstxt", False):
            specific_weaknesses.append({
                "code": "missing_llmstxt",
                "category": "Aksesibilitas Mesin",
                "title": "Ketiadaan Berkas llms.txt & Potensi Pemblokiran Bot AI",
                "impact": "Tinggi",
                "impact_color": "#F59E0B",
                "explanation": "Crawler AI (GPTBot, ClaudeBot, PerplexityBot) tidak memiliki dokumen ringkasan machine-readable resmi.",
                "solution": "Unggah berkas /llms.txt standar di root domain dan pastikan robots.txt mengizinkan bot AI."
            })
        if not norm_answers.get("content_metadata_og", False):
            specific_weaknesses.append({
                "code": "missing_bluf_og",
                "category": "Struktur Konten",
                "title": "Format Proposisi Nilai Belum Menerapkan BLUF",
                "impact": "Tinggi",
                "impact_color": "#EF4444",
                "explanation": "Proposisi nilai terkubur di bagian tengah halaman web.",
                "solution": "Letakkan ringkasan 50 kata pertama (BLUF) berisi nama merek, keunggulan, dan harga di bagian paling atas."
            })
        if not norm_answers.get("citation_multi_source", False):
            specific_weaknesses.append({
                "code": "low_grounding",
                "category": "Otoritas & Grounding",
                "title": "Minimnya Jejak Konsensus Pihak Ketiga (Off-Page Grounding)",
                "impact": "Sedang",
                "impact_color": "#F59E0B",
                "explanation": f"AI melakukan validasi silang data di internet. Merek {b_name} membutuhkan konsensus ulasan di {loc}.",
                "solution": f"Lengkapi Google Business Profile di {loc} dan minta 15+ ulasan autentik."
            })

        prob_score = sampling_audit.get("probability_score", 0.0) if sampling_audit else (
            80.0 if norm_answers.get("ai_high_intent_visibility") else 20.0
        )
        high_intent_mentioned = prob_score >= 60.0
        exploratory_mentioned = prob_score >= 40.0

        return {
            "brand_name": b_name,
            "category": cat,
            "main_competitor": main_comp,
            "specific_weaknesses": specific_weaknesses,
            "intent_breakdown": {
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
            },
            "priority_action_steps": [
                {
                    "priority": "1. Quick Win",
                    "timeframe": "< 1 Hari",
                    "badge_color": "#10B981",
                    "title": "Salin Schema JSON-LD & Terapkan Format BLUF",
                    "description": "Salin kode Schema LocalBusiness dan Product serta draf BLUF ke halaman website Anda.",
                    "expected_impact": "Mencegah kesalahan halusinasi harga dan membuat AI membaca entitas bisnis secara instan."
                },
                {
                    "priority": "2. Medium-Term",
                    "timeframe": "1 - 2 Minggu",
                    "badge_color": "#3B82F6",
                    "title": "Terbitkan Berkas /llms.txt & Conversational FAQ",
                    "description": f"Buat berkas /llms.txt di root domain dan tambahkan FAQ percakapan {prod}.",
                    "expected_impact": "Meningkatkan vector similarity saat pengguna bertanya dalam bahasa alami."
                },
                {
                    "priority": "3. Strategic / Digital PR",
                    "timeframe": "2 - 4 Minggu",
                    "badge_color": "#8B5CF6",
                    "title": "Bangun Grounding Konsensus Eksternal & GBP",
                    "description": f"Verifikasi Google Business Profile di {loc} dan dapatkan ulasan autentik.",
                    "expected_impact": "Memperkuat skor grounding multi-sumber sehingga AI merekomendasikan brand Anda di atas kompetitor."
                }
            ]
        }

try:
    from autofix_generators import (
        generate_organization_schema,
        generate_faq_schema,
        generate_product_schema,
        generate_bluf_draft,
        generate_robots_txt,
        generate_conversational_faqs,
        generate_llms_txt,
        generate_open_graph_meta
    )
except (ImportError, AttributeError):
    import autofix_generators
    generate_organization_schema = getattr(autofix_generators, "generate_organization_schema", None)
    generate_faq_schema = getattr(autofix_generators, "generate_faq_schema", None)
    generate_product_schema = getattr(autofix_generators, "generate_product_schema", None)
    generate_bluf_draft = getattr(autofix_generators, "generate_bluf_draft", None)
    generate_robots_txt = getattr(autofix_generators, "generate_robots_txt", None)
    generate_conversational_faqs = getattr(autofix_generators, "generate_conversational_faqs", None)
    generate_llms_txt = getattr(autofix_generators, "generate_llms_txt", lambda *args, **kwargs: "# llms.txt")
    generate_open_graph_meta = getattr(autofix_generators, "generate_open_graph_meta", lambda *args, **kwargs: "<!-- Open Graph -->")

try:
    from ai_testing_engine import (
        AI_ENGINES,
        CITATION_CATEGORIES,
        get_default_competitors_by_category,
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
except (ImportError, AttributeError):
    import ai_testing_engine
    AI_ENGINES = getattr(ai_testing_engine, "AI_ENGINES", {})
    CITATION_CATEGORIES = getattr(ai_testing_engine, "CITATION_CATEGORIES", {})
    get_default_competitors_by_category = getattr(ai_testing_engine, "get_default_competitors_by_category", lambda cat, loc: ["Kompetitor A", "Kompetitor B"])
    build_benchmark_queries = getattr(ai_testing_engine, "build_benchmark_queries", None)
    detect_brand_mentions = getattr(ai_testing_engine, "detect_brand_mentions", None)
    detect_brand_mentions_strict = getattr(ai_testing_engine, "detect_brand_mentions_strict", None)
    run_5x_sampling_audit = getattr(ai_testing_engine, "run_5x_sampling_audit", None)
    generate_5x_simulated_rag_responses = getattr(ai_testing_engine, "generate_5x_simulated_rag_responses", None)
    fetch_live_ai_completion_5x = getattr(ai_testing_engine, "fetch_live_ai_completion_5x", None)
    extract_and_categorize_citations = getattr(ai_testing_engine, "extract_and_categorize_citations", None)
    analyze_citation_gap_matrix = getattr(ai_testing_engine, "analyze_citation_gap_matrix", None)
    generate_simulated_ai_response = getattr(ai_testing_engine, "generate_simulated_ai_response", None)
    run_full_simulation_benchmark = getattr(ai_testing_engine, "run_full_simulation_benchmark", None)
    fetch_live_ai_completion = getattr(ai_testing_engine, "fetch_live_ai_completion", None)
    export_audit_to_json = getattr(ai_testing_engine, "export_audit_to_json", None)
    export_audit_to_csv = getattr(ai_testing_engine, "export_audit_to_csv", None)

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
# INISIALISASI SESSION STATE (BERSIH / TANPA DUMMY PRESET SAAT AWAL)
# ==============================================================================
if "brand_name" not in st.session_state:
    st.session_state["brand_name"] = ""
if "website_url" not in st.session_state:
    st.session_state["website_url"] = ""
if "business_category" not in st.session_state:
    st.session_state["business_category"] = "Pertanian & Agribisnis"
if "phone_number" not in st.session_state:
    st.session_state["phone_number"] = ""
if "location_info" not in st.session_state:
    st.session_state["location_info"] = ""
if "product_name" not in st.session_state:
    st.session_state["product_name"] = ""
if "price_range" not in st.session_state:
    st.session_state["price_range"] = ""
if "key_advantages" not in st.session_state:
    st.session_state["key_advantages"] = ""

# State untuk Indikator 3 Pilar GEO Riil (Default False / Bersih)
DEFAULT_CHECKS = {
    # Pilar 1: Crawlability & Machine-Readability (30%)
    "schema_org": False,
    "content_metadata_og": False,
    "tech_robots_llmstxt": False,
    # Pilar 2: Share of Model / AI Visibility (40%)
    "ai_high_intent_visibility": False,
    "ai_exploratory_visibility": False,
    # Pilar 3: Grounding & Citations (30%)
    "citation_official_domain": False,
    "citation_multi_source": False,
    # Indikator Kompatibilitas / Legacy Crawler
    "tech_robots": False,
    "tech_https_speed": False,
    "content_bluf": False,
    "content_headings": False,
    "content_faq": False,
    "content_data": False,
    "schema_product_faq": False,
    "offpage_youtube": False,
    "offpage_mentions": False,
}

for k, v in DEFAULT_CHECKS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# State untuk Modul AI Testing & Audit
if "brand_aliases" not in st.session_state:
    st.session_state["brand_aliases"] = ""
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
    st.session_state["ai_test_competitors"] = ""
if "ai_test_5x_prompt" not in st.session_state:
    st.session_state["ai_test_5x_prompt"] = ""
if "ai_test_5x_responses" not in st.session_state:
    st.session_state["ai_test_5x_responses"] = None
if "ai_test_5x_scenario" not in st.session_state:
    st.session_state["ai_test_5x_scenario"] = "🟢 AI-Ready (4-5 dari 5 Run Ditemukan)"
if "ai_test_5x_audit" not in st.session_state:
    st.session_state["ai_test_5x_audit"] = None


def reset_checklist_only():
    """
    Mengosongkan HANYA checklist indikator audit ke False.
    TIDAK menghapus data input form (brand, url, kategori, lokasi, dll)
    serta hasil kalkulasi skor / audit 5x yang sudah tersimpan.
    """
    for k in DEFAULT_CHECKS.keys():
        st.session_state[k] = False

    for p_val in GEO_PILLARS.values():
        for ind in p_val["indicators"]:
            st.session_state[ind["id"]] = False
            widget_key = f"chk_{ind['id']}"
            if widget_key in st.session_state:
                st.session_state[widget_key] = False

    for key in list(st.session_state.keys()):
        if key.startswith("checklist_") or key.startswith("chk_"):
            st.session_state[key] = False

    if "last_analysis_summary" in st.session_state:
        del st.session_state["last_analysis_summary"]
    if "last_live_crawl" in st.session_state:
        del st.session_state["last_live_crawl"]


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

                # 2. Live Web Crawl (Server TTFB, HTTPS SSL, robots.txt untuk 4 AI Bots & llms.txt)
                crawl_res = live_crawl_website(target_site)
                if crawl_res["success"]:
                    st.session_state["tech_robots"] = crawl_res["tech_robots_passed"]
                    st.session_state["tech_https_speed"] = crawl_res["tech_https_speed_passed"]
                    st.session_state["tech_robots_llmstxt"] = crawl_res.get("tech_robots_passed", False) or crawl_res.get("llms_txt_found", False)
                    if crawl_res.get("html_inspections", {}).get("has_schema_jsonld"):
                        st.session_state["schema_org"] = True
                        st.session_state["schema_product_faq"] = True
                    if crawl_res.get("html_inspections", {}).get("has_open_graph") or crawl_res.get("html_inspections", {}).get("has_headings"):
                        st.session_state["content_metadata_og"] = True
                        st.session_state["content_headings"] = True
                    st.session_state["last_live_crawl"] = crawl_res
                    st.toast("✅ Live Audit Web Selesai! Indikator GEO telah terisi otomatis.", icon="🌐")
                else:
                    st.sidebar.warning(f"⚠️ Live Crawl: {crawl_res.get('error_message')}")
                    st.toast("⚠️ Evaluasi selesai dengan data inputan lokal.", icon="⚠️")
                st.rerun()

    if st.button("🔄 Kosongkan Checklist", use_container_width=True, help="Kosongkan seluruh centang checklist audit tanpa mereset profil data UMKM"):
        reset_checklist_only()
        st.toast("Checklist berhasil dikosongkan. Data form tetap tersimpan.", icon="🔄")
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
# LOGIKA HITUNG SKOR SECARA REAL-TIME (3 PILAR RIIL & REVENUE IMPACT)
# ==============================================================================
current_answers = {k: st.session_state.get(k, False) for k in DEFAULT_CHECKS.keys()}
for p_val in GEO_PILLARS.values():
    for ind in p_val["indicators"]:
        if ind["id"] in st.session_state:
            current_answers[ind["id"]] = st.session_state[ind["id"]]

sampling_audit_state = st.session_state.get("ai_test_5x_audit")
try:
    score_data = calculate_geo_score(current_answers=current_answers, sampling_data=sampling_audit_state)
except TypeError:
    try:
        score_data = calculate_geo_score(current_answers, sampling_data=sampling_audit_state)
    except TypeError:
        try:
            score_data = calculate_geo_score(current_answers)
        except TypeError:
            score_data = calculate_geo_score(answers=current_answers)

if not isinstance(score_data, dict):
    score_data = {}

total_score = float(score_data.get("total_score", 0.0))
tier_badge = str(score_data.get("tier_badge", "🔴"))
tier_name = str(score_data.get("tier_name", "Invisible to AI (Belum Siap)"))
tier_color = str(score_data.get("tier_color", "#EF4444"))
tier_description = str(score_data.get("tier_description", "Audit GEO menunjukkan perlunya perbaikan fondasi visibilitas AI."))
pillar_results = score_data.get("pillar_results")
if not isinstance(pillar_results, dict):
    pillar_results = {}

for p_key, default_title, default_weight in [
    ("pilar_1", "Crawlability & Machine-Readability", 0.30),
    ("pilar_2", "Share of Model / AI Visibility", 0.40),
    ("pilar_3", "Grounding & Citations", 0.30)
]:
    if p_key not in pillar_results:
        pillar_results[p_key] = {
            "title": default_title,
            "icon": "🤖" if p_key == "pilar_1" else ("🔍" if p_key == "pilar_2" else "🌐"),
            "weight": default_weight,
            "weight_pct": int(default_weight * 100),
            "checked_count": 0,
            "total_count": 2,
            "percentage": 0.0,
            "earned_score": 0.0,
            "max_score": round(default_weight * 100, 1)
        }
score_data["total_score"] = total_score
score_data["tier_badge"] = tier_badge
score_data["tier_name"] = tier_name
score_data["tier_color"] = tier_color
score_data["tier_description"] = tier_description
score_data["pillar_results"] = pillar_results

citation_gaps = analyze_citation_gaps(current_answers)
recom_data = get_prioritized_recommendations(current_answers)

# Hitung Analisis Dampak Finansial & Deteksi Celah LLM (Revenue Impact)
active_comps = [c.strip() for c in st.session_state.get("ai_test_competitors", "").split(",") if c.strip()]
if not active_comps:
    active_comps = get_default_competitors_by_category(st.session_state.get("business_category", ""), st.session_state.get("location_info", ""))

revenue_analysis = analyze_revenue_impact_and_weaknesses(
    brand_name=st.session_state.get("brand_name", ""),
    category=st.session_state.get("business_category", ""),
    product_name=st.session_state.get("product_name", ""),
    location=st.session_state.get("location_info", ""),
    answers=current_answers,
    sampling_audit=sampling_audit_state,
    competitors=active_comps
)


# ==============================================================================
# 5 TAB UTAMA INTERFACE
# ==============================================================================
tab_audit, tab_dashboard, tab_testing, tab_autofix, tab_guide = st.tabs([
    "📋 1. Checklist Audit (3 Pilar Riil)",
    "📊 2. Dasbor Skor & Kesenjangan Kutipan",
    "🤖 3. Automated AI Testing & Audit",
    "⚡ 4. Auto-Fix Generator",
    "📖 5. Panduan Edukasi GEO"
])


# ==============================================================================
# TAB 1: CHECKLIST AUDIT (3 PILAR GEO RIIL)
# ==============================================================================
with tab_audit:
    st.markdown("### 📋 Evaluasi Kesiapan GEO (3 Pilar Riil)")
    st.write(
        "Centang setiap indikator di bawah ini yang sudah benar-benar diterapkan pada website dan kehadiran digital merek Anda. "
        "Skor dan analisis dampak finansial dihitung secara transparan dan instan."
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
        p_primary_ids = ["schema_org", "content_metadata_og", "tech_robots_llmstxt", "ai_high_intent_visibility", "ai_exploratory_visibility", "citation_official_domain", "citation_multi_source"]
        checked_total = sum(1 for ind_id in p_primary_ids if current_answers.get(ind_id, False))
        st.info(f"**Progres:** {checked_total} dari 7 indikator utama 3 pilar terpenuhi. Kategori status: **{tier_name}**")

    st.markdown("---")

    # KOTAK AKSI & HASIL LIVE WEB CRAWLER
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 1.2rem 1.4rem; margin-bottom: 1.2rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem;">
                        <span style="font-size: 1.2rem;">🌐</span>
                        <strong style="color: #0f172a; font-size: 1.05rem;">Live Crawler Otomatis: Fetch URL, robots.txt &amp; llms.txt AI</strong>
                        <span style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">REAL-TIME INSPECTION</span>
                    </div>
                    <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0; line-height: 1.5;">
                        Pindai langsung server website Anda secara real-time: Mendeteksi apakah <code>/robots.txt</code> mengizinkan <strong>GPTBot, ClaudeBot, Google-Extended, dan PerplexityBot</strong>, memeriksa keberadaan <code>/llms.txt</code>, serta memvalidasi Open Graph dan kecepatan respons (TTFB).
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            st.caption(f"Target URL: `{st.session_state.get('website_url') or '(Belum diisi)'}` (Ubah di sidebar jika ingin menguji domain lain)")
        with col_run2:
            if st.button("🚀 Jalankan Live Audit Web", type="primary", use_container_width=True, key="btn_run_live_tab1"):
                target_url = st.session_state.get("website_url", "").strip()
                if not target_url:
                    st.error("Silakan masukkan URL website di sidebar.")
                else:
                    with st.spinner(f"🔍 Menghubungi server live {target_url} dan memindai robots.txt & llms.txt..."):
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

                        crawl_res = live_crawl_website(target_url)
                        if crawl_res["success"]:
                            st.session_state["tech_robots"] = crawl_res["tech_robots_passed"]
                            st.session_state["tech_https_speed"] = crawl_res["tech_https_speed_passed"]
                            st.session_state["tech_robots_llmstxt"] = crawl_res.get("tech_robots_passed", False) or crawl_res.get("llms_txt_found", False)
                            if crawl_res.get("html_inspections", {}).get("has_schema_jsonld"):
                                st.session_state["schema_org"] = True
                                st.session_state["schema_product_faq"] = True
                            if crawl_res.get("html_inspections", {}).get("has_open_graph") or crawl_res.get("html_inspections", {}).get("has_headings"):
                                st.session_state["content_metadata_og"] = True
                                st.session_state["content_headings"] = True
                            st.session_state["last_live_crawl"] = crawl_res
                            st.toast("✅ Live Audit Berhasil! Indikator GEO telah terisi otomatis.", icon="🌐")
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
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700;">Protokol Enkripsi &amp; Open Graph</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: {'#059669' if crawl['https_active'] else '#dc2626'};">
                        🔒 {'HTTPS Aktif' if crawl['https_active'] else 'HTTP Tidak Aman'}
                    </div>
                    <div style="font-size: 0.75rem; color: #059669; font-weight: 600;">
                        {'✓ OG Tags Terdeteksi' if crawl.get('html_inspections', {}).get('has_open_graph') else '⚠️ OG Tags Belum Ada'}
                    </div>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem 1rem; border-radius: 10px;">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #64748b; font-weight: 700;">Berkas /llms.txt &amp; robots.txt</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">
                        📄 {'llms.txt Ada' if crawl.get('llms_txt_found') else 'llms.txt Belum Ada'}
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

    # Render 3 Pilar GEO Riil
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

            if p_key == "pilar_2" and sampling_audit_state:
                st.info(f"💡 Skor Pilar 2 tersinkronisasi presisi dari **5-Time Sampling AI**: Probabilitas **{sampling_audit_state['probability_score']}%** ({sampling_audit_state['found_count']}/5 Run)")

            # Checkbox per indikator
            for ind in p_val["indicators"]:
                ind_id = ind["id"]
                col_chk, col_exp = st.columns([4, 1])
                with col_chk:
                    is_checked = st.checkbox(
                        label=f"**{ind['label']}** (+{ind['weight_total']}%)",
                        value=st.session_state.get(ind_id, False),
                        key=f"chk_{ind_id}",
                        help=ind["help"]
                    )
                    # Sinkronkan ke session_state utama jika berubah
                    if is_checked != st.session_state.get(ind_id, False):
                        st.session_state[ind_id] = is_checked
                        st.rerun()

                    st.markdown(f"<span style='color: #64748b; font-size: 0.85rem; margin-left: 1.8rem; display: block;'>{ind['sublabel']}</span>", unsafe_allow_html=True)
                
                with col_exp:
                    if st.session_state.get(ind_id, False):
                        st.success("✅ Terpenuhi")
                    else:
                        st.warning("⚠️ Belum Ada")

            st.markdown("</div>", unsafe_allow_html=True)

    # ==============================================================================
    # MODUL REVENUE IMPACT & DETEKSI KELEMAHAN RETRIEVAL LLM
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 💰 Revenue Impact & LLM Retrieval Weakness Detection")
    st.caption("Diagnosis korelasi visibilitas AI dengan potensi kehilangan omzet calon pembeli (Buyer Intent) serta analisis titik lemah retrieval model bahasa.")

    # 1. Alert Box Potensi Kehilangan Omzet
    high_intent_data = revenue_analysis["intent_breakdown"]["high_intent"]
    if high_intent_data["has_lost_revenue"]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%); border: 2px solid #ef4444; border-radius: 14px; padding: 1.3rem 1.6rem; margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.08);">
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem;">⚠️</span>
                <strong style="color: #991b1b; font-size: 1.18rem;">POTENTIAL LOST REVENUE ALERT</strong>
                <span style="background: #ef4444; color: white; font-size: 0.72rem; font-weight: 800; padding: 3px 8px; border-radius: 6px;">HIGH-INTENT BUYER RISK</span>
            </div>
            <p style="color: #7f1d1d; font-size: 0.94rem; line-height: 1.6; margin-bottom: 0.4rem;">
                {high_intent_data['alert_description']}
            </p>
            <div style="font-size: 0.85rem; color: #b91c1c; font-weight: 600;">
                💡 <strong>Koreksi Segera:</strong> Lengkapi Schema Product dengan harga transparan dan unggah berkas <code>/llms.txt</code> agar AI merekomendasikan bisnis Anda di atas kompetitor.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border: 2px solid #10b981; border-radius: 14px; padding: 1.3rem 1.6rem; margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.08);">
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem;">
                <span style="font-size: 1.5rem;">✅</span>
                <strong style="color: #065f46; font-size: 1.18rem;">REVENUE OPPORTUNITY SECURED</strong>
                <span style="background: #10b981; color: white; font-size: 0.72rem; font-weight: 800; padding: 3px 8px; border-radius: 6px;">COMMERCIAL INTENT CONVERTED</span>
            </div>
            <p style="color: #047857; font-size: 0.94rem; line-height: 1.6; margin-bottom: 0.2rem;">
                {high_intent_data['alert_description']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 2. Klasifikasi Buyer Intent
    col_int1, col_int2 = st.columns(2)
    with col_int1:
        st.markdown(f"""
        <div style="background: white; border: 1.5px solid {'#10b981' if high_intent_data['is_mentioned'] else '#ef4444'}; border-radius: 12px; padding: 1.1rem 1.3rem; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: #0f172a; font-size: 1rem;">🎯 High-Intent (Siap Beli)</strong>
                <span style="font-size: 0.78rem; font-weight: 700;">{high_intent_data['status_label']}</span>
            </div>
            <p style="color: #64748b; font-size: 0.84rem; margin-bottom: 0.6rem;">{high_intent_data['intent_description']}</p>
            <div style="background: #f8fafc; border-left: 3px solid #3b82f6; padding: 0.6rem 0.8rem; border-radius: 0 6px 6px 0; font-size: 0.82rem; color: #1e293b; font-style: italic;">
                "{high_intent_data['query_example']}"
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_int2:
        exploratory_data = revenue_analysis["intent_breakdown"]["exploratory"]
        st.markdown(f"""
        <div style="background: white; border: 1.5px solid {'#10b981' if exploratory_data['is_mentioned'] else '#f59e0b'}; border-radius: 12px; padding: 1.1rem 1.3rem; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <strong style="color: #0f172a; font-size: 1rem;">🔍 Exploratory (Solusi &amp; Riset)</strong>
                <span style="font-size: 0.78rem; font-weight: 700;">{exploratory_data['status_label']}</span>
            </div>
            <p style="color: #64748b; font-size: 0.84rem; margin-bottom: 0.6rem;">{exploratory_data['intent_description']}</p>
            <div style="background: #f8fafc; border-left: 3px solid #8b5cf6; padding: 0.6rem 0.8rem; border-radius: 0 6px 6px 0; font-size: 0.82rem; color: #1e293b; font-style: italic;">
                "{exploratory_data['query_example']}"
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Deteksi Kelemahan Spesifik Retrieval LLM
    st.markdown("##### 🔬 Kelemahan Spesifik Retrieval Mesin AI yang Terdeteksi:")
    if not revenue_analysis["specific_weaknesses"]:
        st.success("🎉 Tidak terdeteksi kelemahan retrieval kritis pada profil website Anda!")
    else:
        for w in revenue_analysis["specific_weaknesses"]:
            st.markdown(f"""
            <div style="background: white; border-left: 4px solid {w['impact_color']}; border-radius: 0 10px 10px 0; padding: 0.9rem 1.2rem; margin-bottom: 0.7rem; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                    <strong style="color: #0f172a; font-size: 0.98rem;">{w['title']}</strong>
                    <span style="font-size: 0.72rem; font-weight: 800; background: {w['impact_color']}; color: white; padding: 2px 7px; border-radius: 4px;">Tingkat: {w['impact']}</span>
                </div>
                <p style="color: #475569; font-size: 0.86rem; margin-bottom: 0.4rem; line-height: 1.5;">{w['explanation']}</p>
                <div style="font-size: 0.83rem; color: #059669; font-weight: 600;">
                    🛠️ Solusi: {w['solution']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 4. Tiga Langkah Aksi Prioritas
    st.markdown("##### 🚀 3 Langkah Aksi Prioritas:")
    col_act1, col_act2, col_act3 = st.columns(3)
    actions = revenue_analysis["priority_action_steps"]
    with col_act1:
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 12px; padding: 1rem 1.1rem; height: 100%;">
            <span style="background: {actions[0]['badge_color']}; color: white; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 4px;">{actions[0]['priority']} ({actions[0]['timeframe']})</span>
            <h5 style="margin: 0.5rem 0 0.3rem 0; color: #064e3b; font-size: 0.95rem;">{actions[0]['title']}</h5>
            <p style="color: #14532d; font-size: 0.82rem; line-height: 1.5; margin-bottom: 0.4rem;">{actions[0]['description']}</p>
            <div style="font-size: 0.75rem; color: #047857; font-weight: 700;">📈 {actions[0]['expected_impact']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_act2:
        st.markdown(f"""
        <div style="background: #eff6ff; border: 1.5px solid #93c5fd; border-radius: 12px; padding: 1rem 1.1rem; height: 100%;">
            <span style="background: {actions[1]['badge_color']}; color: white; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 4px;">{actions[1]['priority']} ({actions[1]['timeframe']})</span>
            <h5 style="margin: 0.5rem 0 0.3rem 0; color: #1e3a8a; font-size: 0.95rem;">{actions[1]['title']}</h5>
            <p style="color: #1e40af; font-size: 0.82rem; line-height: 1.5; margin-bottom: 0.4rem;">{actions[1]['description']}</p>
            <div style="font-size: 0.75rem; color: #1d4ed8; font-weight: 700;">📈 {actions[1]['expected_impact']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_act3:
        st.markdown(f"""
        <div style="background: #faf5ff; border: 1.5px solid #d8b4fe; border-radius: 12px; padding: 1rem 1.1rem; height: 100%;">
            <span style="background: {actions[2]['badge_color']}; color: white; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 4px;">{actions[2]['priority']} ({actions[2]['timeframe']})</span>
            <h5 style="margin: 0.5rem 0 0.3rem 0; color: #581c87; font-size: 0.95rem;">{actions[2]['title']}</h5>
            <p style="color: #6b21a8; font-size: 0.82rem; line-height: 1.5; margin-bottom: 0.4rem;">{actions[2]['description']}</p>
            <div style="font-size: 0.75rem; color: #7e22ce; font-weight: 700;">📈 {actions[2]['expected_impact']}</div>
        </div>
        """, unsafe_allow_html=True)


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

    # Dua Grafik Plotly: Radar Chart & Bar Chart (3 Pilar)
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 🕸️ Radar Keseimbangan 3 Pilar GEO")
        # Data untuk Radar Chart 3 Pilar
        categories_radar = [
            "Crawlability & Readability (30%)",
            "Share of Model / AI Visibility (40%)",
            "Grounding & Citations (30%)"
        ]
        values_radar = [
            pillar_results["pilar_1"]["percentage"],
            pillar_results["pilar_2"]["percentage"],
            pillar_results["pilar_3"]["percentage"]
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
        pilar_names = ["Crawlability (30 pt)", "AI Visibility (40 pt)", "Grounding (30 pt)"]
        earned_vals = [pillar_results[p]["earned_score"] for p in ["pilar_1", "pilar_2", "pilar_3"]]
        max_vals = [pillar_results[p]["max_score"] for p in ["pilar_1", "pilar_2", "pilar_3"]]

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
            yaxis=dict(range=[0, 45], title="Poin Skor"),
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
        st.success("🎉 **Luar Biasa! Tidak Ditemukan Kesenjangan Kutipan yang Kritis.** Website dan merek Anda telah memenuhi indikator dasar GEO.")
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
- Nama Merek: {st.session_state['brand_name'] or 'Merek UMKM'}
- Website: {st.session_state['website_url'] or '-'}
- Kategori Bisnis: {st.session_state['business_category']}
- Lokasi: {st.session_state['location_info'] or '-'}
- WhatsApp: {st.session_state['phone_number'] or '-'}

## 2. HASIL SKOR AUDIT (3 PILAR RIIL)
- Total Skor GEO: {total_score} / 100
- Kategori Kematangan: {tier_badge} {tier_name}
- Deskripsi Status: {tier_description}

### Rincian Ketercapaian 3 Pilar:
1. Crawlability & Machine-Readability (30%): {pillar_results['pilar_1']['earned_score']} / {pillar_results['pilar_1']['max_score']} pt ({pillar_results['pilar_1']['percentage']}%)
2. Share of Model / AI Visibility (40%): {pillar_results['pilar_2']['earned_score']} / {pillar_results['pilar_2']['max_score']} pt ({pillar_results['pilar_2']['percentage']}%)
3. Grounding & Citations (30%): {pillar_results['pilar_3']['earned_score']} / {pillar_results['pilar_3']['max_score']} pt ({pillar_results['pilar_3']['percentage']}%)

## 3. DIAGNOSIS POTENSI KEHILANGAN OMZET & BUYER INTENT
- Kueri Siap Beli (High-Intent): {high_intent_data['status_label']}
- Kueri Eksplorasi: {revenue_analysis['intent_breakdown']['exploratory']['status_label']}
- Peringatan Finansial: {high_intent_data['alert_title']} - {high_intent_data['alert_description']}

## 4. KESENJANGAN KUTIPAN (CITATION GAPS)
"""
    for g in citation_gaps:
        report_markdown += f"- [{g['impact']}] {g['gap_title']}: {g['fix_summary']}\n"

    report_markdown += f"""
## 5. REKOMENDASI PRIORITAS
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
        file_name=f"GEO_Audit_{st.session_state['brand_name'].replace(' ', '_') if st.session_state['brand_name'] else 'UMKM'}.md",
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
            value=st.session_state.get("brand_name", ""),
            placeholder="Misal: CV Tani Organik Nusantara / Nama Merek Anda",
            key="ai_input_brand_name",
            help="Nama merek utama yang akan dicocokkan secara ketat dengan batas kata (\\b)."
        )
        if cur_brand_name != st.session_state.get("brand_name"):
            st.session_state["brand_name"] = cur_brand_name
            st.session_state["ai_test_5x_responses"] = None

    with col_inp2:
        default_alias_str = st.session_state.get("brand_aliases", "")
        if not default_alias_str and st.session_state.get("website_url"):
            clean_host = st.session_state.get("website_url", "").replace("https://","").replace("http://","").strip("/").split("/")[0]
            default_alias_str = f"{clean_host}, {cur_brand_name}" if cur_brand_name else clean_host
        cur_aliases_input = st.text_input(
            "Daftar Alias / Variasi Merek (pisahkan koma):",
            value=default_alias_str,
            placeholder="Domain website, akronim, variasi ejaan resmi",
            key="ai_input_brand_aliases",
            help="Domain website, akronim, variasi ejaan resmi, atau nama tanpa spasi yang juga sah dianggap sebagai sebutan merek Anda."
        )
        if cur_aliases_input != st.session_state.get("brand_aliases"):
            st.session_state["brand_aliases"] = cur_aliases_input
            st.session_state["ai_test_5x_responses"] = None

    # Parse daftar alias bersih
    active_aliases = [a.strip() for a in cur_aliases_input.split(",") if a.strip()]

    # 2. AREA TEKS KUERI PROMPT PENGUJIAN
    b_cat = st.session_state.get('business_category', 'Pertanian & Agribisnis')
    b_loc = st.session_state.get('location_info', 'Bandung, Jawa Barat').split(',')[0].strip() or 'Indonesia'
    default_prompt_text = f"Rekomendasikan {b_cat} terbaik dari {b_loc} yang berkualitas tinggi, terpercaya, dan siap dipesan sekarang."
    
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
            st.info("⚡ Masukkan API Key untuk melakukan 5 kali pemanggilan sekuensial secara langsung ke server OpenAI, Perplexity, atau Gemini.")
            col_ap1, col_ap2, col_ap3 = st.columns([1, 2, 1])
            with col_ap1:
                api_provider = st.selectbox(
                    "Provider API:",
                    ["OpenAI (ChatGPT)", "Perplexity AI", "Google Gemini (gemini-1.5-flash)"],
                    key="api_5x_provider"
                )
            with col_ap2:
                api_key_val = st.text_input("API Key:", type="password", value=st.session_state.get("ai_test_api_key", ""), key="api_5x_key_input")
                st.session_state["ai_test_api_key"] = api_key_val
            with col_ap3:
                if "Perplexity" in api_provider:
                    model_tag = "sonar"
                    p_code = "perplexity"
                elif "Gemini" in api_provider:
                    model_tag = "gemini-1.5-flash"
                    p_code = "gemini"
                else:
                    model_tag = "gpt-4o-mini"
                    p_code = "openai"
                st.caption(f"Model: `{model_tag}` (Temp: 0.7)")

            if st.button("🚀 Jalankan 5x Sampling Live via API", type="primary", use_container_width=True):
                if not api_key_val.strip():
                    st.error("Silakan masukkan API Key Anda.")
                else:
                    with st.spinner("Mengirimkan 5 kueri sekuensial ke server API..."):
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
    # Sinkronkan hasil audit_data ke session_state untuk menggerakkan Pilar 2 dan Revenue Impact
    st.session_state["ai_test_5x_audit"] = audit_data

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
        default_cat_comps = ", ".join(get_default_competitors_by_category(st.session_state.get("business_category", ""), st.session_state.get("location_info", "")))
        comp_val = st.session_state.get("ai_test_competitors") or default_cat_comps
        raw_comp_str = st.text_input(
            "Daftar Kompetitor Pembanding (pisahkan koma):",
            value=comp_val,
            key="ai_input_competitors_list",
            help="Daftar nama kompetitor di kategori bisnis yang sama untuk dihitung rasio sebutan dan Share of Voice (SOV)."
        )
        st.session_state["ai_test_competitors"] = raw_comp_str
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

    gen_tab1, gen_tab2, gen_tab3, gen_tab4, gen_tab5, gen_tab6 = st.tabs([
        "🏷️ Schema JSON-LD Generator",
        "📄 Berkas /llms.txt",
        "🌐 Open Graph & Social Meta",
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
            file_name=f"schema_{st.session_state['brand_name'].lower().replace(' ', '_') if st.session_state['brand_name'] else 'umkm'}.html",
            mime="text/html"
        )

    # 2. Berkas /llms.txt Machine-Readable Generator
    with gen_tab2:
        st.markdown("#### Generator Berkas /llms.txt Standar Machine-Readable")
        st.write(
            "Standar <code>/llms.txt</code> (menurut llmstxt.org) memberikan ringkasan padat dan terstruktur "
            "tentang identitas bisnis, produk, harga, dan URL rujukan resmi kepada bot AI crawler."
        )
        llms_text_code = generate_llms_txt(
            brand_name=st.session_state["brand_name"],
            category=st.session_state["business_category"],
            product_name=st.session_state["product_name"],
            price_range=st.session_state["price_range"],
            key_advantages=st.session_state["key_advantages"],
            location=st.session_state["location_info"],
            website_url=st.session_state["website_url"],
            phone=st.session_state["phone_number"]
        )
        st.code(llms_text_code, language="markdown")
        st.download_button(
            label="💾 Unduh Berkas llms.txt",
            data=llms_text_code,
            file_name="llms.txt",
            mime="text/markdown",
            help="Simpan dan unggah berkas ini ke direktori root (https://domain-anda.com/llms.txt)."
        )

    # 3. Open Graph & Social Meta Tags
    with gen_tab3:
        st.markdown("#### Generator Open Graph (OG Tags) & Twitter Cards")
        st.write(
            "Tag Open Graph memastikan judul entitas, deskripsi keunggulan, dan preview thumbnail "
            "terbaca dengan pasti oleh peramban dan crawler AI generatif."
        )
        og_code = generate_open_graph_meta(
            brand_name=st.session_state["brand_name"],
            product_name=st.session_state["product_name"],
            category=st.session_state["business_category"],
            website_url=st.session_state["website_url"],
            key_advantages=st.session_state["key_advantages"]
        )
        st.code(og_code, language="html")
        st.download_button(
            label="💾 Unduh Snippet Open Graph (.html)",
            data=og_code,
            file_name="meta_open_graph.html",
            mime="text/html",
            help="Tempelkan kode ini di dalam blok <head> halaman utama website Anda."
        )

    # 4. Draf Teks BLUF
    with gen_tab4:
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

        b_b = st.session_state.get('brand_name') or 'Brand Anda'
        b_c = st.session_state.get('business_category') or 'Kategori Produk'
        b_l = st.session_state.get('location_info') or 'Indonesia'
        b_p = st.session_state.get('product_name') or 'Produk Unggulan'
        b_adv = st.session_state.get('key_advantages') or 'Kualitas Terbaik'
        b_pr = st.session_state.get('price_range') or 'Harga Terjangkau'
        b_w = st.session_state.get('phone_number') or 'Kontak Resmi'

        st.markdown("##### Preview Tampilan Konten BLUF:")
        st.markdown(f"""
        > **{b_b}** adalah produsen dan penyedia **{b_c}** terkemuka asal **{b_l}**, yang menghadirkan **{b_p}** berkualitas tinggi dengan *{b_adv}*. Seluruh produk dapat dipesan secara langsung dengan harga mulai dari **{b_pr}**, didukung jaminan pengiriman cepat ke seluruh Indonesia dan layanan konsultasi ramah via WhatsApp di **{b_w}**.
        >
        > - **Kategori & Spesialisasi:** {b_c} ({b_p})
        > - **Standar Kualitas & Keunggulan:** {b_adv}
        > - **Transparansi Harga:** {b_pr} (Tanpa biaya tersembunyi)
        > - **Pusat Operasional:** {b_l}
        > - **Kanal Pemesanan Cepat:** WhatsApp {b_w}
        """)

        st.markdown("##### Kode HTML / Markdown Siap Copas:")
        st.code(bluf_code, language="html")

    # 5. AI robots.txt Generator
    with gen_tab5:
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

    # 6. Conversational FAQ Generator
    with gen_tab6:
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
            file_name=f"FAQ_{st.session_state['brand_name'].replace(' ', '_') if st.session_state['brand_name'] else 'UMKM'}.md",
            mime="text/markdown"
        )


# ==============================================================================
# TAB 5: PANDUAN EDUKASI GEO NUSANTARA
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
        guide_brand = st.session_state.get('brand_name') or 'Merek Anda'
        guide_cat = st.session_state.get('business_category') or 'produk'
        guide_loc = st.session_state.get('location_info') or 'Indonesia'
        guide_pr = st.session_state.get('price_range') or 'Rp 85.000'
        st.markdown(f"""
        #### ⚙️ Bagaimana Cara Kerja AI RAG Saat Merekomendasikan Merek?
        
        1. **Query Masuk**: Pengguna bertanya ke AI: *"Rekomendasikan {guide_cat} terbaik dari {guide_loc} yang berkualitas tinggi dan siap dipesan."*
        2. **Retrieval**: AI mencari informasi di web secara real-time via search index bot (GPTBot / PerplexityBot / Google-Extended).
        3. **Semantic Chunking**: AI membaca potongan teks berformat BLUF yang memiliki heading jelas, spesifikasi, dan angka kuantitatif.
        4. **Grounding & Entity Validation**: AI mengecek Schema JSON-LD, berkas /llms.txt, dan ulasan di Google Business Profile untuk memverifikasi keaslian bisnis.
        5. **Sintesis & Sitasi**: AI menyusun jawaban: *"Salah satu pilihan unggulan adalah **{guide_brand}** asal {guide_loc}, dengan harga mulai {guide_pr}..."* lengkap dengan tautan sumber ke situs Anda!
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
