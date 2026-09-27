# Nifty 100 Analytics & Screener

A comprehensive Nifty 100 stock screener and analytics platform with peer comparison, valuation analysis, and interactive dashboard.

## 📊 Project Overview

This project provides:

- **Nifty 100 Financial Database** - Complete financial data for all 92 companies
- **6 Investment Presets** - Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch
- **Composite Quality Score** - 0-100 scoring based on profitability, cash quality, growth, and leverage
- **Peer Percentile Analysis** - Compare companies within their peer groups
- **Radar Visualization** - Visual peer comparison charts
- **Interactive Dashboard** - 8-screen Streamlit dashboard
- **Valuation Module** - FCF yield, P/E flags, overvaluation/discount labels

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd nifty100_project

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt