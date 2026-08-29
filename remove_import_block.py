"""One-off (2026-08-27, user policy): the all-products Buy Box track is
GTV-only; Arden reverts to eBay-sheet-products-only like YRA (Amazon API
integration is the future route for the rest of the catalog). Remove the
remaining 08-25 imported block rows: a row is deleted only if ALL hold:
  - it sits in the appended import block (row >= BLOCK_START);
  - it is import-shaped (no Supplier URL, Sync Status "Synced");
  - its Cost Price is still empty (a filled cost = the team adopted it -
    kept and reported).
Original rows are never touched; the live listings stay live on OnBuy.
Block rows with a different Sync Status are kept and reported (the hourly
backfill re-stamped some imported rows). deleteDimension runs descending.
DRY_RUN default on."""
import json
import os
import re

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import supabase_db
from retry_utils import with_retry

DRY_RUN = (os.getenv("DRY_RUN") or "1").strip().lower() not in ("0", "no", "false", "")
SHEET_NAME = os.getenv("SHEET_NAME") or "OpenMaal_Full_Feed_Master"
BLOCK_START = int(os.environ["BLOCK_START"])
# "1" = also delete block rows whose Sync Status is not "Synced" (still
# reported). Position (>= BLOCK_START) + no URL + no cost stays required.
LIFT_STATUS_GUARD = (os.getenv("LIFT_STATUS_GUARD") or "").strip() == "1"
# "1" (2026-08-29, user policy): the team-adopted import rows go too - the
# user pulled OpenMaal out of the all-products Buy Box track entirely
# (Amazon API is the future route), so URL/cost/status no longer protect a
# block row. Position is then the only criterion, which makes BLOCK_END
# matter: rows the team appended AFTER the import block (new eBay products)
# must be fenced out of range. Adopted rows were mirrored to Supabase by
# the rotation, so their mirror rows are purged after the sheet delete.
DELETE_ADOPTED = (os.getenv("DELETE_ADOPTED") or "").strip() == "1"
# Optional inclusive last row of the block; 0/unset = to the sheet's end.
BLOCK_END = int(os.getenv("BLOCK_END") or "0")


def main():
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    sheet = with_retry(lambda: gspread.authorize(creds).open(SHEET_NAME).sheet1, what="sheet open", max_attempts=3)
    rows = with_retry(lambda: sheet.get_all_records(), what="sheet read", max_attempts=3)
    print(f"rows: {len(rows)} | block starts at row {BLOCK_START}")

    to_delete, kept_cost, kept_status, kept_url = [], [], [], []
    delete_skus = []
    for i, r in enumerate(rows):
        rownum = i + 2
        if rownum < BLOCK_START:
            continue
        if BLOCK_END and rownum > BLOCK_END:
            continue
        sku = str(r.get("SKU") or "").strip()
        if not sku:
            continue
        if str(r.get("Supplier URL") or "").strip():
            kept_url.append(rownum)
            if not DELETE_ADOPTED:
                continue
        elif str(r.get("Cost Price (£)") or "").strip():
            kept_cost.append((rownum, sku))
            if not DELETE_ADOPTED:
                continue
        elif str(r.get("Sync Status") or "").strip() != "Synced":
            kept_status.append((rownum, sku, str(r.get("Sync Status") or "").strip()[:30]))
            if not (LIFT_STATUS_GUARD or DELETE_ADOPTED):
                continue
        to_delete.append(rownum)
        delete_skus.append(sku)
    _kw = "DELETE (adopted)" if DELETE_ADOPTED else "KEEP"
    for rn, sku in kept_cost[:10]:
        print(f"  {_kw} row {rn} SKU {sku} - team filled Cost Price")
    for rn, sku, st in kept_status[:10]:
        print(f"  {_kw} row {rn} SKU {sku} - status {st!r}")
    if kept_url:
        print(f"  {_kw} {len(kept_url)} row(s) with a Supplier URL (team-adopted)")
    if to_delete:
        print(f"block row span selected: {min(to_delete)}..{max(to_delete)}")
    print(f"import rows to delete: {len(to_delete)} | url {len(kept_url)}, cost {len(kept_cost)}, "
          f"odd-status {len(kept_status)} ({'deleted too' if DELETE_ADOPTED else 'kept'})")
    # The mirror only ever held rows the pipeline processed - the adopted
    # (URL-bearing) rows. Purging plain-safe SKUs covers them; any SKU with
    # characters PostgREST's in.() list can't carry raw is reported instead
    # (a stale mirror row is harmless - report-only, don't fail the run).
    purge_skus = [s for s in delete_skus if re.fullmatch(r"[0-9A-Za-z_.-]+", s)]
    odd_skus = sorted(set(delete_skus) - set(purge_skus))
    if odd_skus:
        print(f"mirror purge will skip {len(odd_skus)} SKU(s) with unsafe characters: {', '.join(odd_skus[:8])}")
    if DRY_RUN:
        print(f"DRY RUN - nothing deleted (would purge {len(purge_skus)} mirror row(s))")
        return
    if not to_delete:
        print("nothing to delete")
        return
    requests = [{"deleteDimension": {"range": {
        "sheetId": sheet.id, "dimension": "ROWS",
        "startIndex": rn - 1, "endIndex": rn}}} for rn in sorted(to_delete, reverse=True)]
    done = 0
    for c in range(0, len(requests), 400):
        chunk = requests[c:c + 400]
        with_retry(lambda ch=chunk: sheet.spreadsheet.batch_update({"requests": ch}),
                   what=f"delete batch {c}", max_attempts=3)
        done = min(c + 400, len(requests))
        print(f"deleted {done}/{len(requests)}")
    print(f"removed {len(to_delete)} imported row(s); originals and live listings untouched")
    purged = 0
    for c in range(0, len(purge_skus), 150):
        if supabase_db.delete_products(purge_skus[c:c + 150]):
            purged += len(purge_skus[c:c + 150])
    print(f"mirror purge: {purged}/{len(purge_skus)} SKU(s) deleted from Supabase")


if __name__ == "__main__":
    main()
