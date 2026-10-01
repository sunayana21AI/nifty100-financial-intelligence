import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestCompaniesList:
    def test_list_returns_200(self):
        assert client.get("/api/v1/companies").status_code == 200

    def test_list_returns_92(self):
        assert len(client.get("/api/v1/companies").json()) == 92

    def test_list_has_expected_fields(self):
        first = client.get("/api/v1/companies").json()[0]
        assert "company_id" in first
        assert "company_name" in first

    def test_filter_by_sector(self):
        data = client.get("/api/v1/companies?sector=Financials").json()
        for row in data:
            assert row["sector"] == "Financials"

    def test_search_filter(self):
        data = client.get("/api/v1/companies?search=TCS").json()
        tickers = [r["company_id"] for r in data]
        assert "TCS" in tickers


class TestCompanyDetail:
    def test_tcs_exists(self):
        assert client.get("/api/v1/companies/TCS").status_code == 200

    def test_tcs_correct(self):
        r = client.get("/api/v1/companies/TCS")
        assert "Tata Consultancy" in r.json()["company_name"]

    def test_invalid_ticker_returns_404(self):
        assert client.get("/api/v1/companies/INVALID_XYZ").status_code == 404


class TestCompanyRatios:
    def test_tcs_ratios(self):
        r = client.get("/api/v1/companies/TCS/ratios")
        assert r.status_code == 200
        assert len(r.json()) >= 10

    def test_tcs_ratios_year_filter(self):
        r = client.get("/api/v1/companies/TCS/ratios?year=2024")
        assert r.status_code == 200