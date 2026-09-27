"""
src/analytics/valuation.py
Valuation Module - FCF Yield, P/E flags, overvaluation/discount labels
"""

import os  # <-- ADD THIS
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = "nifty100.db"
OUTPUT_DIR = Path("output")