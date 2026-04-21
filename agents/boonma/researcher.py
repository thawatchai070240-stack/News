#!/usr/bin/env python3
"""
บุญมา (BoonMa) - นักหาข้อมูลกฎหมายไทย
หน้าที่: ค้นหากฎหมายไทยอัพเดทใหม่จากแหล่งที่เข้าถึงได้

แหล่งข้อมูลที่ยืนยันว่าใช้ได้:
1. rd.go.th/rss.xml - กรมสรรพากร (30 รายการ ภาษี/ระเบียบ)
2. thaigov.go.th/sitemap.xml - เว็บรัฐบาลไทย (53 หน้า)
3. thaigov.go.th/news/{politics,economy,region} - ข่าวรัฐบาล
4. ฐานข้อมูลกฎหมายอื่นๆ ที่เข้าถึงได้
"""

import json
import sys
import re
import gzip
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from xml.etree.ElementTree import fromstring

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.helpers import save_json, generate_id

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "boonma_findings.json"

# ============================================================
# แหล่งข้อมูลที่รองรับ (เฉพาะที่ยืนยันว่าเข้าถึงได้)
# ============================================================
RSS_FEEDS = [
    {
        "key": "rd_rss",
        "name": "กรมสรรพากร",
        "url": "https://www.rd.go.th/rss.xml",
        "base_url": "https://www.rd.go.th",
        "type": "tax_regulation",
        "description": "ประกาศระเบียบภาษี กำหนดยื่นแบบ ข่าวสรรพากร"
    },
]

SITEMAP_SOURCES = [
    {
        "key": "thaigov_sitemap",
        "name": "เว็บรัฐบาลไทย - Sitemap",
        "url": "https://www.thaigov.go.th/sitemap.xml",
        "base_url": "https://www.thaigov.go.th",
        "type": "government_policy",
        "description": "แผนงาน นโยบายรัฐบาล จากเว็บรัฐบาลไทย"
    },
]

HTML_NEWS_SOURCES = [
    {
        "key": "thaigov_news",
        "name": "ข่าวรัฐบาลไทย",
        "url": "https://www.thaigov.go.th/th/news",
        "base_url": "https://www.thaigov.go.th",
        "type": "government_news",
        "description": "ข่าวจากเว็บรัฐบาลไทย"
    },
]


def fetch_url(url, timeout=15):
    """ดึงข้อมูลจาก URL พร้อมรองรับ gzip"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'th,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            status = resp.status
            ct = resp.headers.get('Content-Type', '')
            ce = resp.headers.get('Content-Encoding', '')
            content = resp.read()
            
            # Decompress if needed
            if ce == 'gzip' or (content[:2] == b'\x1f\x8b'):
                content = gzip.decompress(content)
            
            # Decode
            if isinstance(content, bytes):
                charset = 'utf-8'
                if 'charset=' in ct:
                    charset = ct.split('charset=')[-1].split(';')[0].strip()
                try:
                    text = content.decode(charset)
                except:
                    text = content.decode('utf-8', errors='replace')
            else:
                text = content
            
            return {
                "status_code": status,
                "content_type": ct,
                "content_length": len(content),
                "text": text,  # ไม่ truncate เพราะ XML ต้อง parse เต็ม
                "text_preview": text[:500],
                "accessible": True,
                "error": None
            }
    except HTTPError as e:
        return {"accessible": False, "error": f"HTTP {e.code}", "status_code": e.code, "content_length": 0}
    except URLError as e:
        return {"accessible": False, "error": str(e.reason)[:50], "status_code": 0, "content_length": 0}
    except Exception as e:
        return {"accessible": False, "error": str(e)[:80], "status_code": 0, "content_length": 0}


def parse_rss_feed(url, base_url, source_key, source_name, source_type, description):
    """ดึงข้อมูลจาก RSS Feed"""
    results = []
    data = fetch_url(url)
    
    if not data["accessible"]:
        return [{
            "id": generate_id(),
            "source": source_key,
            "source_name": source_name,
            "url": url,
            "status": "error",
            "error": data.get("error", "unknown"),
            "fetched_at": datetime.now().isoformat()
        }]
    
    try:
        text = data["text"]
        if not text.strip().startswith('<?xml') and not text.strip().startswith('<rss'):
            # Not RSS - might be HTML redirect
            return [{
                "id": generate_id(),
                "source": source_key,
                "source_name": source_name,
                "url": url,
                "status": "error",
                "error": "Not an RSS feed",
                "fetched_at": datetime.now().isoformat()
            }]
        
        root = fromstring(text.encode() if isinstance(text, str) else text)
        
        # Handle RSS 2.0
        items = root.findall('.//item')
        if not items:
            # Handle Atom
            items = root.findall('.//entry')
        
        for item in items:
            title = item.find('title')
            link = item.find('link')
            desc = item.find('description') or item.find('summary') or item.find('content')
            pubdate = item.find('pubDate') or item.find('published') or item.find('updated')
            
            title_text = title.text.strip() if title is not None and title.text else ""
            link_text = link.text if link is not None and link.text else ""
            
            # Handle relative links
            if link_text.startswith('/'):
                link_text = base_url + link_text
            elif link_text and not link_text.startswith('http'):
                link_text = base_url + '/' + link_text
            
            desc_text = desc.text[:200] if desc is not None and desc.text else ""
            pubdate_text = pubdate.text if pubdate is not None and pubdate.text else ""
            
            if title_text:
                results.append({
                    "id": generate_id(),
                    "source": source_key,
                    "source_name": source_name,
                    "title": title_text,
                    "url": link_text or url,
                    "summary": desc_text,
                    "published": pubdate_text,
                    "status": "found",
                    "type": source_type,
                    "description": description,
                    "fetched_at": datetime.now().isoformat(),
                    "content_length": data.get("content_length", 0)
                })
        
    except Exception as e:
        return [{
            "id": generate_id(),
            "source": source_key,
            "source_name": source_name,
            "url": url,
            "status": "error",
            "error": f"Parse error: {str(e)[:50]}",
            "fetched_at": datetime.now().isoformat()
        }]
    
    return results


def parse_sitemap(url, base_url, source_key, source_name, source_type, description):
    """ดึงข้อมูลจาก Sitemap XML"""
    results = []
    data = fetch_url(url)
    
    if not data["accessible"]:
        return [{
            "id": generate_id(),
            "source": source_key,
            "source_name": source_name,
            "url": url,
            "status": "error",
            "error": data.get("error", "unknown"),
            "fetched_at": datetime.now().isoformat()
        }]
    
    try:
        text = data["text"]
        root = fromstring(text.encode() if isinstance(text, str) else text)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        urls = root.findall('sm:url', ns)
        if not urls:
            urls = root.findall('url')
        
        for u in urls:
            loc = u.find('sm:loc', ns) or u.find('loc')
            lastmod = u.find('sm:lastmod', ns) or u.find('lastmod')
            
            if loc is not None and loc.text:
                url_text = loc.text.strip()
                lastmod_text = lastmod.text if lastmod is not None else ""
                
                results.append({
                    "id": generate_id(),
                    "source": source_key,
                    "source_name": source_name,
                    "title": f"หน้า: {url_text.split('/')[-1][:50]}",
                    "url": url_text,
                    "lastmod": lastmod_text,
                    "status": "found",
                    "type": source_type,
                    "description": description,
                    "fetched_at": datetime.now().isoformat(),
                    "content_length": data.get("content_length", 0)
                })
        
    except Exception as e:
        return [{
            "id": generate_id(),
            "source": source_key,
            "source_name": source_name,
            "url": url,
            "status": "error",
            "error": f"Sitemap parse error: {str(e)[:50]}",
            "fetched_at": datetime.now().isoformat()
        }]
    
    return results


def parse_html_news(url, base_url, source_key, source_name, source_type, description):
    """ดึงข่าวจาก HTML page (heuristic extraction)"""
    results = []
    data = fetch_url(url)
    
    if not data["accessible"]:
        return [{
            "id": generate_id(),
            "source": source_key,
            "source_name": source_name,
            "url": url,
            "status": "error",
            "error": data.get("error", "unknown"),
            "fetched_at": datetime.now().isoformat()
        }]
    
    text = data.get("text", "")
    
    # Extract links with news keywords - ใช้ text_preview ที่ truncate แล้วสำหรับ HTML
    text_for_extract = data.get("text_preview", text[:10000])
    patterns = [
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*<[^>]+>\s*([^<]*(?:ประกาศ|พระราชกำหนด|ระเบียบ|กฎหมาย|ข่าว|แถลง)[^<]*)\s*</a>',
        r'<h[234][^>]*>\s*<a[^>]+href=["\']([^"\']+)["\'][^>]*>\s*([^<]{15,100})\s*</a>',
        r'<a[^>]+href=["\']([^"\']*(?:news|ข่าว|announce)[^"\']*)["\'][^>]*>\s*([^<]{15,100})\s*</a>',
    ]
    
    seen_urls = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text_for_extract, re.IGNORECASE):
            link = m.group(1).strip()
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            
            if title and len(title) > 10 and link not in seen_urls:
                seen_urls.add(link)
                
                # Make absolute URL
                if link.startswith('/'):
                    link = base_url.rstrip('/') + link
                elif not link.startswith('http'):
                    link = base_url.rstrip('/') + '/' + link
                
                results.append({
                    "id": generate_id(),
                    "source": source_key,
                    "source_name": source_name,
                    "title": title,
                    "url": link,
                    "status": "found",
                    "type": source_type,
                    "description": description,
                    "fetched_at": datetime.now().isoformat(),
                    "content_length": data.get("content_length", 0)
                })
    
    return results


def run_research():
    """ฟังก์ชันหลัก"""
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
    
    total_found = 0
    total_errors = 0
    
    # 1. RSS Feeds (แหล่งที่ใช้ได้ดีที่สุด)
    print("\n📋 [1] ดึงข้อมูลจาก RSS Feeds...")
    for src in RSS_FEEDS:
        print(f"  ▶ {src['name']} ({src['url'][:50]})", end=" ... ")
        findings = parse_rss_feed(
            src['url'], src['base_url'],
            src['key'], src['name'], src['type'], src['description']
        )
        found = sum(1 for f in findings if f.get("status") == "found")
        errors = sum(1 for f in findings if f.get("status") == "error")
        print(f"{'✅ ' + str(found) + ' รายการ' if found else '❌ ' + str(errors) + ' error(s)'}")
        all_results["findings"].extend(findings)
        total_found += found
        total_errors += errors
        all_results["sources_checked"].append(src['key'])
    
    # 2. Sitemap Sources
    print("\n📋 [2] ดึงข้อมูลจาก Sitemaps...")
    for src in SITEMAP_SOURCES:
        print(f"  ▶ {src['name']} ({src['url'][:50]})", end=" ... ")
        findings = parse_sitemap(
            src['url'], src['base_url'],
            src['key'], src['name'], src['type'], src['description']
        )
        found = sum(1 for f in findings if f.get("status") == "found")
        print(f"{'✅ ' + str(found) + ' หน้า' if found else '❌ ไม่พบ'}")
        all_results["findings"].extend(findings)
        total_found += found
        all_results["sources_checked"].append(src['key'])
    
    # 3. HTML News Sources (fallback - อาจเจอ JS-rendered content)
    print("\n📋 [3] ดึงข้อมูลจาก HTML News Pages...")
    for src in HTML_NEWS_SOURCES:
        print(f"  ▶ {src['name']} ({src['url'][:50]})", end=" ... ")
        findings = parse_html_news(
            src['url'], src['base_url'],
            src['key'], src['name'], src['type'], src['description']
        )
        found = sum(1 for f in findings if f.get("status") == "found")
        print(f"{'✅ ' + str(found) + ' รายการ' if found else '⚠️ 0 (อาจเป็น JavaScript)'}")
        all_results["findings"].extend(findings)
        total_found += found
        all_results["sources_checked"].append(src['key'])
    
    # บันทึกผลลัพธ์
    save_json(all_results, OUTPUT_FILE)
    print(f"\n💾 บันทึกข้อมูลที่: {OUTPUT_FILE}")
    
    accessible = [f for f in all_results["findings"] if f.get("status") == "found"]
    errors = [f for f in all_results["findings"] if f.get("status") == "error"]
    
    print(f"\n📊 สรุป: พบ {total_found} รายการจาก {len(accessible)} แหล่ง")
    print(f"   ✅ เข้าถึงได้: {len(accessible)} แหล่ง")
    print(f"   ❌ บล็อค/error: {len(errors)} แหล่ง")
    
    if accessible:
        print(f"\n📰 ตัวอย่างข่าวที่พบ:")
        for item in accessible[:5]:
            print(f"   • {item.get('title', '')[:60]}")
            print(f"     จาก: {item.get('source_name', '')}")
            print(f"     URL: {item.get('url', '')[:60]}")
    
    return all_results


if __name__ == "__main__":
    result = run_research()
    sys.exit(0 if result["status"] == "success" else 1)
