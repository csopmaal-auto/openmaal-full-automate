"""One-off (2026-08-13): OnBuy support asked for example SKUs where the
Product Listings: Update by SKU endpoint rejects suspended listings.
Attempt a real by-SKU price/stock update on three known-suspended SKUs
(values identical to what their activation would set, so an unexpected
success just fixes the listing) and log the verbatim outcome for the
ticket reply. Delete with the rest of the incident tooling."""
import logging
import os

from onbuy_client import OnBuyClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# (sku, price, stock) - the exact values from the 2026-08-11 attach attempt
TARGETS = [
    ("788193201182", 44.80, 5),
    ("247797350066", 116.19, 4),
    ("633312438423", 16.18, 5),
]


def main():
    onbuy = OnBuyClient()
    if not onbuy.authenticate():
        raise SystemExit("OnBuy auth failed")
    for sku, price, stock in TARGETS:
        try:
            result = onbuy.update_listing(sku=sku, price=price, stock=stock)
            log.info("PROBE %s: SUCCEEDED (%s)", sku, result)
        except Exception as exc:
            log.info("PROBE %s: rejected - %s", sku, exc)


if __name__ == "__main__":
    main()
