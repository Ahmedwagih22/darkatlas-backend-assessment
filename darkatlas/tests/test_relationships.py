from tests.conftest import HEADERS


def _create(client, type_, value):
    return client.post("/api/v1/assets/", json={"type": type_, "value": value, "source": "manual"}, headers=HEADERS).json()["id"]


def test_create_and_read_relationship(client):
    d = _create(client, "domain", "rel.com")
    s = _create(client, "subdomain", "www.rel.com")

    res = client.post("/api/v1/relationships/", json={"from_id": s, "to_id": d, "relation_type": "subdomain_of"}, headers=HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["relation_type"] == "subdomain_of"


def test_no_duplicate_relationships(client):
    d = _create(client, "domain", "dup.com")
    s = _create(client, "subdomain", "sub.dup.com")

    client.post("/api/v1/relationships/", json={"from_id": s, "to_id": d, "relation_type": "subdomain_of"}, headers=HEADERS)
    res = client.post("/api/v1/relationships/", json={"from_id": s, "to_id": d, "relation_type": "subdomain_of"}, headers=HEADERS)
    assert res.status_code == 409


def test_asset_graph(client):
    d = _create(client, "domain", "graph.com")
    s = _create(client, "subdomain", "api.graph.com")
    client.post("/api/v1/relationships/", json={"from_id": s, "to_id": d, "relation_type": "subdomain_of"}, headers=HEADERS)

    res = client.get(f"/api/v1/assets/{d}/graph")
    assert res.status_code == 200
    data = res.json()
    assert len(data["related"]) == 1
    assert data["related"][0]["relation_type"] == "subdomain_of"
