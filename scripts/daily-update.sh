#!/bin/bash
# =============================================================================
# daily-update.sh - Daily News Agency Update Script
# สคริปต์หลักที่รันทุกวันเพื่ออัพเดทข่าว
# ทำงานตามลำดับ: บุญมา → บุญส่ง → บุญตรวจ → บกลายจุด → โรงพิมพ์บุญมี → บุญรัก
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENCY_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$AGENCY_DIR/logs"

# สร้าง logs directory
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/daily-update_$(date '+%Y%m%d').log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

log "============================================================"
log "🚀 Daily News Agency Update Started"
log "============================================================"

# ตรวจสอบ GitHub Token
if [ -z "$GITHUB_TOKEN" ]; then
    # ลองอ่านจาก .env
    if [ -f "$AGENCY_DIR/.env" ]; then
        source "$AGENCY_DIR/.env" 2>/dev/null || true
    fi
fi

if [ -z "$GITHUB_TOKEN" ]; then
    log "WARNING: GITHUB_TOKEN not set. บุญรักจะข้ามการอัพโหลด"
fi

# ตรวจสอบ Python
if ! command -v python3 &>/dev/null; then
    error "Python3 not found"
    exit 1
fi

log ""
log "📡 Step 1: บุญมา - นักหาข้อมูล"
log "-----------------------------------------------"
cd "$AGENCY_DIR"
python3 agents/boonma/researcher.py >> "$LOG_FILE" 2>&1 || error "บุญมา failed"
log ""

log "✍️ Step 2: บุญส่ง - นักเขียนข่าว"
log "-----------------------------------------------"
python3 agents/boonsong/writer.py >> "$LOG_FILE" 2>&1 || error "บุญส่ง failed"
log ""

log "🔎 Step 3: บุญตรวจ - นักตรวจข้อเท็จจริง"
log "-----------------------------------------------"
python3 agents/boontrap/factchecker.py >> "$LOG_FILE" 2>&1 || error "บุญตรวจ failed"
log ""

log "📐 Step 4: บกลายจุด - บรรณาธิการ"
log "-----------------------------------------------"
python3 agents/boklayjood/controller.py >> "$LOG_FILE" 2>&1 || error "บกลายจุด failed"
log ""

log "🖨️ Step 5: โรงพิมพ์บุญมี - ตีพิมพ์ HTML"
log "-----------------------------------------------"
python3 agents/roongpim/publisher.py >> "$LOG_FILE" 2>&1 || error "โรงพิมพ์บุญมี failed"
log ""

log "📦 Step 6: บุญรัก - อัพโหลด GitHub"
log "-----------------------------------------------"
if [ -n "$GITHUB_TOKEN" ]; then
    export GITHUB_TOKEN
    python3 agents/boonrak/uploader.py >> "$LOG_FILE" 2>&1 || error "บุญรัก failed"
else
    log "SKIPPED: GITHUB_TOKEN not set"
fi
log ""

log "============================================================"
log "✅ Daily Update Completed"
log "============================================================"
