#!/usr/bin/env python3
"""
สำนักข่าวบุญมา - News Agency AI
รัน AI Agents ทั้ง 6 ตัวเพื่อสร้างเว็บข่าวกฎหมายไทย

Usage:
    python3 run_news_agency.py              # รันทั้งหมด
    python3 run_news_agency.py --step 1     # รันเฉพาะ step ที่ 1
    python3 run_news_agency.py --agent boonma  # รันเฉพาะ agent
"""

import sys
import os
from pathlib import Path
from datetime import datetime

AGENCY_DIR = Path(__file__).parent

def run_step1_boonma():
    """บุญมา - นักหาข้อมูล"""
    print("\n" + "="*60)
    print("📡 บุญมา - นักหาข้อมูลกฎหมาย")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "boonma"))
    from researcher import run_research
    return run_research()

def run_step2_boonsong():
    """บุญส่ง - นักเขียนข่าว"""
    print("\n" + "="*60)
    print("✍️ บุญส่ง - นักเขียนข่าว")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "boonsong"))
    from writer import run_writer
    return run_writer()

def run_step3_boontrap():
    """บุญตรวจ - นักตรวจข้อเท็จจริง"""
    print("\n" + "="*60)
    print("🔎 บุญตรวจ - นักตรวจข้อเท็จจริง")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "boontrap"))
    from factchecker import run_factchecker
    return run_factchecker()

def run_step4_boklayjood():
    """บกลายจุด - บรรณาธิการ"""
    print("\n" + "="*60)
    print("📐 บกลายจุด - บรรณาธิการ")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "boklayjood"))
    from controller import run_controller
    return run_controller()

def run_step5_roongpim():
    """โรงพิมพ์บุญมี - ตีพิมพ์ HTML"""
    print("\n" + "="*60)
    print("🖨️ โรงพิมพ์บุญมี - ตีพิมพ์ HTML")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "roongpim"))
    from publisher import run_publisher
    return run_publisher()

def run_step6_boonrak():
    """บุญรัก - อัพโหลด GitHub"""
    print("\n" + "="*60)
    print("📦 บุญรัก - อัพโหลด GitHub")
    print("="*60)
    sys.path.insert(0, str(AGENCY_DIR / "agents" / "boonrak"))
    from uploader import run_uploader
    os.environ["GITHUB_TOKEN"] = os.environ.get("GITHUB_TOKEN", os.environ.get("GITHUB_PAT", ""))
    return run_uploader()

def run_all():
    """รันทั้งหมด"""
    print("\n" + "="*60)
    print("🏢 สำนักข่าวบุญมา - AI News Agency")
    print("   รันทั้ง 6 ตัว: บุญมา → บุญส่ง → บุญตรวจ → บกลายจุด → โรงพิมพ์บุญมี → บุญรัก")
    print("="*60)
    print(f"🕐 เริ่มงาน: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    steps = [
        ("บุญมา (นักหาข้อมูล)", run_step1_boonma),
        ("บุญส่ง (นักเขียนข่าว)", run_step2_boonsong),
        ("บุญตรวจ (ตรวจข้อเท็จจริง)", run_step3_boontrap),
        ("บกลายจุด (บรรณาธิการ)", run_step4_boklayjood),
        ("โรงพิมพ์บุญมี (ตีพิมพ์ HTML)", run_step5_roongpim),
        ("บุญรัก (อัพโหลด GitHub)", run_step6_boonrak),
    ]
    
    results = []
    for name, func in steps:
        try:
            result = func()
            results.append((name, "✅ success", result.get("status", "")))
        except Exception as e:
            results.append((name, "❌ failed", str(e)[:80]))
    
    print("\n" + "="*60)
    print("📊 สรุปผลการทำงาน")
    print("="*60)
    for name, status, detail in results:
        print(f"  {status} {name}")
        if detail:
            print(f"         → {detail}")
    
    print(f"\n🕐 เสร็จสิ้น: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = sum(1 for _, s, _ in results if "✅" in s)
    print(f"\n🎉 สำเร็จ {success_count}/{len(results)} ขั้นตอน")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--step":
            step = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            steps = [
                run_step1_boonma,
                run_step2_boonsong,
                run_step3_boontrap,
                run_step4_boklayjood,
                run_step5_roongpim,
                run_step6_boonrak,
            ]
            if 1 <= step <= len(steps):
                steps[step-1]()
        elif sys.argv[1] == "--agent":
            agent = sys.argv[2] if len(sys.argv) > 2 else ""
            agents = {
                "boonma": run_step1_boonma,
                "boonsong": run_step2_boonsong,
                "boontrap": run_step3_boontrap,
                "boklayjood": run_step4_boklayjood,
                "roongpim": run_step5_roongpim,
                "boonrak": run_step6_boonrak,
            }
            if agent in agents:
                agents[agent]()
            else:
                print(f"Unknown agent: {agent}")
                print(f"Available: {', '.join(agents.keys())}")
    else:
        run_all()
