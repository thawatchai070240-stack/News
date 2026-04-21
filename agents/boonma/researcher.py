#!/usr/bin/env python3
"""
บุญมา (BoonMa) - นักหาข้อมูลกฎหมายไทย
หน้าที่: ค้นหากฎหมายไทยอัพเดทใหม่จากราชกิจจานุเบกษา

แหล่งข้อมูล: www.soc.go.th (ไม่ต้องใช้ Token)
- หน้า "กฎหมายสำคัญที่ประกาศในราชกิจจานุเบกษา"
- ข้อมูลทั้งหมดอยู่ใน HTML (ไม่ต้องใช้ JavaScript/AJAX)
- ดึงรายละเอียดแต่ละฉบับ (สาระสำคัญ, ผู้เกี่ยวข้อง, วันที่มีผล, PDF)
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.helpers import save_json, generate_id

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "boonma_findings.json"

# ============================================================
# แหล่งข้อมูลจาก www.soc.go.th (ไม่ต้องใช้ Token)
# ============================================================
SOURCE_CONFIG = {
    "base_url": "https://www.soc.go.th",
    "list_page": "/?p=7548",
    "name": "สำนักเลขาธิการคณะรัฐมนตรี",
    "type": "government_law",
    "description": "กฎหมายสำคัญที่ประกาศในราชกิจจานุเบกษา จากเว็บ สลค.",
}

# ============================================================
# ดึง HTML จากหน้าเว็บ
# ============================================================
def fetch_html(url_path, timeout=20):
    """ดึง HTML จาก www.soc.go.th"""
    url = SOURCE_CONFIG["base_url"] + url_path
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
    }
    req = Request(url, headers=headers)
    try:
        resp = urlopen(req, timeout=timeout)
        raw = resp.read()
        try:
            html = raw.decode('utf-8')
        except UnicodeDecodeError:
            html = raw.decode('utf-8', errors='replace')
        return html
    except HTTPError as e:
        print(f"  ERROR: HTTP {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# ============================================================
# แปลงเลขไทยเป็นอารบิก
# ============================================================
def thai_to_arabic(text):
    """แปลงตัวเลขไทยเป็นอารบิก"""
    thai_nums = "๐๑๒๓๔๕๖๗๘๙"
    arabic_nums = "0123456789"
    result = text
    for t, a in zip(thai_nums, arabic_nums):
        result = result.replace(t, a)
    return result

def thai_year_to_ad(thai_year_str):
    """แปลงปี พ.ศ. ไทยเป็น ค.ศ."""
    try:
        # Extract number from Thai string
        num = int(thai_to_arabic(thai_year_str))
        return num - 543
    except:
        return None

def ad_year_to_thai_year(ad_year):
    """แปลง ค.ศ. เป็น พ.ศ. ไทย (สตริงง่าย)"""
    thai_year = ad_year + 543
    # แปลงเป็นเลขไทย
    thai_nums = "๐๑๒๓๔๕๖๗๘๙"
    result = ""
    for d in str(thai_year):
        result += thai_nums[int(d)]
    return result

# ============================================================
# ดึงรายการกฎหมายจากหน้าเว็บ (HTML ทั้งหมด)
# ============================================================
def extract_laws_from_html(html):
    """ดึงกฎหมายทั้งหมดจาก HTML"""
    laws_by_year = {}
    
    # Pattern: กฎหมายแต่ละฉบับอยู่ใน div ที่มี class="col-md-12 fiscal_year fiscal_YYYY"
    # ลิงค์อยู่ในรูปแบบ: <a href="/?page_id=2375&id=XXX" ...> ชื่อกฎหมาย </a>
    
    fiscal_pattern = r'<div class="col-md-12 fiscal_year fiscal_(\d{4})">\s*<a[^>]+href=["\']([^"\']*id=(\d+)[^"\']*)["\'][^>]*>\s*([^<]+)\s*</a>'
    matches = re.findall(fiscal_pattern, html, re.DOTALL)
    
    for year_ad, href, law_id, title in matches:
        year_ad_int = int(year_ad)
        year_thai = year_ad_int + 543  # พ.ศ.
        
        if year_ad_int not in laws_by_year:
            laws_by_year[year_ad_int] = []
        
        # Clean title
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        clean_title = ' '.join(clean_title.split())
        
        law = {
            "id": f"soc_{law_id}",
            "detail_url": href,
            "title": clean_title,
            "year_ad": year_ad_int,
            "year_thai": year_thai,
        }
        laws_by_year[year_ad_int].append(law)
    
    return laws_by_year

# ============================================================
# ดึงรายละเอียดกฎหมายจากหน้า detail
# ============================================================
def get_law_detail(html, law_info):
    """ดึงรายละเอียด (สาระสำคัญ, ผู้เกี่ยวข้อง, วันที่, PDF) จากหน้า detail"""
    
    result = law_info.copy()
    
    # ดึงชื่อกฎหมายจาก paragraph
    p_match = re.search(r'<p[^>]*>\s*([^<]*พระราชบัญญัติ[^<]+)\s*</p>', html)
    if p_match:
        result["full_title"] = p_match.group(1).strip()
    
    # ดึงตารางรายละเอียด
    table_pattern = r'<table[^>]*>(.*?)</table>'
    table_match = re.search(table_pattern, html, re.DOTALL)
    
    if table_match:
        table_html = table_match.group(1)
        
        # ดึง key-value จาก td โดยดึง span ข้างใน
        # Key อยู่ในรูปแบบ: <span><b>ชื่อหัวข้อ</b></span>
        # Value อยู่ในรูปแบบ: <span>ค่าข้อมูล</span>
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, table_html, re.DOTALL)
        
        for row in rows:
            # ดึง key (ใน td แรก > span > b)
            key_match = re.search(r'<span><b>([^<]+)</b></span>', row)
            if not key_match:
                continue
            key = key_match.group(1).strip()
            
            # ดึง value - get all TDs and use the second one
            tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(tds) < 2:
                continue
            value = re.sub(r'<[^>]+>', '', tds[1]).strip()
            value = ' '.join(value.split())
            
            if not value:
                continue
                
            if 'สาระสำคัญ' in key:
                result["summary"] = value
            elif 'ผู้ที่เกี่ยวข้อง' in key:
                result["applies_to"] = value
            elif 'วันที่มีผลบังคับ' in key:
                result["effective_date"] = value
            elif 'วันที่ประกาศ' in key or 'วันประกาศ' in key:
                result["gazette_date"] = value
        
        # หา PDF link จาก table - มักจะอยู่ในปุ่มหรือ link
        pdf_pattern = r'href=["\']([^"\']*(?:ratchakitcha|documents)[^"\']*\.pdf[^"\']*)["\']'
        pdf_match = re.search(pdf_pattern, table_html, re.IGNORECASE)
        if pdf_match:
            result["pdf_url"] = pdf_match.group(1)
    
    # หา PDF link ที่ไหนสักแห่งในหน้า
    if "pdf_url" not in result:
        pdf_pattern = r'href=["\']([^"\']*ratchakitcha[^"\']*\.pdf[^"\']*)["\']'
        pdf_match = re.search(pdf_pattern, html)
        if pdf_match:
            result["pdf_url"] = pdf_match.group(1)
    
    # หา link อ้างอิง
    if "source_url" not in result:
        ref_pattern = r'href=["\']([^"\']*\?page_id=2375&id=\d+[^"\']*)["\']'
        ref_match = re.search(ref_pattern, html)
        if ref_match:
            result["source_url"] = SOURCE_CONFIG["base_url"] + ref_match.group(1)
    
    return result

# ============================================================
# ฟังก์ชันหลัก - รันบุญมา
# ============================================================
def run_boonma():
    """ฟังก์ชันหลัก - ดึงกฎหมายจาก สลค. ไม่ต้องใช้ Token"""
    print("=" * 60)
    print("📡 บุญมาเริ่มทำงาน - ดึงข้อมูลกฎหมายจาก สลค.")
    print("=" * 60)
    
    # ดึงหน้ารายการ
    print("\n📋 ดึงหน้ารายการกฎหมาย...")
    html = fetch_html(SOURCE_CONFIG["list_page"])
    if not html:
        print("❌ ไม่สามารถดึงหน้าเว็บได้")
        return {"status": "error", "message": "Cannot fetch page"}
    
    # ดึงกฎหมายทั้งหมด
    laws_by_year = extract_laws_from_html(html)
    
    total_laws = sum(len(laws) for laws in laws_by_year.values())
    print(f"✅ พบกฎหมายทั้งหมด {total_laws} ฉบับ")
    
    for year in sorted(laws_by_year.keys(), reverse=True):
        print(f"   ปี {year+543} (พ.ศ.): {len(laws_by_year[year])} ฉบับ")
    
    # ใช้ปีล่าสุดที่มีข้อมูล
    if not laws_by_year:
        print("❌ ไม่พบข้อมูลกฎหมาย")
        return {"status": "no_data"}
    
    # เลือกปีล่าสุด (ปี ค.ศ. สูงสุด)
    latest_year = max(laws_by_year.keys())
    latest_laws = laws_by_year[latest_year]
    print(f"\n📌 เลือกปีล่าสุด: พ.ศ. {latest_year + 543} ({len(latest_laws)} ฉบับ)")
    
    # ดึงรายละเอียดแต่ละฉบับ
    detailed_laws = []
    fetched_at = datetime.now().isoformat()
    
    print("\n📄 ดึงรายละเอียดแต่ละฉบับ...")
    for i, law in enumerate(latest_laws):
        print(f"  [{i+1}/{len(latest_laws)}] {law['title'][:50]}...")
        
        detail_html = fetch_html(law["detail_url"])
        if detail_html:
            detail = get_law_detail(detail_html, law)
            detailed_laws.append(detail)
        else:
            detailed_laws.append(law)
        
        time.sleep(0.2)  # รอบ้างไม่ให้เร็วเกิน
    
    # เพิ่มข้อมูลเวลา
    for law in detailed_laws:
        law["fetched_at"] = fetched_at
        law["source"] = "soc_gov_th"
        law["source_name"] = SOURCE_CONFIG["name"]
        law["url"] = SOURCE_CONFIG["base_url"] + SOURCE_CONFIG["list_page"]
    
    # สร้างผลลัพธ์
    findings = {
        "agent": "บุญมา (BoonMa)",
        "role": "นักหาข้อมูลกฎหมาย",
        "run_at": fetched_at,
        "source": SOURCE_CONFIG,
        "total_laws": len(detailed_laws),
        "year": latest_year + 543,
        "findings": detailed_laws,
        "status": "success" if detailed_laws else "no_data",
    }
    
    # บันทึก
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ บุญมาเสร็จสิ้น - ได้ {len(detailed_laws)} ฉบับ")
    print(f"📁 บันทึกที่: {OUTPUT_FILE}")
    
    return findings

# ============================================================
# Test ดึงข้อมูล
# ============================================================
if __name__ == "__main__":
    result = run_boonma()
    
    if result.get("findings"):
        print(f"\n📋 ตัวอย่าง 3 ฉบับแรก:")
        for law in result["findings"][:3]:
            print(f"\n  [{law['id']}] {law.get('title', 'N/A')[:70]}")
            if "summary" in law:
                print(f"     สาระ: {law['summary'][:100]}...")
            if "applies_to" in law:
                print(f"     ผู้เกี่ยวข้อง: {law['applies_to'][:60]}...")
            if "effective_date" in law:
                print(f"     มีผล: {law['effective_date']}")
            if "pdf_url" in law:
                print(f"     PDF: {law['pdf_url'][:80]}")
    else:
        print("\n⚠️ ไม่พบข้อมูล ลองตรวจสอบการเชื่อมต่ออินเทอร์เน็ต")
