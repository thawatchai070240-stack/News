#!/usr/bin/env python3
"""
Utils Helper - ฟังก์ชันช่วยเหลือสำหรับ AI Agents
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

def generate_id():
    """สร้าง ID เฉพาะ"""
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

def save_json(data, filepath):
    """บันทึก JSON"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filepath):
    """โหลด JSON"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)

def timestamp():
    """สร้าง timestamp"""
    return datetime.now().isoformat()
