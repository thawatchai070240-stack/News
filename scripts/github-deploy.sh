#!/bin/bash
# =============================================================================
# github-deploy.sh - GitHub Upload & Deploy Script
# อัพโหลด index.html ขึ้น GitHub และ trigger GitHub Pages deploy
# =============================================================================

set -e

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="thawatchai070240-stack/News"
BRANCH="main"
HTML_FILE="output/index.html"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN not set"
    exit 1
fi

if [ ! -f "$HTML_FILE" ]; then
    echo "ERROR: $HTML_FILE not found"
    exit 1
fi

echo "📦 Uploading to GitHub..."
echo "   Repo: $GITHUB_REPO"
echo "   File: $HTML_FILE"

# อ่านไฟล์ HTML
HTML_CONTENT=$(cat "$HTML_FILE")
CONTENT_B64=$(echo -n "$HTML_CONTENT" | base64 -w 0)

# ตรวจสอบว่ามีไฟล์อยู่แล้วหรือไม่
SHA=""
EXISTING=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$GITHUB_REPO/contents/$HTML_FILE")

if echo "$EXISTING" | grep -q "\"sha\""; then
    SHA=$(echo "$EXISTING" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sha',''))")
    echo "📁 File exists, will update (SHA: ${SHA:0:7})"
fi

# อัพโหลด
PAYLOAD=$(python3 -c "
import sys, json
data = {
    'message': 'Update news: $(date +%Y-%m-%d\ %H:%M)',
    'content': '''$CONTENT_B64''',
    'branch': '$BRANCH'
}
if '$SHA':
    data['sha'] = '$SHA'
print(json.dumps(data))
")

RESPONSE=$(curl -s -X PUT \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.github.com/repos/$GITHUB_REPO/contents/$HTML_FILE" \
    -d "$PAYLOAD")

if echo "$RESPONSE" | grep -q '"commit"'; then
    COMMIT=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['sha'][:7])")
    echo "✅ Uploaded successfully! Commit: $COMMIT"
    
    # Trigger Pages workflow
    echo "🚀 Triggering GitHub Pages deploy..."
    curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_REPO/actions/workflows/deploy.yml/dispatches" \
        -d '{"ref":"main"}' || true
    
    echo ""
    echo "🌐 News site: https://thawatchai070240-stack.github.io/News/"
else
    echo "❌ Upload failed:"
    echo "$RESPONSE"
    exit 1
fi
