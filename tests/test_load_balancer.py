import unittest

from twcmanager.core.load_balancer import compute_allowed_amps


class TestLoadBalancer(unittest.TestCase):
    def test_clamps_to_zero_when_below_min(self):
        allowed = compute_allowed_amps(25, 24, 0, 12, 40, 2)
        self.assertEqual(allowed, 0.0)

    def test_allows_expected_headroom(self):
        allowed = compute_allowed_amps(25, 18, 8, 12, 40, 2)
        self.assertEqual(allowed, 13.0)


if __name__ == "__main__":
    unittest.main()
