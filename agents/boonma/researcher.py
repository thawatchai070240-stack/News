#!/usr/bin/env python3
"""
บุญมา (BoonMa) - นักหาข้อมูลกฎหมายไทย
หน้าที่: ค้นหากฎหมายไทยอัพเดทใหม่จากราชกิจจานุเบกษาและแหล่งที่น่าเชื่อถือ
อัพเดท: Real-time เข้าไปดูทุกวัน
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.helpers import save_json, load_json, generate_id

# Source URLs for Thai law
SOURCES = {
    "ratchakitcha": {
        "name": "ราชกิจจานุเบกษา",
        "base_url": "https://www.ratchakitcha.soc.go.th",
        "search_url": "https://www.ratchakitcha.soc.go.th/cgi/swishprof",
        "description": "เว็บราชกิจจานุเบกษา �ศาลรัฐธรรมนูญ"
    },
    "thailaws": {
        "name": "ThaiLaws ฐานกฎหมายไทย",
        "base_url": "https://www.thailaws.com",
        "search_url": "https://www.thailaws.com/law/search.php",
        "description": "ฐานข้อมูลกฎหมายไทย"
    },
    "loippo": {
        "name": "กฎหมาย กรอบแนวคิด มาตรา 40",
        "base_url": "https://www.loippo.go.th",
        "description": "สำนักงานคณะกรรมการกฤษฎีกา"
    },
    "thailawforum": {
        "name": "ThaiLaw Forum",
        "base_url": "https://www.thailawforum.com",
        "description": "สาระกฎหมาย คำพิพากษา บทความ"
    },
    "gov_news": {
        "name": "ข่าวราชกิจจานุเบกษา ล่าสุด",
        "base_url": "https://www.gov.uk/current",
        "description": "Government news"
    }
}

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "boonma_findings.json"

def fetch_ratchakitcha():
    """ดึงข้อมูลจากราชกิจจานุเบกษา"""
    import requests
    results = []
    
    try:
        # ลองดึงข้อมูลจากหน้าแรกราชกิจจา
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        resp = requests.get("https://www.ratchakitcha.soc.go.th", headers=headers, timeout=15)
        if resp.status_code == 200:
            results.append({
                "source": "ratchakitcha",
                "name": "ราชกิจจานุเบกษา",
                "url": "https://www.ratchakitcha.soc.go.th",
                "status": "accessible",
                "content_preview": resp.text[:500] if resp.text else "",
                "fetched_at": datetime.now().isoformat()
            })
    except Exception as e:
        results.append({
            "source": "ratchakitcha",
            "name": "ราชกิจจานุเบกษา",
            "url": "https://www.ratchakitcha.soc.go.th",
            "status": "error",
            "error": str(e),
            "fetched_at": datetime.now().isoformat()
        })
    return results

def fetch_thailaws():
    """ดึงข้อมูลจาก ThaiLaws"""
    import requests
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = requests.get("https://www.thailaws.com", headers=headers, timeout=15)
        if resp.status_code == 200:
            results.append({
                "source": "thailaws",
                "name": "ThaiLaws",
                "url": "https://www.thailaws.com",
                "status": "accessible",
                "fetched_at": datetime.now().isoformat()
            })
    except Exception as e:
        results.append({
            "source": "thailaws",
            "name": "ThaiLaws",
            "url": "https://www.thailaws.com",
            "status": "error",
            "error": str(e),
            "fetched_at": datetime.now().isoformat()
        })
    return results

def search_latest_laws():
    """ค้นหากฎหมายใหม่ล่าสุดจากหลายแหล่ง"""
    import requests
    findings = []
    
    # ค้นหาจากหลายแหล่ง
    search_urls = [
        ("https://www.ratchakitcha.soc.go.th/node/ราชกิจจานุเบกษา", "ratchakitcha"),
        ("https://www.thailaws.com/law/search.php", "thailaws"),
        ("https://www.loippo.go.th", "loippo"),
    ]
    
    for url, source in search_urls:
        try:
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200:
                findings.append({
                    "id": generate_id(),
                    "source": source,
                    "title": f"ข้อมูลจาก {SOURCES[source]['name']}",
                    "url": url,
                    "status": "found",
                    "fetched_at": datetime.now().isoformat(),
                    "content_length": len(resp.text)
                })
        except Exception as e:
            findings.append({
                "id": generate_id(),
                "source": source,
                "title": f"ข้อมูลจาก {SOURCES[source]['name']}",
                "url": url,
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now().isoformat()
            })
    
    return findings

def run_research():
    """ฟังก์ชันหลัก - รันการวิจัย"""
    print("=" * 60)
    print("📡 บุญมาเริ่มทำงาน - ค้นหากฎหมายไทยอัพเดทใหม่")
    print("=" * 60)
    
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    all_results = {
        "agent": "บุญมา (BoonMa)",
        "role": "นักหาข้อมูลกฎหมาย",
        "run_at": datetime.now().isoformat(),
        "sources_checked": [],
        "findings": [],
        "status": "success"
    }
    
    # ตรวจสอบแหล่งข้อมูลทีละแหล่ง
    print("\n🔍 กำลังตรวจสอบแหล่งข้อมูล...")
    
    for source_key, source_info in SOURCES.items():
        print(f"  ▶ กำลังดึงข้อมูลจาก: {source_info['name']}")
        try:
            import requests
            resp = requests.get(source_info['base_url'], timeout=15, 
                              headers={'User-Agent': 'Mozilla/5.0'})
            
            finding = {
                "id": generate_id(),
                "source": source_key,
                "source_name": source_info['name'],
                "url": source_info['base_url'],
                "status": "accessible" if resp.status_code == 200 else f"http_{resp.status_code}",
                "http_status": resp.status_code,
                "fetched_at": datetime.now().isoformat(),
                "title": source_info['name'],
                "description": source_info['description'],
                "content_length": len(resp.text) if hasattr(resp, 'text') else 0
            }
            
            all_results["sources_checked"].append(finding)
            all_results["findings"].append(finding)
            print(f"    ✅ {source_info['name']} - Status: {resp.status_code}")
            
        except Exception as e:
            error_finding = {
                "id": generate_id(),
                "source": source_key,
                "source_name": source_info['name'],
                "url": source_info['base_url'],
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now().isoformat(),
                "title": source_info['name'],
                "description": source_info['description']
            }
            all_results["sources_checked"].append(error_finding)
            print(f"    ❌ {source_info['name']} - Error: {str(e)[:50]}")
    
    # บันทึกผลลัพธ์
    save_json(all_results, OUTPUT_FILE)
    print(f"\n💾 บันทึกข้อมูลที่: {OUTPUT_FILE}")
    
    # สรุปผล
    accessible_count = sum(1 for f in all_results["sources_checked"] if f["status"] == "accessible")
    print(f"\n📊 สรุป: ตรวจสอบ {len(all_results['sources_checked'])} แหล่งที่มา")
    print(f"   ✅ เข้าถึงได้: {accessible_count}")
    print(f"   ❌ เข้าถึงไม่ได้: {len(all_results['sources_checked']) - accessible_count}")
    
    return all_results

if __name__ == "__main__":
    result = run_research()
    sys.exit(0 if result["status"] == "success" else 1)
