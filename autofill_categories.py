"""One-off: apply HAND-CURATED categories for rows the strict matcher
refused. The relaxed auto-scorer tried first and produced DisplayPort-
grade mistakes (Smart TV -> TV Smart Glasses), so each entry below was
chosen by a human eye against the official category file (2026-08-01).
Rows not in the map stay on the employee worklist. DRY_RUN honoured.
"""
import json
import logging
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("onbuy_sync")

SHEET_NAME = "OpenMaal_Full_Feed_Master"
DRY_RUN = (os.getenv("DRY_RUN") or "1").strip().lower() not in ("0", "no", "false", "")

CURATED = {
    # 2026-08-06 batch - refusals from the overnight runs (31023834413/
    # 31045685093/31058858262), diagnosed with diagnose_categories.py: no
    # eBay Type set, no leaf named in any title. Monitors (MSI CMS, Acer
    # UM.*, LG, Samsung, HyperX, Lenovo TDS):
    "105168124275": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "121439004145": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "151009206921": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "152119441691": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "328965507410": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "915496878289": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "932737991316": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "308955325422": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "370709123219": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "692692350633": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "973255148974": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "196162335590": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "203837707009": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "435618291906": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "651034548862": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "700683502241": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "748806174456": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    # TVs (Sharp, Veltech):
    "135062856071": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "177372271151": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "273828555582": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "349690741351": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "693950581998": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    # HP All-in-One desktop:
    "300098014096": "Electronics & Technology > Computing & Gaming > Desktop Computers > All-in-one PCs",
    # Braun Series 5 foil shaver:
    "301853382795": "Health & Beauty > Shaving & Hair Removal > Electric Shavers > Foil Shavers",
    # Siemens built-in warming drawer (closest leaf):
    "317337370134": "Home & Garden > Kitchen & Home Appliances > Cooking Appliances > Ovens",
    # Acer Chromebook:
    "326705898729": "Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptops",
    # Remington multi groomers:
    "388862133853": "Health & Beauty > Shaving & Hair Removal > Electric Shavers > Hair Trimmers",
    "636841364720": "Health & Beauty > Shaving & Hair Removal > Electric Shavers > Hair Trimmers",
    # Brother laser printer:
    "401214645504": "Electronics & Technology > Computing & Gaming > Printers & Accessories > Printers",
    # Babyliss / Tresemme curling tongs:
    "428692372975": "Health & Beauty > Hair Care > Hair Styling Tools > Hair Curlers",
    "604912175889": "Health & Beauty > Hair Care > Hair Styling Tools > Hair Curlers",
    # Xbox Onimusha game:
    "432460235898": "Electronics & Technology > Computing & Gaming > Video Games, Consoles & Accessories > Video Games",
    # Breville iron:
    "847873176179": "Home & Garden > Kitchen & Home Appliances > Irons & Garment Steamers > Irons",
    # Lay-Z-Spa inflatable hot tub:
    "896518876882": "Home & Garden > Swimming Pools & Hot Tubs > Hot Tubs & Accessories > In-Ground & Inflatable Hot Tubs",
    # RingConn smart ring (an activity tracker):
    "110065267390": "Sports & Outdoors > Exercise & Fitness > Sports Technology > Sports Activity Trackers",
    # 2026-08-05 batch - the 48 SKUs refusing across runs 30932938530/
    # 30957208320/30987744041, diagnosed with diagnose_categories.py: none
    # of these listings set eBay's Type item-specific and no title names a
    # category leaf as a phrase, so the strict matcher correctly refused.
    # Chosen by eye against the official category file. Two of them
    # (649982845560, 691372424459) the scorer would have WRONGLY matched
    # from description noise (AirTag keyring -> Phone Mounts & Holders,
    # Sharp TV -> Radio Power Supplies) - curating them preempts that.
    # TVs (Hisense, Veltech, Sharp):
    "199874625003": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "211012632022": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "268976698397": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "289164177050": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "326660885550": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "349132426617": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "691372424459": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "699743614607": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "794060051880": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    "836972603877": "Electronics & Technology > TV & Audio > TVs & Accessories > TVs",
    # Computer monitors (MSI CMS, iiyama, Samsung, ASUS ProArt pen display):
    "122527407374": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "342396668526": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "904286030983": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "385723189264": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "394585844907": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "486921277620": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    "690622831641": "Electronics & Technology > Computing & Gaming > Computer Monitors & Monitor Accessories > Computer Monitors",
    # Chromebooks:
    "250665258371": "Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptops",
    "917983975457": "Electronics & Technology > Computing & Gaming > Laptops, MacBooks & Accessories > Laptops",
    # soundcore earbuds (no earbuds leaf - Headphones is the device leaf):
    "151041171577": "Electronics & Technology > TV & Audio > Headphones & Accessories > Headphones",
    "274245173120": "Electronics & Technology > TV & Audio > Headphones & Accessories > Headphones",
    "454531240952": "Electronics & Technology > TV & Audio > Headphones & Accessories > Headphones",
    "809345557176": "Electronics & Technology > TV & Audio > Headphones & Accessories > Headphones",
    "651822086262": "Electronics & Technology > TV & Audio > Headphones & Accessories > Headphones",
    # soundcore Boom Go 3i speakers:
    "147626043766": "Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers",
    "178472936636": "Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers",
    "613028061924": "Electronics & Technology > TV & Audio > Speakers & Sound Systems > Speakers",
    # Anker USB-C hubs; HDMI switch:
    "117254514242": "Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs",
    "619428203742": "Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs",
    "331982981101": "Electronics & Technology > Computing & Gaming > Computing Peripherals > USB & FireWire Hubs",
    "774213573278": "Electronics & Technology > Cables & Adapters > Adapters > DVI & HDMI Adapters",
    # Xbox games:
    "189397389872": "Electronics & Technology > Computing & Gaming > Video Games, Consoles & Accessories > Video Games",
    "221806139675": "Electronics & Technology > Computing & Gaming > Video Games, Consoles & Accessories > Video Games",
    # WD internal NVMe SSD:
    "239979695751": "Electronics & Technology > Computing & Gaming > Computer Components > Internal Solid State Drives",
    # Sekonda ladies watch:
    "301286780922": "Jewellery & Watches > Watches > Watches For Women > Women's Watches",
    # Apple Watch braided loops:
    "323227069071": "Electronics & Technology > Mobile & Smart Tech > Smart Watches & Accessories > Smart Watch Bands & Straps",
    "464604480772": "Electronics & Technology > Mobile & Smart Tech > Smart Watches & Accessories > Smart Watch Bands & Straps",
    "788851929670": "Electronics & Technology > Mobile & Smart Tech > Smart Watches & Accessories > Smart Watch Bands & Straps",
    "823954902752": "Electronics & Technology > Mobile & Smart Tech > Smart Watches & Accessories > Smart Watch Bands & Straps",
    # AirTag key ring holder:
    "649982845560": "Clothing, Shoes & Accessories > Luggage, Bags & Travel Accessories > Travel Accessories > Keyrings",
    # ELEMIS cleansing balm:
    "697960501939": "Health & Beauty > Skin Care > Facial Skin Care > Facial Cleansers",
    # RODE boompole (a boom for microphones):
    "731407598370": "Musical Instruments & DJ > Microphones & Music Accessories > Microphone Accessories > Microphone Stands",
    # NEBULA Capsule projector travel case:
    "769878818543": "Electronics & Technology > TV & Audio > Projectors & Accessories > Projector Bags",
    # LookSmart Ferrari 499P diecast models (closest leaf - no finished-
    # diecast leaf exists):
    "807773493752": "Toys & Games > Hobby Toys & Games > Model Kits > Motorcycles, Cars & Trucks Model Kits",
    "878166375283": "Toys & Games > Hobby Toys & Games > Model Kits > Motorcycles, Cars & Trucks Model Kits",
    # HOVERAir X1 Pro camera drone:
    "923149774284": "Electronics & Technology > Cameras & Photography > Cameras > Drones",
    # Bosch Purion 200 eBike display unit:
    "645729914551": "Sports & Outdoors > Cycling > Bike Parts > Electric Bike Parts",
    # Console thumb-stick grip caps:
    "430939380407": "Electronics & Technology > Computing & Gaming > Video Games, Consoles & Accessories > Video Game Controller Parts & Accessories",
}
# NOT curated: 366797761556 - its Supabase Title is empty, nothing to
# categorize until a title fetch succeeds.


def main():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]), scope)
    sheet = gspread.authorize(creds).open(SHEET_NAME).sheet1
    data = sheet.get_all_records()
    headers = [str(h).strip() for h in sheet.row_values(1)]
    col_map = {col: idx + 1 for idx, col in enumerate(headers) if col}

    def col_letter(n):
        out = ""
        while n:
            n, rem = divmod(n - 1, 26)
            out = chr(65 + rem) + out
        return out

    updates, applied = [], []
    for idx, row in enumerate(data, start=2):
        sku = str(row.get("SKU") or "").strip()
        if sku in CURATED and "no matching OnBuy category" in str(row.get("Sync Status") or ""):
            path = CURATED[sku]
            applied.append((idx, sku, path))
            updates.append({"range": f"{col_letter(col_map['Category'])}{idx}", "values": [[path]]})
            updates.append({"range": f"{col_letter(col_map['Sync Status'])}{idx}", "values": [[""]]})
    for idx, sku, path in applied:
        logger.info("row %d %s -> %s", idx, sku, path)
    logger.info("curated categories to apply: %d", len(applied))
    if DRY_RUN:
        logger.info("DRY RUN - nothing written")
        return
    if updates:
        sheet.batch_update(updates)
        logger.info("Written - these rows retry on the next scheduled run")


if __name__ == "__main__":
    main()
