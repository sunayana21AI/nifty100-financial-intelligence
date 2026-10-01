import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestScreener:
    def test_screener_returns_200(self):
        assert client.get("/api/v1/screener").status_code == 200

    def test_min_roe_filter(self):
        data = client.get("/api/v1/screener?min_roe=15").json()
        for row in data:
            assert row["roe"] >= 15

    def test_max_de_filter(self):
        data = client.get("/api/v1/screener?max_de=1.0").json()
        for row in data:
            assert row["debt_to_equity"] <= 1.0

    def test_combined_filters(self):
        r = client.get("/api/v1/screener?min_roe=15&max_de=2.0")
        assert r.status_code == 200

    def test_invalid_roe_returns_400(self):
        assert client.get("/api/v1/screener?min_roe=-500").status_code == 400

    def test_invalid_de_returns_400(self):
        assert client.get("/api/v1/screener?max_de=-1").status_code == 400

    def test_invalid_pe_returns_400(self):
        assert client.get("/api/v1/screener?max_pe=-5").status_code == 400