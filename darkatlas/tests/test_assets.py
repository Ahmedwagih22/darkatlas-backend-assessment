from tests.conftest import HEADERS


def test_create_asset(client):
    res = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "example.com", "source": "manual"
    }, headers=HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["value"] == "example.com"
    assert data["type"] == "domain"


def test_create_asset_requires_auth(client):
    res = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "example.com"
    })
    assert res.status_code == 401


def test_get_asset(client):
    create = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "test.com", "source": "manual"
    }, headers=HEADERS)
    asset_id = create.json()["id"]

    res = client.get(f"/api/v1/assets/{asset_id}")
    assert res.status_code == 200
    assert res.json()["id"] == asset_id


def test_list_assets_pagination(client):
    for i in range(5):
        client.post("/api/v1/assets/", json={
            "type": "domain", "value": f"domain{i}.com", "source": "manual"
        }, headers=HEADERS)

    res = client.get("/api/v1/assets/?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_list_filter_by_type(client):
    client.post("/api/v1/assets/", json={"type": "domain", "value": "a.com", "source": "manual"}, headers=HEADERS)
    client.post("/api/v1/assets/", json={"type": "ip_address", "value": "1.2.3.4", "source": "manual"}, headers=HEADERS)

    res = client.get("/api/v1/assets/?type=domain")
    assert all(a["type"] == "domain" for a in res.json()["items"])


def test_update_asset(client):
    create = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "update.com", "source": "manual"
    }, headers=HEADERS)
    asset_id = create.json()["id"]

    res = client.patch(f"/api/v1/assets/{asset_id}", json={"tags": ["prod"]}, headers=HEADERS)
    assert res.status_code == 200
    assert "prod" in res.json()["tags"]


def test_mark_stale(client):
    create = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "stale.com", "source": "manual"
    }, headers=HEADERS)
    asset_id = create.json()["id"]

    res = client.post(f"/api/v1/assets/{asset_id}/stale", headers=HEADERS)
    assert res.status_code == 200
    assert res.json()["status"] == "stale"


def test_delete_asset(client):
    create = client.post("/api/v1/assets/", json={
        "type": "domain", "value": "del.com", "source": "manual"
    }, headers=HEADERS)
    asset_id = create.json()["id"]

    res = client.delete(f"/api/v1/assets/{asset_id}", headers=HEADERS)
    assert res.status_code == 204

    res = client.get(f"/api/v1/assets/{asset_id}")
    assert res.status_code == 404
