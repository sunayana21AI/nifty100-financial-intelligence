import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self):
        assert client.get("/api/v1/health").status_code == 200

    def test_health_status_ok(self):
        assert client.get("/api/v1/health").json()["status"] == "ok"

    def test_health_has_db_counts(self):
        data = client.get("/api/v1/health").json()
        assert "db_row_counts" in data
        assert data["db_row_counts"]["companies"] == 92

    def test_health_has_uptime(self):
        assert "uptime_seconds" in client.get("/api/v1/health").json()

    def test_health_has_version(self):
        assert client.get("/api/v1/health").json()["version"] == "1.0.0"

    def test_health_all_tables_present(self):
        counts = client.get("/api/v1/health").json()["db_row_counts"]
        expected = ["companies", "financial_ratios", "profitandloss",
                    "balancesheet", "cashflow", "sectors", "peer_groups",
                    "peer_percentiles", "documents", "stock_prices"]
        for t in expected:
            assert t in counts