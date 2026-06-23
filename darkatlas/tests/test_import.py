from tests.conftest import HEADERS

SAMPLE = {
    "assets": [
        {"id": "a1", "type": "domain", "value": "example.com", "status": "active", "source": "scan", "tags": ["root"], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com", "status": "active", "source": "scan", "tags": ["prod"], "metadata": {}, "parent": "a1"},
        {"id": "a3", "type": "certificate", "value": "CN=api.example.com", "status": "active", "source": "scan", "tags": [], "metadata": {"issuer": "Let's Encrypt", "expires": "2025-01-02"}, "covers": "a2"},
    ]
}


def test_bulk_import(client):
    res = client.post("/api/v1/import/", json=SAMPLE, headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["created"] == 3
    assert data["failed"] == 0


def test_idempotent_import(client):
    client.post("/api/v1/import/", json=SAMPLE, headers=HEADERS)
    res = client.post("/api/v1/import/", json=SAMPLE, headers=HEADERS)
    data = res.json()
    # Second import: all updated, none created
    assert data["created"] == 0
    assert data["updated"] == 3

    # Total assets should still be 3
    list_res = client.get("/api/v1/assets/")
    assert list_res.json()["total"] == 3


def test_partial_failure_doesnt_crash(client):
    bad_data = {
        "assets": [
            {"id": "b1", "type": "domain", "value": "good.com", "source": "scan"},
            {"id": "b2", "type": "domain", "value": "", "source": "scan"},  # empty value → should fail
        ]
    }
    res = client.post("/api/v1/import/", json=bad_data, headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["created"] == 1
    assert data["failed"] == 1


def test_stale_asset_reactivated_on_reimport(client):
    # Create and mark stale
    create = client.post("/api/v1/assets/", json={"type": "domain", "value": "reappear.com", "source": "manual"}, headers=HEADERS)
    asset_id = create.json()["id"]
    client.post(f"/api/v1/assets/{asset_id}/stale", headers=HEADERS)

    # Re-import same asset
    client.post("/api/v1/import/", json={"assets": [{"type": "domain", "value": "reappear.com", "source": "scan"}]}, headers=HEADERS)

    res = client.get(f"/api/v1/assets/{asset_id}")
    assert res.json()["status"] == "active"
