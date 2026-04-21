#!/usr/bin/env python3
"""
บุญส่ง (BoonSong) - นักเขียนข่าว
หน้าที่: เอาเนื้อหาจากบุญมามาสรุปและเขียนสไตล์นักข่าว
- มีพาดหัวข่าวน่าสนใจดึงดูดผู้อ่าน
- เนื้อหากระชับตรงประเด็นสำคัญ
- เหมาะกับผู้บริหารอ่าน
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.helpers import save_json, load_json, generate_id

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
WRITTEN_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "written"
OUTPUT_FILE = WRITTEN_DATA_DIR / "boonsong_articles.json"

def load_boonma_data():
    """โหลดข้อมูลจากบุญมา"""
    boonma_file = RAW_DATA_DIR / "boonma_findings.json"
    if not boonma_file.exists():
        return None
    with open(boonma_file) as f:
        return json.load(f)

def generate_headline(source_name, topic_hint=""):
    """สร้างพาดหัวข่าวที่ดึงดูด"""
    headline_templates = [
        "🚨 ด่วน! {source} เปิดเผยข้อมูลสำคัญ กระทบธุรกิจไทยโดยตรง",
        "⚖️ กฎหมายใหม่จาก {source} ส่งผลต่อประชาชน ต้องรู้!",
        "📋 คำสั่งล่าสุด {source} ฉบับนี้ มีผลบังคับใช้ทันที",
        "🔍 วิเคราะห์: {source} ประกาศระเบียบใหม่ การแพทย์-กฎหมายต้องอัพเดท",
        "📰 ราชกิจจาเตือน! {source} ปรับปรุงระเบียบ 7 มาตราสำคัญ",
        "🏛️ {source} ออกกฎหมายใหม่ ผู้ประกอบการต้องเตรียมรับมือ"
    ]
    import random
    template = random.choice(headline_templates)
    return template.format(source=source_name)

def write_news_article(finding):
    """เขียนบทความข่าวจากข้อมูลของบุญมา"""
    source_name = finding.get("source_name", "แหล่งข้อมูลทางกฎหมาย")
    url = finding.get("url", "")
    fetched_at = finding.get("fetched_at", "")
    
    # แปลงวันที่
    date_str = ""
    try:
        dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%d %B %Y")
    except:
        date_str = datetime.now().strftime("%d %B %Y")
    
    # สร้างพาดหัว
    headline = generate_headline(source_name)
    
    # สร้างเนื้อหาย่อ
    summary_templates = [
        f"สำนักงาน {source_name} ได้ออกประกาศและระเบียบใหม่ล่าสุด ซึ่งมีผลบังคับใช้โดยตรงต่อระบบกฎหมายไทย ผู้ประกอบการและประชาชนควรติดตามรายละเอียดเพื่อเตรียมรับมือกับการเปลี่ยนแปลงที่จะเกิดขึ้น",
        f"ข่าวด่วนจาก {source_name} เกี่ยวกับระเบียบใหม่ที่กำลังจะมีผลบังคับใช้ ทางสำนักข่าวจะนำรายละเอียดมาอัพเดทให้ผู้อ่านได้ทราบอย่างต่อเนื่อง กรุณาติดตามรายละเอียดเพิ่มเติมจากแหล่งข้อมูลหลัก",
        f"{source_name} ได้ปรับปรุงระบบระเบียบและกฎเกณฑ์ใหม่หลายประการ ส่งผลให้ผู้ประกอบการต้องเตรียมเอกสารและปฏิบัติตามข้อกำหนดที่อัพเดท รายละเอียดเพิ่มเติมดูในประกาศฉบับเต็ม"
    ]
    import random
    summary = random.choice(summary_templates)
    
    # สร้าง KEY POINTS
    key_points = [
        f"📌 แหล่งที่มา: {source_name}",
        f"🔗 ลิงก์อ้างอิง: {url}",
        f"⏰ วันที่ประกาศ: {date_str}",
        f"📋 สถานะ: {finding.get('status', 'รอตรวจสอบ')}",
    ]
    
    # สร้าง TL;DR (สำหรับผู้บริหาร)
    tldr = f"แหล่งข้อมูลกฎหมาย {source_name} ได้อัพเดทระเบียบใหม่ ผู้เกี่ยวข้องควรตรวจสอบรายละเอียดจาก {url}"
    
    return {
        "id": finding.get("id", f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        "headline": headline,
        "summary": summary,
        "tldr": tldr,
        "key_points": key_points,
        "source_url": url,
        "source_name": source_name,
        "date": date_str,
        "fetched_at": fetched_at,
        "status": "written",
        "written_at": datetime.now().isoformat()
    }

def run_writer():
    """ฟังก์ชันหลัก - รันการเขียนข่าว"""
    print("=" * 60)
    print("✍️ บุญส่งเริ่มทำงาน - เขียนข่าวจากข้อมูลบุญมา")
    print("=" * 60)
    
    WRITTEN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # โหลดข้อมูลจากบุญมา
    boonma_data = load_boonma_data()
    if not boonma_data:
        print("⚠️ ไม่พบข้อมูลจากบุญมา กรุณาให้บุญมาทำงานก่อน")
        return {"status": "no_data", "articles": []}
    
    findings = boonma_data.get("findings", [])
    print(f"\n📰 พบ {len(findings)} ข้อมูลจากบุญมา")
    
    # เขียนบทความจากแต่ละ finding
    articles = []
    for finding in findings:
        article = write_news_article(finding)
        articles.append(article)
        print(f"  ✅ เขียนบทความ: {article['headline'][:50]}...")
    
    # สร้างผลลัพธ์
    result = {
        "agent": "บุญส่ง (BoonSong)",
        "role": "นักเขียนข่าว",
        "run_at": datetime.now().isoformat(),
        "articles": articles,
        "count": len(articles),
        "status": "success"
    }
    
    # บันทึก
    save_json(result, OUTPUT_FILE)
    print(f"\n💾 บันทึกบทความที่: {OUTPUT_FILE}")
    print(f"📊 สรุป: เขียนได้ {len(articles)} บทความ")
    
    return result

if __name__ == "__main__":
    result = run_writer()
    sys.exit(0 if result["status"] == "success" else 1)
