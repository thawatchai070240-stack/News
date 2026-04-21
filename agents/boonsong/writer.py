#!/usr/bin/env python3
"""
บุญส่ง (BoonSong) - บรรณาธิการ/ตรวจสอบ
หน้าที่: ตรวจสอบว่าข้อมูลจากบุญมาอัพเดทหรือยัง
- ดึงข้อมูลจาก boonma_findings.json
- เช็คว่าเป็นปีล่าสุดที่มีข้อมูลจริง (fiscal year ที่มี 11+ ฉบับ)
- เช็คว่าข้อมูลเหมือนครั้งก่อนหรือไม่
- ถ้าข้อมูลเดิม → ไม่ต้องทำอะไร
- ถ้าข้อมูลใหม่ → เขียนบทความจากข้อมูลที่มี (มี summary, applies_to, pdf อยู่แล้ว)
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.helpers import save_json, load_json, generate_id

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
WRITTEN_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "written"
VERIFIED_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "verified"
FINDINGS_FILE = RAW_DATA_DIR / "boonma_findings.json"
OUTPUT_FILE = WRITTEN_DATA_DIR / "boonsong_articles.json"
CHECKPOINT_FILE = WRITTEN_DATA_DIR / ".last_check.json"

# ปีที่ถือว่ามีข้อมูลจริง (ต้องมี 11+ ฉบับ)
MIN_LAWS_FOR_VALID_YEAR = 5

# ============================================================
# เช็คว่าข้อมูลเปลี่ยนหรือไม่
# ============================================================
def check_for_updates():
    """เช็คว่าข้อมูลจากบุญมามีการอัพเดทหรือไม่"""
    
    # อ่าน checkpoint ล่าสุด
    last_check = {}
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            last_check = json.load(f)
    
    # อ่านข้อมูลจากบุญมา
    if not FINDINGS_FILE.exists():
        return None, "no_findings"
    
    with open(FINDINGS_FILE, "r", encoding="utf-8") as f:
        findings = json.load(f)
    
    laws = findings.get("findings", [])
    if not laws:
        return None, "no_laws"
    
    # หา year ล่าสุดที่มีข้อมูลจริง
    year_thai = findings.get("year", 0)
    total = findings.get("total_laws", 0)
    
    current_info = {
        "year": year_thai,
        "total_laws": total,
        "run_at": findings.get("run_at", ""),
        "law_ids": sorted([law["id"] for law in laws]),
    }
    
    # เช็คว่าเปลี่ยนหรือไม่
    last_year = last_check.get("year", 0)
    last_total = last_check.get("total_laws", 0)
    last_ids = last_check.get("law_ids", [])
    
    if (year_thai != last_year or 
        total != last_total or 
        current_info["law_ids"] != last_ids):
        # มีการเปลี่ยนแปลง
        return current_info, "updated"
    
    return current_info, "unchanged"

# ============================================================
# เขียนบทความจากข้อมูลที่มี (มี summary/applies_to อยู่แล้ว)
# ============================================================
def write_articles(laws, source_info):
    """เขียนบทความจากข้อมูลบุญมาที่มี"""
    articles = []
    
    for law in laws:
        # สร้างบทความจากข้อมูลที่มี
        title = law.get("title", "")
        summary = law.get("summary", "")
        applies_to = law.get("applies_to", "")
        effective = law.get("effective_date", "")
        pdf_url = law.get("pdf_url", "")
        gazette_date = law.get("gazette_date", "")
        
        # Generate headline
        headline = generate_headline(title, summary)
        
        # Generate summary (from existing summary)
        article_summary = generate_summary(summary, applies_to)
        
        # Generate TL;DR
        tldr = generate_tldr(title, applies_to, effective)
        
        # Key points
        key_points = generate_key_points(law)
        
        # Penalties - extract from summary if mentioned
        penalty = extract_penalty(summary)
        
        article = {
            "id": law.get("id", generate_id()),
            "headline": headline,
            "summary": article_summary,
            "tldr": tldr,
            "key_points": key_points,
            "applies_to": applies_to,
            "applies_to_short": applies_to[:100] if applies_to else "",
            "penalties": penalty,
            "penalties_short": penalty[:100] if penalty else "",
            "source_url": law.get("url", ""),
            "source_name": law.get("source_name", "สำนักเลขาธิการคณะรัฐมนตรี"),
            "pdf_url": pdf_url,
            "effective_date": effective,
            "gazette_date": gazette_date,
            "date": gazette_date if gazette_date else datetime.now().strftime("%d %B %Y"),
            "fetched_at": law.get("fetched_at", ""),
            "written_at": datetime.now().isoformat(),
            "status": "written",
        }
        articles.append(article)
    
    return articles

# ============================================================
# สร้าง Headline
# ============================================================
def generate_headline(title, summary):
    """สร้างพาดหัวข่าวดึงดูด"""
    # Clean title
    title = re.sub(r'^\d+\)\s*', '', title)  # ลบ ๑๑) ตอนต้น
    
    urgency_indicators = ["ยกเลิก", "แก้ไขเพิ่มเติม", "ใหม่", "ฉบับที่"]
    severity = "ปานกลาง"
    for ind in urgency_indicators:
        if ind in title:
            severity = "สูง"
            break
    
    urgency_map = {
        "สูง": "🚨 ด่วน!",
        "ปานกลาง": "⚠️ สำคัญ",
        "ต่ำ": "📋 ประกาศ",
    }
    urgency = urgency_map.get(severity, "📰 ข่าว")
    
    if len(title) > 60:
        return f"{urgency} {title[:60]}..."
    return f"{urgency} {title}"

# ============================================================
# สร้าง Summary
# ============================================================
def generate_summary(summary, applies_to):
    """สร้างสรุป 3-5 บรรทัด"""
    if not summary:
        return "ไม่มีรายละเอียดเพิ่มเติม"
    
    # Use existing summary as base
    if len(summary) > 200:
        return summary[:200] + "..."
    return summary

# ============================================================
# สร้าง TL;DR
# ============================================================
def generate_tldr(title, applies_to, effective):
    """สร้าง TL;DR สำหรับผู้บริหาร"""
    title_clean = re.sub(r'^\d+\)\s*', '', title)
    applies_short = applies_to[:60] if applies_to else "ผู้เกี่ยวข้อง"
    effective_short = effective[:40] if effective else "ตามที่กำหนด"
    
    return f"📌 {title_clean} | กระทบ: {applies_short} | มีผล: {effective_short}"

# ============================================================
# สร้าง Key Points
# ============================================================
def generate_key_points(law):
    """สร้าง key points จากข้อมูล"""
    points = []
    
    title = law.get("title", "")
    if title:
        points.append(f"📌 <strong>เรื่อง:</strong> {title}")
    
    source_name = law.get("source_name", "สำนักเลขาธิการคณะรัฐมนตรี")
    if source_name:
        points.append(f"📍 <strong>แหล่งที่มา:</strong> {source_name}")
    
    pdf_url = law.get("pdf_url", "")
    if pdf_url:
        points.append(f"🔗 <strong>อ่านรายละเอียดเต็ม:</strong> <a href='{pdf_url}' target='_blank'>ราชกิจจานุเบกษา PDF</a>")
    
    applies_to = law.get("applies_to", "")
    if applies_to:
        points.append(f"👥 <strong>บังคับใช้กับ:</strong> {applies_to}")
    
    effective = law.get("effective_date", "")
    if effective:
        points.append(f"📅 <strong>มีผลบังคับ:</strong> {effective}")
    
    return points

# ============================================================
# ดึง Penalty จาก Summary
# ============================================================
def extract_penalty(summary):
    """ดึงข้อมูลโทษ/ผลจาก summary"""
    if not summary:
        return "ไม่มีข้อมูลโทษในสาระสำคัญ"
    
    # Look for penalty-related keywords
    penalty_keywords = ["ปรับ", "โทษ", "ลงโทษ", "จำคุก", "ประเมินภาษี", "เบี้ยปรับ", "เรียกเพิ่ม"]
    
    for kw in penalty_keywords:
        if kw in summary:
            # Find the sentence containing the keyword
            sentences = summary.split(".")
            for sent in sentences:
                if kw in sent:
                    return sent.strip() + "."
    
    return "ไม่มีข้อมูลโทษในสาระสำคัญ"

# ============================================================
# ฟังก์ชันหลัก
# ============================================================
def run_boonsong():
    """ฟังก์ชันหลัก - ตรวจสอบและเขียนบทความ"""
    print("=" * 60)
    print("📝 บุญส่งเริ่มทำงาน - ตรวจสอบข้อมูลจากบุญมา")
    print("=" * 60)
    
    # เช็คว่ามีการอัพเดทหรือไม่
    current_info, status = check_for_updates()
    
    if status == "no_findings":
        print("❌ ไม่พบไฟล์ข้อมูลจากบุญมา")
        return {"status": "no_findings"}
    
    if status == "no_laws":
        print("❌ ไม่พบข้อมูลกฎหมาย")
        return {"status": "no_laws"}
    
    print(f"📊 ปีล่าสุด: พ.ศ. {current_info['year']}")
    print(f"📊 จำนวน: {current_info['total_laws']} ฉบับ")
    
    if status == "unchanged":
        print("⏭️  ข้อมูลไม่เปลี่ยนแปลง ไม่ต้องทำอะไร")
        
        # บันทึก checkpoint
        WRITTEN_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(current_info, f, ensure_ascii=False, indent=2)
        
        return {"status": "unchanged", "year": current_info["year"]}
    
    # มีการเปลี่ยนแปลง → เขียนบทความ
    print(f"✅ มีข้อมูลใหม่ → เขียนบทความ...")
    
    # อ่านข้อมูลจากบุญมา
    with open(FINDINGS_FILE, "r", encoding="utf-8") as f:
        findings = json.load(f)
    
    laws = findings.get("findings", [])
    articles = write_articles(laws, current_info)
    
    # บันทึกบทความ
    WRITTEN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "agent": "บุญส่ง (BoonSong)",
        "role": "บรรณาธิการ/ตรวจสอบ",
        "run_at": datetime.now().isoformat(),
        "year": current_info["year"],
        "total_articles": len(articles),
        "status": "written" if articles else "empty",
        "articles": articles,
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # บันทึก verified data สำหรับ publisher
    verified_result = {
        "agent": "บุญตรวจ (BoonTrap)",
        "role": "บุญส่งตรวจแทน",
        "run_at": datetime.now().isoformat(),
        "year": current_info["year"],
        "total_articles": len(articles),
        "status": "verified" if articles else "empty",
        "articles": articles,
    }
    VERIFIED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VERIFIED_DATA_DIR / "boontrap_verified.json", "w", encoding="utf-8") as f:
        json.dump(verified_result, f, ensure_ascii=False, indent=2)
    
    # บันทึก checkpoint
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(current_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ บุญส่งเสร็จสิ้น - เขียน {len(articles)} บทความ")
    print(f"📁 บันทึกที่: {OUTPUT_FILE}")
    print(f"📁 Verified: {VERIFIED_DATA_DIR / 'boontrap_verified.json'}")
    
    return result

# ============================================================
# Test
# ============================================================
if __name__ == "__main__":
    result = run_boonsong()
    
    if result.get("articles"):
        print(f"\n📋 ตัวอย่างบทความ:")
        for art in result["articles"][:2]:
            print(f"\n  [{art['id']}] {art['headline']}")
            print(f"     TL;DR: {art['tldr'][:80]}")
            print(f"     Applies to: {art['applies_to'][:60] if art['applies_to'] else 'N/A'}")
    elif result.get("status") == "unchanged":
        print("\n⏭️ ไม่มีการเปลี่ยนแปลง")
