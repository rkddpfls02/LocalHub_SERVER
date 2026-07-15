import unittest

from app.services.route_service import build_tmap_request_payload


class RouteServiceTests(unittest.TestCase):
    def test_build_tmap_request_payload_uses_first_and_last_places(self):
        start_place = {"id": 1, "name": "출발지", "latitude": 35.1, "longitude": 129.1}
        end_place = {"id": 5, "name": "도착지", "latitude": 35.5, "longitude": 129.5}
        via_places = [
            {"id": 2, "name": "경유지1", "latitude": 35.2, "longitude": 129.2},
            {"id": 3, "name": "경유지2", "latitude": 35.3, "longitude": 129.3},
            {"id": 4, "name": "경유지3", "latitude": 35.4, "longitude": 129.4},
        ]

        payload = build_tmap_request_payload(start_place, end_place, via_places)

        self.assertEqual(payload["startName"], "출발지")
        self.assertEqual(payload["endName"], "도착지")
        self.assertEqual(payload["endX"], "129.5")
        self.assertEqual(len(payload["viaPoints"]), 3)
        self.assertEqual(payload["viaPoints"][0]["viaPointId"], "2")


if __name__ == "__main__":
    unittest.main()
