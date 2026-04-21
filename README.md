# 📰 สำนักข่าวบุญมา - AI News Agency

> ระบบ AI Agents 6 ตัว สำหรับสร้างเว็บข่าวกฎหมายไทยอัตโนมัติ

## 🎯 ทีม AI Agents

| ชื่อ | หน้าที่ | คำอธิบาย |
|------|---------|----------|
| 📡 **บุญมา** | นักหาข้อมูล | ค้นหากฎหมายไทยอัพเดทจากราชกิจจานุเบกษาและแหล่งที่น่าเชื่อถือ |
| ✍️ **บุญส่ง** | นักเขียนข่าว | สรุปและเขียนข่าวสไตล์นักข่าว พาดหัวดึงดูด |
| 🔎 **บุญตรวจ** | นักตรวจข้อเท็จจริง | ตรวจสอบความถูกต้องของข้อมูลและแหล่งอ้างอิง |
| 📐 **บกลายจุด** | บรรณาธิการ | ออกแบบ HTML Template หลัก |
| 🖨️ **โรงพิมพ์บุญมี** | ตีพิมพ์ HTML | แปลงข้อมูลเป็น Interactive HTML |
| 📦 **บุญรัก** | คนส่งหนังสือพิมพ์ | อัพโหลดขึ้น GitHub + Deploy GitHub Pages |

## 🚀 วิธีใช้งาน

### รันทั้งหมด
```bash
cd /home/thawatchai200/news-agency
export GITHUB_TOKEN="your_github_pat_here"
python3 run_news_agency.py
```

### รันเฉพาะขั้นตอน
```bash
python3 run_news_agency.py --step 1    # รันเฉพาะบุญมา
python3 run_news_agency.py --step 2    # รันเฉพาะบุญส่ง
```

### รันเฉพาะ Agent
```bash
python3 run_news_agency.py --agent boonma     # บุญมา
python3 run_news_agency.py --agent boonsong    # บุญส่ง
python3 run_news_agency.py --agent boontrap   # บุญตรวจ
```

## ⏰ ตั้งเวลาอัพเดท day (Cron Job)

```bash
# เพิ่ม crontab
crontab -e

# รันทุกวัน 08:00 น.
0 8 * * * cd /home/thawatchai200/news-agency && export GITHUB_TOKEN="your_token" && bash scripts/daily-update.sh >> logs/cron.log 2>&1
```

## 🌐 ผลลัพธ์

เว็บไซต์จะถูก Deploy ที่: **https://thawatchai070240-stack.github.io/News/**

## 📁 โครงสร้างไฟล์

```
news-agency/
├── agents/
│   ├── boonma/          # บุญมา - นักหาข้อมูล
│   ├── boonsong/        # บุญส่ง - นักเขียนข่าว
│   ├── boontrap/        # บุญตรวจ - ตรวจข้อเท็จจริง
│   ├── boonsong/        # บุญส่ง
│   ├── roongpim/        # โรงพิมพ์บุญมี - ตีพิมพ์ HTML
│   ├── boonrak/         # บุญรัก - อัพโหลด GitHub
│   └── boklayjood/      # บกลายจุด - บรรณาธิการ
├── data/
│   ├── raw/             # ข้อมูลดิบจากบุญมา
│   ├── written/         # ข้อมูลที่เขียนแล้ว
│   └── verified/        # ข้อมูลที่ตรวจแล้ว
├── output/
│   └── index.html       # HTML ที่พร้อม deploy
├── scripts/
│   ├── daily-update.sh  # Cron script
│   └── github-deploy.sh # Deploy script
├── templates/
│   └── base.html        # HTML template หลัก
├── utils/
│   └── helpers.py       # Helper functions
├── run_news_agency.py   # Main runner
└── README.md
```

## 🔧 ต้องมี

- Python 3.8+
- GitHub PAT ที่มี scopes: `repo`, `workflow`, `pages`

## 📋 Workflow

```
1. บุญมา → ดึงข้อมูลกฎหมายจากราชกิจจานุเบกษา
2. บุญส่ง → เขียนข่าวสไตล์นักข่าว
3. บุญตรวจ → ตรวจสอบความถูกต้อง
4. บกลายจุด → สร้าง HTML Template
5. โรงพิมพ์บุญมี → สร้าง Interactive HTML
6. บุญรัก → ขึ้น GitHub + Deploy
```

## 📌 หมายเหตุ

- ตั้ง `GITHUB_TOKEN` environment variable ก่อนรัน
- GitHub Pages ต้อง Enable ใน repo settings หลังจากรันครั้งแรก
- ดู log ได้ที่ `logs/` directory
