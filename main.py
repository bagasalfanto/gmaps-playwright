import asyncio
import csv
import argparse
import random
import re
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

SEARCH_URL = "https://www.google.com/maps/search/{query}"
SCROLL_PAUSE = 2.0
DETAIL_PAUSE_MIN = 2.0
DETAIL_PAUSE_MAX = 4.0
MAX_SCROLL_ATTEMPTS = 15

CSV_FIELDNAMES = [
    "nama_tempat",
    "rating",
    "rentang_harga",
    "kategori_tempat",
    "alamat_lengkap",
    "situs_web",
    "nomor_telepon",
    "email",
    "kode_lokasi_google",
    "google_maps_url",
]

async def apply_stealth(page):
    try:
        from playwright_stealth import Stealth
        await Stealth().apply_stealth_async(page)
    except (ImportError, AttributeError):
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        except ImportError:
            print("  [Peringatan] playwright-stealth tidak terinstall, lanjut tanpa stealth mode")
            print("  Install dengan: pip install playwright-stealth")

async def handle_consent(page):
    await asyncio.sleep(2)
    selectors = [
        'button:has-text("Accept all")',
        'button:has-text("Accept All")',
        'button:has-text("I agree")',
        'button:has-text("Terima semua")',
        'button:has-text("Terima")',
        'button:has-text("Setuju")',
        'button:has-text("Tout accepter")',
        'button:has-text("Alle akzeptieren")',
        'button:has-text("Accept")',
        'form[action*="consent"] button',
        'button[jsname="higCR"]',
        'button[jsname="b3VHJd"]',
    ]
    for sel in selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0:
            print(f"  Consent popup ditemukan, mengklik: {sel}")
            await btn.click()
            await asyncio.sleep(2)
            return True
    print("  Tidak ada consent popup")
    return False

async def scroll_results(page):
    try:
        await page.wait_for_selector('div[role="feed"]', state="visible", timeout=15000)
    except Exception:
        print("  Tidak menemukan panel hasil. Kemungkinan query tidak menghasilkan data.")
        await page.screenshot(path="debug_error.png")
        print("  Screenshot disimpan sebagai 'debug_error.png'.")
        return []

    feed = page.locator('div[role="feed"]')
    links = page.locator('div[role="feed"] a[href*="/maps/place/"]')
    previous_count = 0
    no_change_count = 0
    end_selector = 'text="You\'ve reached the end of the list.", text="Anda sudah mencapai akhir daftar."'

    while no_change_count < MAX_SCROLL_ATTEMPTS:
        await feed.evaluate("(el) => el.scrollTop = el.scrollHeight")
        await asyncio.sleep(SCROLL_PAUSE)
        current_count = await links.count()

        if current_count == previous_count:
            no_change_count += 1
            if await page.locator(end_selector).count() > 0:
                break
        else:
            no_change_count = 0
            previous_count = current_count

        print(f"     ...{current_count} tempat dimuat", end="\r")

    print(f"     ...{previous_count} tempat dimuat (selesai)")

    final_count = await links.count()
    places = []
    for i in range(final_count):
        href = await links.nth(i).get_attribute("href")
        aria = await links.nth(i).get_attribute("aria-label")
        if href:
            places.append({"url": href, "name": aria or f"Tempat #{i+1}"})
    return places

async def _get_text(locator) -> str:
    if await locator.count() > 0:
        return (await locator.inner_text()).strip()
    return ""

async def _get_label(locator, prefix_pattern: str) -> str:
    if await locator.count() > 0:
        label = await locator.get_attribute("aria-label")
        if label:
            return re.sub(prefix_pattern, "", label).strip()
        return (await locator.inner_text()).strip()
    return ""

async def extract_place_details(page):
    data = {field: "" for field in CSV_FIELDNAMES}
    try:
        await page.wait_for_selector("h1.fontHeadlineLarge, h1", timeout=8000)
    except Exception:
        return data

    await asyncio.sleep(1.2)

    data["nama_tempat"] = (
        await _get_text(page.locator("h1.fontHeadlineLarge").first)
        or await _get_text(page.locator("h1").last)
    )

    raw_rating = await _get_text(page.locator("div.fontDisplayLarge").first)
    normalized = raw_rating.replace(",", ".")
    if re.match(r"^\d+\.?\d*$", normalized):
        data["rating"] = normalized

    price_el = page.locator('span[aria-label*="Harga:" i], span:has-text("Rp"), span:has-text("· $")').first
    if await price_el.count() > 0:
        clean_txt = re.sub(r'[.,]', '', await price_el.inner_text())
        nums = [str(int(n)//1000 if int(n)>=1000 else int(n)) for n in re.findall(r'\d+', clean_txt)]
        if nums:
            data["rentang_harga"] = "-".join(nums)

    data["kategori_tempat"] = (
        await _get_text(page.locator('button[jsaction*="category"]').first)
        or await _get_text(page.locator('div[role="main"] span.DkEaL').first)
    )

    data["alamat_lengkap"] = await _get_label(
        page.locator('button[data-item-id="address"]').first,
        r"^(Alamat|Address):\s*",
    )

    data["nomor_telepon"] = await _get_label(
        page.locator('button[data-item-id^="phone"]').first,
        r"^(Telepon|Phone):\s*",
    )

    web_link = page.locator('a[data-item-id="authority"]').first
    if await web_link.count() > 0:
        href = await web_link.get_attribute("href")
        data["situs_web"] = href.strip() if href else ""

    main_div = page.locator('div[role="main"]')
    if await main_div.count() > 0:
        page_text = await main_div.inner_text()
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", page_text)
        if email_match:
            email = email_match.group()
            if not any(skip in email for skip in ["google.com", "gstatic.com", "gmail.com"]):
                data["email"] = email

    data["kode_lokasi_google"] = await _get_label(
        page.locator('button[data-item-id="oloc"], button[aria-label*="Plus code" i], button[aria-label*="Kode Plus" i]').first,
        r"^(Plus code|Kode Plus):\s*",
    )

    data["google_maps_url"] = page.url
    return data

def export_csv(leads, business_type, area, output_dir="."):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_type = re.sub(r"[^\w\-]", "_", business_type)
    safe_area = re.sub(r"[^\w\-]", "_", area)
    filepath = os.path.join(output_dir, f"{safe_type}_{safe_area}_{timestamp}.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(leads)
    return filepath

async def scrape(business_type, area, headless=True, output_dir="."):
    query = f"{business_type} di {area}"
    search_url = SEARCH_URL.format(query=query.replace(" ", "+"))
    sep = "=" * 60

    print(f"\n{sep}\nGoogle Maps Scraper\n{sep}")
    print(f"  Jenis usaha : {business_type}")
    print(f"  Wilayah     : {area}")
    print(f"  Query       : {query}")
    print(f"  Mode        : {'Visible (browser tampil)' if not headless else 'Headless (di latar belakang)'}")
    print(f"{sep}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,900",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        await apply_stealth(page)

        print("Membuka Google Maps...")
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            print("  networkidle timeout, melanjutkan proses...")

        await asyncio.sleep(3)
        print(f"  URL: {page.url[:80]}")

        await handle_consent(page)
        await asyncio.sleep(3)

        print("Scroll untuk memuat semua hasil...")
        places_data = await scroll_results(page)
        total_results = len(places_data)

        if total_results == 0:
            print("\nTidak ditemukan tempat untuk pencarian ini.")
            await browser.close()
            return

        print(f"\nTotal ditemukan: {total_results} tempat\n")
        print("Mengambil detail setiap tempat...\n")

        leads = []
        errors = 0

        for i, place in enumerate(places_data):
            print(f"  [{i+1}/{total_results}] {place['name'][:40]}...")
            try:
                await page.goto(place["url"], wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(1.5)
                details = await extract_place_details(page)
                if not details.get("nama_tempat"):
                    details["nama_tempat"] = place["name"]
                leads.append(details)

                nama = details.get("nama_tempat", "N/A")
                hp = details.get("nomor_telepon", "") or "-"
                rating = details.get("rating", "") or "-"
                web = "[Web]" if details.get("situs_web") else ""
                info_line = f"     {nama[:30]} | HP: {hp} | Rating: {rating}"
                if web:
                    info_line += f" | {web}"
                print(info_line)
            except Exception as e:
                print(f"     Error: {e}")
                errors += 1

            await asyncio.sleep(random.uniform(DETAIL_PAUSE_MIN, DETAIL_PAUSE_MAX))

            if (i + 1) % 20 == 0 and (i + 1) < total_results:
                print(f"\n[Pause] Sudah {i + 1} detail tempat diambil.")
                lanjut = await asyncio.to_thread(
                    input, "Lanjut ambil 20 data berikutnya? (y/n) [default: y]: "
                )
                if lanjut.strip().lower() == "n":
                    print("Proses dihentikan oleh pengguna. Menyimpan data yang sudah terkumpul...\n")
                    break
                print("Melanjutkan proses...\n")

        await browser.close()

    if leads:
        filepath = export_csv(leads, business_type, area, output_dir)
        print(f"\n{sep}\nSELESAI\n{sep}")
        print(f"  Total tempat ditemukan : {total_results}")
        print(f"  Berhasil diambil       : {len(leads)}")
        print(f"  Error / dilewati       : {errors}")
        print(f"  File disimpan ke       : {filepath}")
        print(f"{sep}\n")
    else:
        print(f"\nTidak ada data yang berhasil diambil ({errors} error).")

def main():
    parser = argparse.ArgumentParser(
        description="Google Maps Scraper - Ambil data bisnis dari Google Maps tanpa API key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py --type "angkringan" --area "purwokerto"
  python main.py --type "toko baju" --area "semarang" --visible
  python main.py --type "warung makan" --area "yogyakarta" --output-dir "./hasil"

Persiapan sebelum menjalankan:
  pip install -r requirements.txt
  playwright install chromium
        """,
    )
    parser.add_argument("--type", required=True, help='Jenis usaha (misal: "angkringan", "toko baju")')
    parser.add_argument("--area", required=True, help='Wilayah pencarian (misal: "purwokerto", "semarang")')
    parser.add_argument("--visible", action="store_true", help="Tampilkan browser saat proses berjalan")
    parser.add_argument("--output-dir", default="data", help="Folder output CSV (default: data)")
    args = parser.parse_args()

    asyncio.run(scrape(args.type, args.area, headless=not args.visible, output_dir=args.output_dir))

if __name__ == "__main__":
    main()
