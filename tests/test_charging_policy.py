import unittest

from twcmanager.core.charging_policy import OfferPolicyState, enforce_offer_policy


class TestChargingPolicy(unittest.TestCase):
    def test_below_min_becomes_zero(self):
        state = OfferPolicyState(last_offered_amps=0.0, last_change_ts=0.0)
        out = enforce_offer_policy(5.0, 6.0, state, now=1000)
        self.assertEqual(out, 0.0)

    def test_block_fast_off_to_on(self):
        state = OfferPolicyState(last_offered_amps=0.0, last_change_ts=1000.0)
        out = enforce_offer_policy(10.0, 6.0, state, now=1020.0, min_on_off_interval_s=60)
        self.assertEqual(out, 0.0)

    def test_block_fast_on_to_off(self):
        state = OfferPolicyState(last_offered_amps=10.0, last_change_ts=1000.0)
        out = enforce_offer_policy(0.0, 6.0, state, now=1020.0, min_on_off_interval_s=60)
        self.assertEqual(out, 10.0)


if __name__ == "__main__":
    unittest.main()
