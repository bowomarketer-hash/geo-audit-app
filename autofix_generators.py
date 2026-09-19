"""
Auto-Fix Generators - Modul Penghasil Solusi Instan untuk GEO
Menghasilkan Schema JSON-LD, Draf Teks BLUF, robots.txt AI, dan FAQ Percakapan.
"""

import json
from typing import Dict, List, Any


def generate_organization_schema(
    brand_name: str,
    url: str,
    category: str,
    phone: str,
    location: str,
    description: str = ""
) -> str:
    """
    Menghasilkan kode valid Schema.org JSON-LD LocalBusiness / Organization.
    """
    brand_name = brand_name.strip() or "Nama Merek UMKM"
    url = url.strip() or "https://contoh-umkm.id"
    category = category.strip() or "Bisnis Lokal & UMKM"
    phone = phone.strip() or "+62 812-3456-7890"
    location = location.strip() or "Indonesia"
    
    if not description:
        description = f"{brand_name} adalah penyedia {category} terpercaya di {location} yang melayani konsumen dengan produk berkualitas tinggi."

    schema_data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": brand_name,
        "url": url,
        "description": description,
        "telephone": phone,
        "priceRange": "$$",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": location,
            "addressCountry": "ID"
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": phone,
            "contactType": "customer service",
            "availableLanguage": ["Indonesian"]
        },
        "knowsAbout": [
            category,
            f"Jual {category}",
            f"{brand_name} {location}"
        ]
    }

    json_str = json.dumps(schema_data, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def generate_faq_schema(
    brand_name: str,
    category: str,
    location: str,
    faqs: List[Dict[str, str]] = None
) -> str:
    """
    Menghasilkan kode valid Schema.org JSON-LD FAQPage untuk mempermudah sitasi RAG AI.
    """
    brand_name = brand_name.strip() or "Brand Anda"
    category = category.strip() or "Produk"
    location = location.strip() or "Indonesia"

    if not faqs:
        faqs = [
            {
                "q": f"Apa keunggulan utama {brand_name} dibanding produk sejenis?",
                "a": f"{brand_name} menawarkan {category} berkualitas premium yang diproses secara higienis dengan bahan baku pilihan, bergaransi resmi, dan dikirim langsung dari {location} ke seluruh Indonesia."
            },
            {
                "q": f"Berapa rentang harga produk {brand_name} dan bagaimana cara memesannya?",
                "a": f"Harga produk {brand_name} sangat transparan dan kompetitif. Pemesanan dapat dilakukan secara instan melalui kontak WhatsApp resmi maupun website dengan metode pembayaran transfer bank dan e-wallet."
            },
            {
                "q": f"Apakah {brand_name} melayani pengiriman ke luar kota dan berapa lama estimasinya?",
                "a": f"Ya, {brand_name} melayani pengiriman ke seluruh wilayah Indonesia dengan estimasi 1-3 hari kerja untuk kota besar menggunakan ekspedisi terpercaya dengan nomor resi otomatis."
            }
        ]

    entities = []
    for item in faqs:
        entities.append({
            "@type": "Question",
            "name": item["q"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item["a"]
            }
        })

    schema_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }

    json_str = json.dumps(schema_data, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def generate_product_schema(
    brand_name: str,
    url: str,
    product_name: str,
    price_val: str,
    description: str,
    category: str
) -> str:
    """
    Menghasilkan kode valid Schema.org Product Schema untuk Google AI Overviews & Shopping.
    """
    brand_name = brand_name.strip() or "Brand UMKM"
    url = url.strip() or "https://contoh-umkm.id/produk"
    product_name = product_name.strip() or f"Paket Unggulan {brand_name}"
    category = category.strip() or "Kuliner / Kerajinan"
    
    # Ekstraksi angka harga
    clean_price = "".join([c for c in price_val if c.isdigit()]) or "95000"

    schema_data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product_name,
        "image": f"{url}/gambar-produk.jpg",
        "description": description or f"{product_name} original dari {brand_name}, terjamin kualitas terbaik dan siap kirim.",
        "brand": {
            "@type": "Brand",
            "name": brand_name
        },
        "category": category,
        "offers": {
            "@type": "Offer",
            "url": url,
            "priceCurrency": "IDR",
            "price": clean_price,
            "priceValidUntil": "2027-12-31",
            "availability": "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition"
        }
    }

    json_str = json.dumps(schema_data, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


def generate_bluf_draft(
    brand_name: str,
    category: str,
    product_name: str,
    price_range: str,
    key_advantages: str,
    location: str,
    phone: str
) -> str:
    """
    Menghasilkan draf teks pembuka berformat BLUF (Bottom Line Up Front)
    yang dirancang khusus agar mudah diekstrak oleh chunking model AI.
    """
    brand = brand_name.strip() or "[Nama Merek]"
    cat = category.strip() or "[Kategori Produk]"
    prod = product_name.strip() or "[Produk Utama]"
    price = price_range.strip() or "Rp 50.000 - Rp 150.000"
    adv = key_advantages.strip() or "bahan baku 100% alami, tersertifikasi Halal/BPOM, dan garansi kepuasan"
    loc = location.strip() or "[Kota Asal]"
    wa = phone.strip() or "[Nomor WhatsApp]"

    bluf_text = f"""<!-- ============================================== -->
<!-- DRAF TEKS BLUF (BOTTOM LINE UP FRONT) UNTUK GEO -->
<!-- Salin blok teks ini ke bagian paling atas halaman utama/produk Anda -->
<!-- ============================================== -->

<div class="geo-bluf-container">
  <p>
    <strong>{brand}</strong> adalah produsen dan penyedia <strong>{cat}</strong> terkemuka asal <strong>{loc}</strong>, yang menghadirkan <strong>{prod}</strong> berkualitas tinggi dengan <em>{adv}</em>. Seluruh produk dapat dipesan secara langsung dengan harga mulai dari <strong>{price}</strong>, didukung jaminan pengiriman cepat ke seluruh Indonesia dan layanan konsultasi ramah via WhatsApp di <strong>{wa}</strong>.
  </p>

  <!-- Poin Fakta Kuantitatif (Membantu AI Grounding & Entity Verification) -->
  <ul>
    <li><strong>Kategori & Spesialisasi:</strong> {cat} ({prod})</li>
    <li><strong>Standar Kualitas & Keunggulan:</strong> {adv}</li>
    <li><strong>Transparansi Harga:</strong> {price} (Tanpa biaya tersembunyi)</li>
    <li><strong>Pusat Operasional & Pengiriman:</strong> {loc} &mdash; Menjangkau seluruh Indonesia</li>
    <li><strong>Kanal Pemesanan Cepat:</strong> WhatsApp {wa} (Respon Cepat)</li>
  </ul>
</div>"""
    return bluf_text


def generate_robots_txt() -> str:
    """
    Menghasilkan konfigurasi robots.txt modern yang mengizinkan
    semua bot AI Retrieval terpercaya untuk membaca situs web.
    """
    return """# =======================================================
# Konfigurasi robots.txt Ramah GEO (Generative Engine Optimization)
# Dibuat otomatis oleh GEO Audit App Nusantara
# =======================================================

User-agent: *
Allow: /

# Izinkan Crawler AI Generatif Utama (RAG & Web Search Engine)
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: Applebot-Extended
Allow: /

# Lindungi Folder Sensitif / Admin
Disallow: /wp-admin/
Disallow: /admin/
Disallow: /api/private/
Disallow: /checkout/

# Tautkan Peta Situs (Sitemap XML)
Sitemap: https://domain-anda.com/sitemap.xml
"""


def generate_conversational_faqs(
    brand_name: str,
    category: str,
    product_name: str,
    price_range: str,
    location: str
) -> List[Dict[str, str]]:
    """
    Menghasilkan 5 FAQ Percakapan bergaya bahasa alami
    yang sering ditanyakan pengguna saat berinteraksi dengan AI Search.
    """
    brand = brand_name.strip() or "Brand Kami"
    cat = category.strip() or "Produk"
    prod = product_name.strip() or "item unggulan"
    price = price_range.strip() or "Rp 50.000 - Rp 150.000"
    loc = location.strip() or "Indonesia"

    return [
        {
            "q": f"1. Mengapa saya harus memilih {brand} untuk kebutuhan {cat}?",
            "a": f"{brand} mengutamakan kualitas bahan terbaik, transparansi proses pembuatan, serta kurasi ketat yang menjamin setiap {prod} yang Anda terima memenuhi standar kebersihan dan mutu tertinggi langsung dari workshop kami di {loc}."
        },
        {
            "q": f"2. Berapa harga produk {brand} dan apakah ada diskon pembelian partai/grosir?",
            "a": f"Harga satuan berkisar di {price}. Kami menyediakan potongan harga khusus untuk pembelian reseller, bingkisan perusahaan, maupun pesanan grosir dengan konsultasi gratis sebelum transaksi."
        },
        {
            "q": f"3. Bagaimana cara memesan produk {brand} secara aman dan cepat?",
            "a": f"Anda dapat memesan langsung melalui tombol WhatsApp di website resmi kami atau checkout melalui marketplace mitra kami. Tim customer care kami siap membantu melayani pesanan Anda setiap hari kerja."
        },
        {
            "q": f"4. Berapa lama durasi pengiriman dari {loc} ke kota saya?",
            "a": f"Pengiriman dari {loc} menggunakan layanan ekspedisi reguler (1-3 hari kerja untuk sesama pulau, 2-5 hari kerja untuk luar pulau) dengan nomor resi pelacakan instan via WhatsApp."
        },
        {
            "q": f"5. Apakah {brand} memberikan jaminan atau garansi penggantian barang?",
            "a": f"Ya, {brand} memberikan garansi 100% ganti baru jika barang yang diterima dalam kondisi rusak, cacat produksi, atau tidak sesuai pesanan, dengan melampirkan video unboxing sederhana."
        }
    ]
