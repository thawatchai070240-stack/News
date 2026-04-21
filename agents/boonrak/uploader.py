#!/usr/bin/env python3
"""
บุญรัก (BoonRak) - คนส่งหนังสือพิมพ์
หน้าที่: อัพโหลด HTML ขึ้น GitHub + Enable GitHub Pages + Deploy
"""

import json
import os
import sys
import base64
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
GITHUB_REPO = "thawatchai070240-stack/News"
GITHUB_BRANCH = "main"

def run_uploader():
    """ฟังก์ชันหลัก - อัพโหลดขึ้น GitHub"""
    print("=" * 60)
    print("📦 บุญรักเริ่มทำงาน - อัพโหลดขึ้น GitHub")
    print("=" * 60)
    
    # ตรวจสอบว่ามีไฟล์ HTML หรือไม่
    html_file = OUTPUT_DIR / "index.html"
    if not html_file.exists():
        print(f"⚠️ ไม่พบไฟล์: {html_file}")
        print("   กรุณาให้โรงพิมพ์บุญมีทำงานก่อน")
        return {"status": "no_html", "url": None}
    
    print(f"\n📄 พบไฟล์: {html_file}")
    
    # อ่าน GitHub Token
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if not github_token:
        print("❌ ไม่พบ GITHUB_TOKEN ใน Environment")
        return {"status": "no_token", "url": None}
    
    print(f"🔑 Token: {github_token[:10]}...{github_token[-5:]}")
    
    # อ่านเนื้อหา HTML
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    print(f"📝 ขนาดไฟล์: {len(html_content):,} bytes")
    
    # === Step 1: Get current commit SHA of main branch ===
    print("\n📡 กำลังเชื่อมต่อ GitHub API...")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # ตรวจสอบว่ามีไฟล์ index.html อยู่แล้วหรือไม่
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html",
        headers=headers
    )
    
    existing_sha = None
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        existing_sha = data.get("sha")
        print(f"  📁 พบไฟล์เดิม (SHA: {existing_sha[:7]})")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  🆕 ไฟล์ใหม่ (ยังไม่มีบน GitHub)")
        else:
            print(f"  ❌ HTTP Error: {e.code}")
            return {"status": "api_error", "error": f"HTTP {e.code}"}
    
    # === Step 2: Upload/Update index.html ===
    print("\n📤 กำลังอัพโหลด index.html...")
    
    content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    
    upload_data = {
        "message": f"Update: ข่าวกฎหมายไทย ณ {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content_b64,
        "branch": GITHUB_BRANCH
    }
    if existing_sha:
        upload_data["sha"] = existing_sha
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html",
        data=json.dumps(upload_data).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="PUT"
    )
    
    try:
        resp = urllib.request.urlopen(req)
        result_data = json.loads(resp.read())
        commit_sha = result_data.get("commit", {}).get("sha", "")[:7]
        print(f"  ✅ อัพโหลดสำเร็จ! (Commit: {commit_sha})")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ❌ อัพโหลดล้มเหลว: {e.code}")
        print(f"     {error_body[:200]}")
        return {"status": "upload_failed", "error": f"HTTP {e.code}"}
    
    # === Step 3: Create GitHub Actions workflow for Pages ===
    print("\n⚙️ กำลังสร้าง GitHub Actions workflow...")
    
    workflow_content = '''name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Pages
        uses: actions/configure-pages@v4
        
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
          
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
'''
    
    workflow_b64 = base64.b64encode(workflow_content.encode("utf-8")).decode("utf-8")
    workflow_data = {
        "message": "Add GitHub Pages workflow",
        "content": workflow_b64,
        "branch": GITHUB_BRANCH
    }
    
    # ตรวจสอบว่ามี workflow อยู่แล้วหรือไม่
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/.github/workflows/deploy.yml",
        headers=headers
    )
    existing_workflow_sha = None
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        existing_workflow_sha = data.get("sha")
    except urllib.error.HTTPError:
        pass
    
    if existing_workflow_sha:
        workflow_data["sha"] = existing_workflow_sha
    
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/.github/workflows/deploy.yml",
        data=json.dumps(workflow_data).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="PUT"
    )
    
    try:
        resp = urllib.request.urlopen(req)
        print("  ✅ Workflow สร้างสำเร็จ!")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # สร้างโฟลเดอร์ก่อน
            mkdir_data = {
                "message": "Create .github/workflows directory",
                "content": "",
                "branch": GITHUB_BRANCH
            }
            req_mkdir = urllib.request.Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/.github",
                data=json.dumps(mkdir_data).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method="PUT"
            )
            try:
                urllib.request.urlopen(req_mkdir)
            except:
                pass
            
            req = urllib.request.Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/.github/workflows/deploy.yml",
                data=json.dumps(workflow_data).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"},
                method="PUT"
            )
            urllib.request.urlopen(req)
            print("  ✅ Workflow สร้างสำเร็จ!")
        else:
            print(f"  ⚠️ Workflow สร้างไม่สำเร็จ: {e.code}")
    
    # === Step 4: Trigger workflow dispatch ===
    print("\n🚀 กำลัง trigger Deploy workflow...")
    
    workflow_req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/deploy.yml/dispatches",
        data=json.dumps({"ref": GITHUB_BRANCH}).encode("utf-8"),
        headers={**headers, "Content-Type": "application/vnd.github.v3+json"},
        method="POST"
    )
    
    try:
        urllib.request.urlopen(workflow_req)
        print("  ✅ Deploy workflow ทำงานแล้ว!")
    except urllib.error.HTTPError as e:
        if e.code == 204:
            print("  ✅ Deploy workflow ทำงานแล้ว!")
        else:
            print(f"  ⚠️ Trigger workflow: {e.code}")
    
    # รอสักครู่แล้วตรวจสอบ Pages URL
    print("\n⏳ รอ GitHub Pages สร้างลิงก์...")
    import time
    time.sleep(3)
    
    pages_url = f"https://thawatchai070240-stack.github.io/News/"
    
    result = {
        "status": "success",
        "url": pages_url,
        "repo": GITHUB_REPO,
        "deployed_at": datetime.now().isoformat()
    }
    
    print(f"\n{'='*60}")
    print("🎉 บุญรักทำงานสำเร็จ!")
    print(f"🌐 เว็บไซต์: {pages_url}")
    print(f"⏰ Deploy เมื่อ: {result['deployed_at']}")
    print(f"{'='*60}")
    
    return result

if __name__ == "__main__":
    result = run_uploader()
    sys.exit(0 if result["status"] == "success" else 1)
