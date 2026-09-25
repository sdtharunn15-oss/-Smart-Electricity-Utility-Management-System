from datetime import date

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def tariff_payload():
    return {
        "connection_type": "Domestic",
        "slab_name": "0-100 Units",
        "min_units": 0,
        "max_units": 100,
        "rate_per_unit": 3.50,
        "fixed_charge": 50.00,
        "effective_from": "2026-01-01",
        "effective_to": None,
    }


def create_tariff():
    response = client.post(
        "/tariffs",
        json=tariff_payload(),
    )

    assert response.status_code == 201

    return response.json()


def test_create_tariff():
    response = client.post(
        "/tariffs",
        json=tariff_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["connection_type"] == "Domestic"
    assert data["slab_name"] == "0-100 Units"
    assert data["min_units"] == 0
    assert data["max_units"] == 100
    assert data["rate_per_unit"] == 3.50
    assert data["fixed_charge"] == 50.00
    assert data["effective_from"] == "2026-01-01"
    assert data["effective_to"] is None
    assert "created_at" in data


def test_get_tariff():
    tariff = create_tariff()

    tariff_id = tariff["id"]

    response = client.get(
        f"/tariffs/{tariff_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == tariff_id
    assert data["connection_type"] == "Domestic"
    assert data["slab_name"] == "0-100 Units"


def test_get_tariff_not_found():
    response = client.get(
        "/tariffs/99999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Tariff not found"


def test_list_tariffs():
    create_tariff()

    response = client.get(
        "/tariffs"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["connection_type"] == "Domestic"


def test_list_tariffs_by_connection_type():
    create_tariff()

    response = client.get(
        "/tariffs",
        params={
            "connection_type": "Domestic"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["connection_type"] == "Domestic"


def test_list_tariffs_wrong_connection_type():
    create_tariff()

    response = client.get(
        "/tariffs",
        params={
            "connection_type": "Industrial"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []


def test_list_tariffs_by_effective_date():
    create_tariff()

    response = client.get(
        "/tariffs",
        params={
            "effective_date": "2026-06-01"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1


def test_list_tariffs_before_effective_date():
    create_tariff()

    response = client.get(
        "/tariffs",
        params={
            "effective_date": "2025-12-01"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []


def test_create_tariff_invalid_dates():
    payload = tariff_payload()

    payload["effective_from"] = "2026-06-01"
    payload["effective_to"] = "2026-01-01"

    response = client.post(
        "/tariffs",
        json=payload,
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "effective_to cannot be before effective_from"
    )


def test_create_tariff_invalid_units():
    payload = tariff_payload()

    payload["min_units"] = 100
    payload["max_units"] = 50

    response = client.post(
        "/tariffs",
        json=payload,
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "max_units cannot be less than min_units"
    )


def test_create_duplicate_tariff():
    create_tariff()

    response = client.post(
        "/tariffs",
        json=tariff_payload(),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Duplicate tariff slab already exists"
    )


def test_update_tariff():
    tariff = create_tariff()

    tariff_id = tariff["id"]

    response = client.put(
        f"/tariffs/{tariff_id}",
        json={
            "connection_type": "Domestic",
            "slab_name": "Updated 0-100 Units",
            "min_units": 0,
            "max_units": 100,
            "rate_per_unit": 4.00,
            "fixed_charge": 75.00,
            "effective_from": "2026-01-01",
            "effective_to": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == tariff_id
    assert data["slab_name"] == "Updated 0-100 Units"
    assert data["rate_per_unit"] == 4.00
    assert data["fixed_charge"] == 75.00


def test_update_tariff_not_found():
    response = client.put(
        "/tariffs/99999",
        json={
            "slab_name": "Updated Tariff"
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Tariff not found"


def test_update_tariff_invalid_dates():
    tariff = create_tariff()

    tariff_id = tariff["id"]

    response = client.put(
        f"/tariffs/{tariff_id}",
        json={
            "effective_from": "2026-06-01",
            "effective_to": "2026-01-01",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "effective_to cannot be before effective_from"
    )


def test_update_tariff_invalid_units():
    tariff = create_tariff()

    tariff_id = tariff["id"]

    response = client.put(
        f"/tariffs/{tariff_id}",
        json={
            "min_units": 100,
            "max_units": 50,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "max_units cannot be less than min_units"
    )


def test_delete_tariff():
    tariff = create_tariff()

    tariff_id = tariff["id"]

    response = client.delete(
        f"/tariffs/{tariff_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/tariffs/{tariff_id}"
    )

    assert response.status_code == 404


def test_delete_tariff_not_found():
    response = client.delete(
        "/tariffs/99999"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Tariff not found"