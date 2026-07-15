import unittest

from app.services.route_service import build_tmap_request_payload


class RouteServiceTests(unittest.TestCase):
    def test_build_tmap_request_payload_with_start_and_places(self):
        start_place = {"name": "서울역", "latitude": 37.5547, "longitude": 126.9706}
        places = [
            {"id": 1, "name": "경복궁", "latitude": 37.5796, "longitude": 126.9770},
            {"id": 2, "name": "남산타워", "latitude": 37.5512, "longitude": 126.9882},
        ]

        payload = build_tmap_request_payload(start_place, places)

        self.assertEqual(payload["startName"], "서울역")
        self.assertEqual(payload["startX"], "126.9706")
        self.assertEqual(payload["startY"], "37.5547")
        self.assertEqual(len(payload["viaPoints"]), 2)
        self.assertEqual(payload["viaPoints"][0]["viaPointName"], "경복궁")


if __name__ == "__main__":
    unittest.main()
