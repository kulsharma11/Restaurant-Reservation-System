# tests/test_tables.py

from tests.conftest import create_test_table


class TestCreateTable:
    def test_create_table_success(self, client):
        """Staff can create a table with valid data."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 4,
            "location": "indoor"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["table_number"] == 1
        assert data["capacity"] == 4
        assert data["location"] == "indoor"
        assert "id" in data

    def test_create_table_outdoor(self, client):
        """Can create an outdoor table."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 6,
            "location": "outdoor"
        })
        assert response.status_code == 201
        assert response.json()["location"] == "outdoor"

    def test_create_table_duplicate_number(self, client):
        """Cannot create two tables with the same table number."""
        create_test_table(client, table_number=1)
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 6,
            "location": "outdoor"
        })
        assert response.status_code == 409

    def test_create_table_invalid_location(self, client):
        """Location must be indoor or outdoor — anything else is rejected."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 4,
            "location": "rooftop"
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_create_table_zero_capacity(self, client):
        """Capacity must be greater than 0."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 0,
            "location": "indoor"
        })
        assert response.status_code == 422

    def test_create_table_negative_capacity(self, client):
        """Negative capacity is also rejected."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": -3,
            "location": "indoor"
        })
        assert response.status_code == 422

    def test_create_table_exceeds_max_capacity(self, client):
        """Capacity cannot exceed 20."""
        response = client.post("/tables/", json={
            "table_number": 1,
            "capacity": 25,
            "location": "indoor"
        })
        assert response.status_code == 422


class TestListTables:
    def test_list_tables_empty(self, client):
        """Returns empty list when no tables exist."""
        response = client.get("/tables/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tables(self, client):
        """Returns all created tables."""
        create_test_table(client, table_number=1)
        create_test_table(client, table_number=2)
        response = client.get("/tables/")
        assert response.status_code == 200
        assert len(response.json()) == 2
