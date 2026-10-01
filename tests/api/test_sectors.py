import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestSectors:
    def test_list_returns_200(self):
        assert client.get("/api/v1/sectors").status_code == 200

    def test_list_has_sectors(self):
        data = client.get("/api/v1/sectors").json()
        assert len(data) >= 9

    def test_sector_has_company_count(self):
        first = client.get("/api/v1/sectors").json()[0]
        assert "sector" in first
        assert "company_count" in first


class TestSectorCompanies:
    def test_it_sector_companies(self):
        r = client.get("/api/v1/sectors/Information Technology/companies")
        assert r.status_code == 200
        assert len(r.json()) >= 5

    def test_unknown_sector_returns_404(self):
        r = client.get("/api/v1/sectors/UnknownSectorXYZ/companies")
        assert r.status_code == 404