"""READ-ONLY (2026-10-05): what is sitting in the "Delist Queue" tab, and which entries OnBuy keeps refusing as suspended.

The deletion reconciler keeps one row per SKU it has taken off the sheet's side (SKU | First Missing At | Stock Zeroed |
Deleted At | Note). A listing OnBuy answers "Listing is suspended" stays queued with Note "suspended" and is retried every
run. This prints the counts and writes the not-yet-deleted entries to OUT_DIR/delist_queue_open.csv. Writes nothing to the
sheet, Supabase or OnBuy.
"""
import csv
import json
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from deletion_reconciler import QUEUE_TAB
from retry_utils import with_retry

SHEET_NAME = os.getenv("SHEET_NAME") or "OpenMaal_Full_Feed_Master"
OUT_DIR = os.getenv("OUT_DIR") or "out"


def main():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]),
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    book = with_retry(lambda: gspread.authorize(creds).open(SHEET_NAME), what="sheet open", max_attempts=3)
    ws = book.worksheet(QUEUE_TAB)
    values = with_retry(ws.get_all_values, what="read queue", max_attempts=3)
    rows = [r + [""] * (5 - len(r)) for r in values[1:] if r and str(r[0]).strip()]
    open_rows = [r for r in rows if not str(r[3]).strip()]
    suspended = [r for r in open_rows if str(r[4]).strip().lower() == "suspended"]
    print(f"queue entries: {len(rows)} | deleted: {len(rows) - len(open_rows)} | still open: {len(open_rows)} "
          f"| of those marked suspended: {len(suspended)}")
    days = {}
    for r in open_rows:
        days[str(r[1])[:10]] = days.get(str(r[1])[:10], 0) + 1
    print("open entries by first-missing day:", dict(sorted(days.items())))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "delist_queue_open.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["SKU", "First Missing At", "Stock Zeroed", "Deleted At", "Note"])
        w.writerows(open_rows)


if __name__ == "__main__":
    main()
