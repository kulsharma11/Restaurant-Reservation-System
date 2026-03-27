# tests/test_reservations.py

from tests.conftest import create_test_table, create_test_reservation
from unittest.mock import patch
from datetime import datetime, timedelta


FUTURE_DATE = "2099-12-31"


class TestAvailableSlots:
    def test_returns_all_slots_when_no_bookings(self, client):
        """All 3 slots should show as available when no reservations exist."""
        create_test_table(client)
        response = client.get(f"/reservations/available?date={FUTURE_DATE}")
        assert response.status_code == 200
        slots = response.json()
        assert len(slots) == 3  # 18:00, 20:00, 22:00

    def test_booked_table_not_in_available(self, client):
        """A booked table should not appear in available tables for that slot."""
        table = create_test_table(client)
        create_test_reservation(client, table_id=table["id"], time_slot="18:00")

        response = client.get(f"/reservations/available?date={FUTURE_DATE}")
        slots = response.json()

        slot_18 = next(s for s in slots if s["time_slot"] == "18:00")
        available_ids = [t["id"] for t in slot_18["available_tables"]]
        assert table["id"] not in available_ids

    def test_booked_table_still_available_in_other_slots(self, client):
        """Booking a table for 18:00 should not affect 20:00 availability."""
        table = create_test_table(client)
        create_test_reservation(client, table_id=table["id"], time_slot="18:00")

        response = client.get(f"/reservations/available?date={FUTURE_DATE}")
        slots = response.json()

        slot_20 = next(s for s in slots if s["time_slot"] == "20:00")
        available_ids = [t["id"] for t in slot_20["available_tables"]]
        assert table["id"] in available_ids

    def test_cancelled_reservation_frees_table(self, client):
        """After cancelling, the table should reappear in available slots."""
        table = create_test_table(client)
        created = create_test_reservation(
            client, table_id=table["id"], time_slot="18:00"
        ).json()

        # Cancel the reservation
        client.delete(f"/reservations/{created['id']}")

        # Table should be available again
        response = client.get(f"/reservations/available?date={FUTURE_DATE}")
        slots = response.json()
        slot_18 = next(s for s in slots if s["time_slot"] == "18:00")
        available_ids = [t["id"] for t in slot_18["available_tables"]]
        assert table["id"] in available_ids

    def test_no_tables_returns_empty_lists(self, client):
        """When no tables exist at all, each slot should have an empty available list."""
        response = client.get(f"/reservations/available?date={FUTURE_DATE}")
        assert response.status_code == 200
        slots = response.json()
        for slot in slots:
            assert slot["available_tables"] == []


class TestCreateReservation:
    def test_create_reservation_success(self, client):
        """Can book an available table."""
        table = create_test_table(client)
        response = create_test_reservation(client, table_id=table["id"])
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"
        assert data["table"]["id"] == table["id"]

    def test_response_includes_all_fields(self, client):
        """Response should contain all expected fields including created_at."""
        table = create_test_table(client)
        response = create_test_reservation(client, table_id=table["id"])
        data = response.json()
        assert "id" in data
        assert "date" in data
        assert "time_slot" in data
        assert "guest_count" in data
        assert "status" in data
        assert "created_at" in data
        assert "table" in data
        assert "customer" in data
        assert data["customer"]["name"] == "Test User"
        assert data["customer"]["email"] == "test@example.com"

    def test_double_booking_prevented(self, client):
        """Cannot book the same table for the same date and slot twice."""
        table = create_test_table(client)
        create_test_reservation(client, table_id=table["id"])
        response = create_test_reservation(client, table_id=table["id"])
        assert response.status_code == 409

    def test_capacity_exceeded(self, client):
        """Cannot book a table-for-2 for 5 guests."""
        table = create_test_table(client, capacity=2)
        response = create_test_reservation(client, table_id=table["id"], guest_count=5)
        assert response.status_code == 400

    def test_nonexistent_table_rejected(self, client):
        """Booking a table that doesn't exist returns 404."""
        response = create_test_reservation(client, table_id=9999)
        assert response.status_code == 404

    def test_invalid_time_slot(self, client):
        """Time slot must be one of the fixed options."""
        table = create_test_table(client)
        response = client.post("/reservations/", json={
            "date": FUTURE_DATE,
            "time_slot": "15:00",  # Not a valid slot
            "guest_count": 2,
            "table_id": table["id"],
            "customer": {"name": "Test", "email": "t@t.com"}
        })
        assert response.status_code == 422

    def test_past_date_rejected(self, client):
        """Cannot make a reservation for a past date."""
        table = create_test_table(client)
        response = client.post("/reservations/", json={
            "date": "2000-01-01",
            "time_slot": "18:00",
            "guest_count": 2,
            "table_id": table["id"],
            "customer": {"name": "Test", "email": "t@t.com"}
        })
        assert response.status_code == 422

    def test_today_date_accepted(self, client):
        """Booking for today's date should be accepted (not rejected as past)."""
        table = create_test_table(client)
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.post("/reservations/", json={
            "date": today,
            "time_slot": "22:00",  # late slot to avoid time-of-day issues
            "guest_count": 2,
            "table_id": table["id"],
            "customer": {"name": "Test", "email": "today@test.com"}
        })
        assert response.status_code == 201

    def test_special_requests_stored(self, client):
        """Special requests should be stored and returned in response."""
        table = create_test_table(client)
        response = client.post("/reservations/", json={
            "date": FUTURE_DATE,
            "time_slot": "18:00",
            "guest_count": 2,
            "table_id": table["id"],
            "special_requests": "Window seat, nut allergy",
            "customer": {"name": "Test", "email": "special@test.com"}
        })
        assert response.status_code == 201
        assert response.json()["special_requests"] == "Window seat, nut allergy"

    def test_same_customer_multiple_reservations(self, client):
        """Same customer (by email) can make multiple reservations."""
        table1 = create_test_table(client, table_number=1)
        table2 = create_test_table(client, table_number=2)

        res1 = create_test_reservation(client, table_id=table1["id"], time_slot="18:00")
        assert res1.status_code == 201

        # Same customer email, different slot
        response = client.post("/reservations/", json={
            "date": FUTURE_DATE,
            "time_slot": "20:00",
            "guest_count": 2,
            "table_id": table2["id"],
            "customer": {"name": "Test User", "email": "test@example.com"}
        })
        assert response.status_code == 201

        # Both should reference the same customer
        assert res1.json()["customer"]["id"] == response.json()["customer"]["id"]


class TestSmartAssignment:
    def test_smart_assign_picks_smallest_fitting_table(self, client):
        """Smart assignment should pick the table-for-2 over table-for-8 for 2 guests."""
        small = create_test_table(client, table_number=1, capacity=2)
        large = create_test_table(client, table_number=2, capacity=8)

        response = create_test_reservation(client, table_id=None, guest_count=2)
        assert response.status_code == 201
        assert response.json()["table"]["id"] == small["id"]

    def test_smart_assign_falls_back_to_next_table(self, client):
        """When smallest table is taken, picks the next smallest."""
        small = create_test_table(client, table_number=1, capacity=2)
        medium = create_test_table(client, table_number=2, capacity=4)

        # Book the small table
        create_test_reservation(client, table_id=small["id"], guest_count=2)

        # Next booking with no table_id should get the medium table
        response = create_test_reservation(client, table_id=None, guest_count=2)
        assert response.status_code == 201
        assert response.json()["table"]["id"] == medium["id"]

    def test_smart_assign_no_tables_available(self, client):
        """Returns 409 when all fitting tables are taken."""
        table = create_test_table(client, capacity=2)
        create_test_reservation(client, table_id=table["id"], guest_count=2)

        response = create_test_reservation(client, table_id=None, guest_count=2)
        assert response.status_code == 409

    def test_smart_assign_skips_too_small_tables(self, client):
        """Smart assignment does not pick a table smaller than guest count."""
        small = create_test_table(client, table_number=1, capacity=2)
        big = create_test_table(client, table_number=2, capacity=6)

        response = create_test_reservation(client, table_id=None, guest_count=4)
        assert response.status_code == 201
        assert response.json()["table"]["id"] == big["id"]

    def test_smart_assign_after_cancellation(self, client):
        """Cancelled reservation's table should be available for smart assignment."""
        table = create_test_table(client, table_number=1, capacity=4)

        # Book and cancel
        created = create_test_reservation(client, table_id=table["id"]).json()
        client.delete(f"/reservations/{created['id']}")

        # Smart assignment should find this table available
        response = create_test_reservation(client, table_id=None, guest_count=2)
        assert response.status_code == 201
        assert response.json()["table"]["id"] == table["id"]


class TestGetReservation:
    def test_get_reservation_success(self, client):
        """Can retrieve a reservation by ID."""
        table = create_test_table(client)
        created = create_test_reservation(client, table_id=table["id"]).json()

        response = client.get(f"/reservations/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_nonexistent_reservation(self, client):
        """Returns 404 for a reservation that doesn't exist."""
        response = client.get("/reservations/9999")
        assert response.status_code == 404

    def test_get_cancelled_reservation(self, client):
        """Can still retrieve a cancelled reservation — status should be cancelled."""
        table = create_test_table(client)
        created = create_test_reservation(client, table_id=table["id"]).json()
        client.delete(f"/reservations/{created['id']}")

        response = client.get(f"/reservations/{created['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


class TestCancelReservation:
    def test_cancel_success(self, client):
        """Can cancel a reservation that is far in the future."""
        table = create_test_table(client)
        created = create_test_reservation(client, table_id=table["id"]).json()

        response = client.delete(f"/reservations/{created['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancel_already_cancelled(self, client):
        """Cannot cancel a reservation that is already cancelled."""
        table = create_test_table(client)
        created = create_test_reservation(client, table_id=table["id"]).json()

        client.delete(f"/reservations/{created['id']}")
        response = client.delete(f"/reservations/{created['id']}")
        assert response.status_code == 400

    def test_cancel_nonexistent_reservation(self, client):
        """Cannot cancel a reservation that doesn't exist."""
        response = client.delete("/reservations/9999")
        assert response.status_code == 404

    def test_cancel_within_window_rejected(self, client):
        """Cannot cancel within 2 hours of the reservation time."""
        table = create_test_table(client)

        # Create a reservation on a fixed future date at 22:00
        fixed_date = "2099-06-15"
        created = create_test_reservation(
            client, table_id=table["id"],
            date=fixed_date, time_slot="22:00"
        ).json()

        # Mock datetime.now() to return a time that is 30 minutes before the slot
        # Slot is 2099-06-15 22:00 → mock now = 2099-06-15 21:30 (inside the 2hr window)
        mock_now = datetime(2099, 6, 15, 21, 30)

        with patch("app.services.reservation_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            response = client.delete(f"/reservations/{created['id']}")

        assert response.status_code == 400

    def test_cancel_outside_window_allowed(self, client):
        """Can cancel when more than 2 hours before the reservation time."""
        table = create_test_table(client)

        fixed_date = "2099-06-15"
        created = create_test_reservation(
            client, table_id=table["id"],
            date=fixed_date, time_slot="22:00"
        ).json()

        # Mock now = 2099-06-15 19:00 (3 hours before slot — outside the window)
        mock_now = datetime(2099, 6, 15, 19, 0)

        with patch("app.services.reservation_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            response = client.delete(f"/reservations/{created['id']}")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancel_exactly_at_boundary(self, client):
        """Cancellation exactly 2 hours before the slot should succeed."""
        table = create_test_table(client)

        fixed_date = "2099-06-15"
        created = create_test_reservation(
            client, table_id=table["id"],
            date=fixed_date, time_slot="22:00"
        ).json()

        # Mock now = 2099-06-15 20:00 (exactly 2 hours before — at the deadline)
        mock_now = datetime(2099, 6, 15, 20, 0)

        with patch("app.services.reservation_service.datetime") as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            response = client.delete(f"/reservations/{created['id']}")

        # At exactly the deadline: now == deadline, so `now > deadline` is False → allowed
        assert response.status_code == 200
