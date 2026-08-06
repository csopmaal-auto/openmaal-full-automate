"""One-off, READ-ONLY: tally the Sheet's Sync Status values (first 70
chars) with OPC presence, so 'most rows show X' claims can be checked
against the actual distribution. Prints only - changes nothing."""
import collections
import json
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.environ["GOOGLE_CREDENTIALS"]), scope)
sheet = gspread.authorize(creds).open("OpenMaal_Full_Feed_Master").sheet1
data = sheet.get_all_records()
print(f"rows: {len(data)}")

tally = collections.Counter()
opc_tally = collections.Counter()
for row in data:
    status = str(row.get("Sync Status") or "").strip()
    key = status[:70] if status else "(blank)"
    tally[key] += 1
    opc = str(row.get("OPC") or "").strip().upper()
    opc_tally["OPC real" if opc not in ("", "PENDING") else "OPC pending/blank"] += 1

print("\n--- Sync Status distribution ---")
for k, n in tally.most_common(20):
    print(f"{n:>5}  {k}")
print("\n--- OPC ---")
for k, n in opc_tally.most_common():
    print(f"{n:>5}  {k}")
