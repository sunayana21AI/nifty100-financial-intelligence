# 📊 Dashboard Pages — Documentation

This folder contains the 8 Streamlit screens for the Nifty 100 Analytics dashboard.

Each file is a **standalone Streamlit script** — auto-detected by Streamlit's multipage system.

---

## 📁 Files in this folder

| File | Screen | Description |
|------|--------|-------------|
| `01_home.py` | 🏠 Home | Overall KPIs, sector donut, top composite scores |
| `02_profile.py` | 🏢 Company Profile | Search + KPIs + charts + pros/cons |
| `03_screener.py` | 🔎 Screener | Sliders, presets, CSV export |
| `04_peers.py` | 👥 Peer Comparison | Radar chart + comparison table |
| `05_trends.py` | 📈 Trend Analysis | Multi-metric 10-year trends |
| `06_sectors.py` | 🗂️ Sector Analysis | Bubble chart + median bar |
| `07_capital.py` | 💰 Capital Allocation | D/E pattern treemap |
| `08_reports.py` | 📄 Reports | Annual report PDF links |

---

## 🚀 How to Run

From **project root** (`nifty100_Project/`):

```bash
streamlit run src/dashboard/app.py