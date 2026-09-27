import os
from datetime import datetime


LOG_PATH = "output/ratio_edge_cases.log"


def log_edge_case(company, issue, category, explanation):

    os.makedirs("output", exist_ok=True)

    with open(LOG_PATH, "a", encoding="utf-8") as f:

        f.write(
            f"""
Date: {datetime.now()}
Company: {company}
Issue: {issue}
Category: {category}
Explanation: {explanation}
------------------------------------
"""
        )