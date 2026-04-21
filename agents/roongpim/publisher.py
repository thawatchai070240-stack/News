#!/usr/bin/env python3
"""
โรงพิมพ์บุญมี (RoongPim BoonMee) - ตีพิมพ์ HTML
หน้าที่: เอาเนื้อหาจากบุญส่ง (ที่ผ่านบุญตรวจแล้ว) มาสร้างเป็น Interactive HTML
- รูปแบบน่าเชื่อถือ เหมือนเว็บข่าวจริง
- มี Interactive elements
"""

import json
import sys
from datetime import datetime
from pathlib import Path

VERIFIED_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "verified"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

def load_verified_data():
    """โหลดข้อมูลที่ผ่านการตรวจ"""
    verified_file = VERIFIED_DATA_DIR / "boontrap_verified.json"
    if not verified_file.exists():
        return None
    with open(verified_file) as f:
        return json.load(f)

def generate_article_html(article, index):
    """สร้าง HTML สำหรับบทความเดียว"""
    credibility = article.get("credibility_level", "ปานกลาง")
    level_color = {
        "สูงมาก": "#10b981",
        "สูง": "#22c55e",
        "ปานกลาง": "#f59e0b",
        "ต่ำ": "#ef4444"
    }.get(credibility, "#6b7280")
    
    key_points_html = ""
    if article.get("key_points"):
        for point in article["key_points"]:
            key_points_html += f"<li>{point}</li>"
    
    return f'''
<article class="news-card" data-id="{article['id']}" data-index="{index}">
    <div class="card-header">
        <span class="news-badge">📋 กฎหมาย</span>
        <span class="credibility-badge" style="background:{level_color}20; color:{level_color}">
            ✓ {credibility}
        </span>
    </div>
    <h2 class="news-headline">{article.get('headline', 'ไม่มีหัวข้อ')}</h2>
    <p class="news-summary">{article.get('summary', '')}</p>
    <div class="news-tldr">
        <strong>📌 TL;DR:</strong> {article.get('tldr', '')}
    </div>
    <ul class="key-points">
        {key_points_html}
    </ul>
    <div class="news-meta">
        <span class="news-date">📅 {article.get('date', '')}</span>
        <span class="news-source">📍 {article.get('source_name', '')}</span>
    </div>
    <div class="news-actions">
        <a href="{article.get('source_url', '#')}" target="_blank" class="btn-read-source">
            🔗 อ่านที่มาต้นฉบับ
        </a>
        <button class="btn-share" onclick="shareArticle('{article['id']}')">
            📤 แชร์
        </button>
    </div>
</article>'''

def generate_full_html(articles, run_at):
    """สร้าง HTML เต็ม"""
    articles_html = ""
    for i, article in enumerate(articles):
        articles_html += generate_article_html(article, i)
    
    return f'''<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>สำนักข่าวบุญมา | ข่าวกฎหมายไทยล่าสุด</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #1e3a5f;
            --secondary: #2d5a87;
            --accent: #c9a227;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1a1a2e;
            --text-muted: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        
        body {{
            font-family: 'Sarabun', 'Noto Sans Thai', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
        /* Header */
        .site-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 2rem 1rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        .site-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .site-header .tagline {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .site-header .update-time {{
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 2rem;
            display: inline-block;
            font-size: 0.9rem;
        }}
        
        /* Main Container */
        .main-container {{
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        
        /* Stats Bar */
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: var(--card-bg);
            padding: 1rem 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            min-width: 120px;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        /* News Grid */
        .news-grid {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        
        /* News Card */
        .news-card {{
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
            border-left: 4px solid var(--accent);
        }}
        
        .news-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .news-badge {{
            background: var(--primary);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.8rem;
        }}
        
        .credibility-badge {{
            padding: 0.3rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .news-headline {{
            font-size: 1.3rem;
            color: var(--primary);
            margin-bottom: 0.8rem;
            line-height: 1.4;
        }}
        
        .news-summary {{
            color: var(--text);
            margin-bottom: 1rem;
            line-height: 1.7;
        }}
        
        .news-tldr {{
            background: #f0f9ff;
            border-left: 3px solid var(--secondary);
            padding: 0.8rem 1rem;
            margin-bottom: 1rem;
            border-radius: 0 0.5rem 0.5rem 0;
            font-size: 0.95rem;
        }}
        
        .key-points {{
            list-style: none;
            margin-bottom: 1rem;
        }}
        
        .key-points li {{
            padding: 0.4rem 0;
            padding-left: 1.5rem;
            position: relative;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        .key-points li::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: var(--accent);
            font-weight: bold;
        }}
        
        .news-meta {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        
        .news-actions {{
            display: flex;
            gap: 0.8rem;
            flex-wrap: wrap;
        }}
        
        .btn-read-source, .btn-share {{
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            font-family: inherit;
        }}
        
        .btn-read-source {{
            background: var(--primary);
            color: white;
            text-decoration: none;
        }}
        
        .btn-read-source:hover {{
            background: var(--secondary);
        }}
        
        .btn-share {{
            background: white;
            color: var(--primary);
            border: 1px solid var(--primary);
        }}
        
        .btn-share:hover {{
            background: var(--primary);
            color: white;
        }}
        
        /* Footer */
        .site-footer {{
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        .team-info {{
            background: var(--primary);
            color: white;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 1rem;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .news-card {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        .news-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .news-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .news-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .news-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .news-card:nth-child(5) {{ animation-delay: 0.5s; }}
        
        /* Responsive */
        @media (max-width: 600px) {{
            .site-header h1 {{ font-size: 1.8rem; }}
            .stats-bar {{ gap: 1rem; }}
            .news-meta {{ flex-direction: column; gap: 0.5rem; }}
            .news-actions {{ flex-direction: column; }}
            .btn-read-source, .btn-share {{ text-align: center; }}
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <h1>📰 สำนักข่าวบุญมา</h1>
        <p class="tagline">ข่าวกฎหมายไทยอัพเดทล่าสุด | ตรวจสอบความถูกต้องโดย AI</p>
        <div class="update-time">
            🕐 อัพเดทล่าสุด: {run_at}
        </div>
    </header>
    
    <main class="main-container">
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-value">{len(articles)}</div>
                <div class="stat-label">📰 ข่าวทั้งหมด</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{sum(1 for a in articles if a.get('credibility_level') in ['สูงมาก','สูง'])}</div>
                <div class="stat-label">✅ น่าเชื่อถือ</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(articles)}</div>
                <div class="stat-label">🔗 แหล่งอ้างอิง</div>
            </div>
        </div>
        
        <div class="team-info">
            <strong>ทีม AI สำนักข่าวบุญมา:</strong><br>
            📡 บุญมา (นักหาข้อมูล) | ✍️ บุญส่ง (นักเขียน) | 🔎 บุญตรวจ (ตรวจข้อเท็จจริง) 
        </div>
        
        <div class="news-grid">
            {articles_html}
        </div>
    </main>
    
    <footer class="site-footer">
        <p>📌 สำนักข่าวบุญมา — ข่าวกฎหมายไทยอัพเดททุกวัน</p>
        <p>สร้างโดย AI Agents: บุญมา | บุญส่ง | บุญตรวจ | โรงพิมพ์บุญมี | บุญรัก | บกลายจุด</p>
        <p style="margin-top:0.5rem; opacity:0.7;">© 2026 BoonMa News Agency</p>
    </footer>
    
    <script>
        // Share functionality
        function shareArticle(id) {{
            if (navigator.share) {{
                navigator.share({{
                    title: 'สำนักข่าวบุญมา',
                    text: 'ข่าวกฎหมายไทยล่าสุด',
                    url: window.location.href
                }});
            }} else {{
                alert('คัดลอกลิงก์แล้ว: ' + window.location.href);
            }}
        }}
        
        // Smooth scroll for better UX
        document.querySelectorAll('.news-card').forEach(card => {{
            card.addEventListener('click', () => {{
                card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }});
        }});
    </script>
</body>
</html>'''

def run_publisher():
    """ฟังก์ชันหลัก - รันการตีพิมพ์ HTML"""
    print("=" * 60)
    print("🖨️ โรงพิมพ์บุญมีเริ่มทำงาน - สร้าง Interactive HTML")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # โหลดข้อมูลที่ผ่านการตรวจ
    verified_data = load_verified_data()
    if not verified_data:
        print("⚠️ ไม่พบข้อมูลที่ผ่านการตรวจ กรุณาให้บุญตรวจทำงานก่อน")
        return {"status": "no_data", "html_file": None}
    
    verifications = verified_data.get("verifications", [])
    verified_articles = [v for v in verifications if v["status"] == "verified"]
    
    print(f"\n📰 พบ {len(verified_articles)} บทความที่ผ่านการตรวจ")
    
    if not verified_articles:
        print("⚠️ ไม่มีบทความที่ผ่านการตรวจ")
        return {"status": "no_verified", "html_file": None}
    
    # แปลงรูปแบบสำหรับ HTML
    # รวมข้อมูลจาก boonsong กับ boontrap
    boonsong_file = Path(__file__).parent.parent.parent / "data" / "written" / "boonsong_articles.json"
    boonsong_data = json.load(open(boonsong_file)) if boonsong_file.exists() else {"articles": []}
    
    articles_for_html = []
    for v in verifications:
        if v["status"] == "verified":
            # หาข้อมูลต้นฉบับจาก boonsong
            article_data = next(
                (a for a in boonsong_data.get("articles", []) if a.get("id") == v.get("article_id")),
                {}
            )
            combined = {**article_data, **v}
            articles_for_html.append(combined)
    
    # สร้าง HTML
    run_at = verified_data.get("run_at", datetime.now().isoformat())
    html_content = generate_full_html(articles_for_html, run_at)
    
    # บันทึกไฟล์
    output_file = OUTPUT_DIR / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n💾 บันทึก HTML ที่: {output_file}")
    print(f"📊 สรุป: สร้าง HTML จาก {len(articles_for_html)} บทความ")
    
    return {
        "status": "success",
        "html_file": str(output_file),
        "article_count": len(articles_for_html)
    }

if __name__ == "__main__":
    result = run_publisher()
    sys.exit(0 if result["status"] == "success" else 1)
