"""One-off: hand-curated category corrections from the 2026-08-10
correctness scan (tier-2 review). Every SKU below was checked by eye
against its title; writes ONLY the Category cell - Sync Status and
OnBuy state stay untouched. DRY_RUN default on."""

SHEET_NAME = 'OpenMaal_Full_Feed_Master'

CORRECTIONS = {
    '828544689235': 'Home & Garden > Kitchen & Home Appliances > Cooking Appliances > Cooker Hoods & Extractor Fans',
    '952572090111': 'Home & Garden > Kitchen & Home Appliances > Cooking Appliances > Cooker Hoods & Extractor Fans',
    '384656741310': 'Home & Garden > Kitchen & Home Appliances > Small Kitchen Appliances > Microwaves',
    '896642467697': 'Home & Garden > Kitchen & Home Appliances > Climate Control Appliances > Climate Control Appliance Parts & Accessories',
    '255390684327': 'Home & Garden > Kitchen & Home Appliances > Climate Control Appliances > Climate Control Appliance Parts & Accessories',
    '779218515193': 'Home & Garden > Kitchen & Home Appliances > Climate Control Appliances > Climate Control Appliance Parts & Accessories',
    '847320984098': 'Home & Garden > Kitchen & Home Appliances > Climate Control Appliances > Climate Control Appliance Parts & Accessories',
    '472675718472': 'Home & Garden > Kitchen & Home Appliances > Water Filters & Coolers > Water Filter Cartridges',
    '489374714117': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '838294467076': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '891208718374': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '880170975922': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '366973264956': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '662447134931': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '894845557207': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '776724509388': 'Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers',
    '717894489957': 'Home & Garden > Garden & Outdoor Living > BBQ & Outdoor Dining > BBQ Replacement Parts',
    '874743439409': 'Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs',
    '278711522986': 'Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs',
    '717587011885': 'Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs',
    '478167672819': 'Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs',
    '195986078805': 'Electronics & Technology > Computing & Gaming > iPads, Tablets & eBook Readers > Tablet Cases',
    '367954145035': 'Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptop Bags',
    '313758988088': 'Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptop Bags',
    '991139730923': 'Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptop Bags',
    '446840818168': 'Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptop Bags',
    '801647163376': 'Electronics & Technology > TV & Audio > Streaming & Catchup > Media Streaming Devices',
    '702948705633': 'Electronics & Technology > TV & Audio > Streaming & Catchup > Media Streaming Devices',
    '830432753409': 'Electronics & Technology > Computing & Gaming > Desktop Computers > Tower PCs',
}

import json
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

DRY_RUN = (os.getenv("DRY_RUN") or "1").strip().lower() not in ("0", "no", "false", "")


def col_letter(n):
    out = ""
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]), scope)
    sheet = gspread.authorize(creds).open(SHEET_NAME).sheet1
    headers = [str(h).strip() for h in sheet.row_values(1)]
    col_map = {col: idx + 1 for idx, col in enumerate(headers) if col}
    data = sheet.get_all_records()

    updates, planned = [], []
    for idx, row in enumerate(data, start=2):
        sku = str(row.get("SKU") or "").strip()
        want = CORRECTIONS.get(sku)
        if not want:
            continue
        cat = str(row.get("Category") or "").strip()
        if cat.lower() == want.lower():
            continue
        planned.append((idx, sku, cat, want))
        updates.append({"range": f"{col_letter(col_map['Category'])}{idx}", "values": [[want]]})

    for idx, sku, cat, want in planned:
        print(f"row {idx} {sku}")
        print(f"    {cat or '(blank)'}  ->  {want}")
    print(f"\ncorrections planned: {len(planned)}")
    if DRY_RUN:
        print("DRY RUN - nothing written")
        return
    if updates:
        sheet.batch_update(updates)
        print(f"Written {len(updates)} Category cell(s).")


if __name__ == "__main__":
    main()
