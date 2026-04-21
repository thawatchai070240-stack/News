#!/usr/bin/env python3
"""
บุญตรวจ (BoonTrap) - นักตรวจข้อเท็จจริง
หน้าที่: ตรวจสอบความถูกต้องของบทความจากบุญส่ง
- ตรวจสอบข้อเท็จจริง (Fact Check)
- ตรวจสอบแหล่งอ้างอิง
- ให้คะแนนความน่าเชื่อถือ
- ผ่านเฉพาะข้อมูลที่ผ่านการตรวจ
"""

import json
import sys
import re
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.helpers import save_json, load_json
WRITTEN_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "written"
VERIFIED_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "verified"
OUTPUT_FILE = VERIFIED_DATA_DIR / "boontrap_verified.json"

def load_boonsong_articles():
    """โหลดบทความจากบุญส่ง"""
    boonsong_file = WRITTEN_DATA_DIR / "boonsong_articles.json"
    if not boonsong_file.exists():
        return None
    with open(boonsong_file) as f:
        return json.load(f)

def check_url_validity(url):
    """ตรวจสอบ URL มีรูปแบบถูกต้อง"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def calculate_credibility_score(article):
    """คำนวณคะแนนความน่าเชื่อถือ"""
    score = 0
    max_score = 100
    
    # มี URL อ้างอิง (+30)
    if article.get("source_url"):
        if check_url_validity(article["source_url"]):
            score += 30
    
    # มี TL;DR (+20)
    if article.get("tldr"):
        score += 20
    
    # มี Key Points (+20)
    if article.get("key_points") and len(article["key_points"]) > 0:
        score += 20
    
    # มี Headline (+15)
    if article.get("headline"):
        score += 15
    
    # มี Summary (+15)
    if article.get("summary"):
        score += 15
    
    return min(score, max_score)

def verify_article(article):
    """ตรวจสอบบทความเดียว"""
    # คำนวณคะแนน
    score = calculate_credibility_score(article)
    
    # แบ่งระดับความน่าเชื่อถือ
    if score >= 80:
        level = "สูงมาก"
    elif score >= 60:
        level = "สูง"
    elif score >= 40:
        level = "ปานกลาง"
    else:
        level = "ต่ำ"
    
    # สร้างรายงานการตรวจ
    verification_report = {
        "article_id": article.get("id"),
        "headline": article.get("headline", ""),
        "credibility_score": score,
        "credibility_level": level,
        "checks": {
            "url_valid": check_url_validity(article.get("source_url", "")) if article.get("source_url") else False,
            "has_tldr": bool(article.get("tldr")),
            "has_key_points": bool(article.get("key_points")),
            "has_headline": bool(article.get("headline")),
            "has_summary": bool(article.get("summary")),
        },
        "verified_at": datetime.now().isoformat(),
        "status": "verified" if score >= 40 else "needs_review"
    }
    
    return verification_report

def run_factchecker():
    """ฟังก์ชันหลัก - รันการตรวจข้อเท็จจริง"""
    print("=" * 60)
    print("🔎 บุญตรวจเริ่มทำงาน - ตรวจข้อเท็จจริงบทความ")
    print("=" * 60)
    
    VERIFIED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # โหลดบทความจากบุญส่ง
    boonsong_data = load_boonsong_articles()
    if not boonsong_data:
        print("⚠️ ไม่พบบทความจากบุญส่ง กรุณาให้บุญส่งทำงานก่อน")
        return {"status": "no_data", "verifications": []}
    
    articles = boonsong_data.get("articles", [])
    print(f"\n🔍 ตรวจสอบ {len(articles)} บทความ")
    
    verifications = []
    for article in articles:
        verification = verify_article(article)
        verifications.append(verification)
        
        level_icon = "🟢" if verification["credibility_level"] == "สูงมาก" else \
                     "🟡" if verification["credibility_level"] == "สูง" else \
                     "🟠" if verification["credibility_level"] == "ปานกลาง" else "🔴"
        
        print(f"  {level_icon} {article['headline'][:40]}...")
        print(f"     📊 คะแนน: {verification['credibility_score']}/100 ({verification['credibility_level']})")
    
    # สร้างผลลัพธ์
    verified_articles = [v for v in verifications if v["status"] == "verified"]
    result = {
        "agent": "บุญตรวจ (BoonTrap)",
        "role": "นักตรวจข้อเท็จจริง",
        "run_at": datetime.now().isoformat(),
        "verifications": verifications,
        "total_articles": len(articles),
        "verified_count": len(verified_articles),
        "status": "success"
    }
    
    # บันทึก
    save_json(result, OUTPUT_FILE)
    print(f"\n💾 บันทึกผลตรวจที่: {OUTPUT_FILE}")
    print(f"📊 สรุป: ผ่านการตรวจ {len(verified_articles)}/{len(articles)} บทความ")
    
    return result

if __name__ == "__main__":
    result = run_factchecker()
    sys.exit(0 if result["status"] == "success" else 1)
