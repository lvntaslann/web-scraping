import os
import json
import time
import random
import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from slugify import slugify

# === Ayarlar ===
DRIVER_PATH = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
CATEGORY_JSON_PATH = "category_updated.json"
BASE_OUTPUT_DIR = "datav3"
SUPER_CATEGORY_BULK_SAVE = ["bilgisayar sistemleri ve ekipmanları"]

def human_like_delay(min_sec=0.5, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))

def fix_categories(products, folder_path):
    parent_dir = os.path.basename(os.path.dirname(folder_path))
    parent_dir = parent_dir.replace("-", " ").title()

    for product in products:
        category = product.get("category", "").lower()
        if category == "muadil":
            product["category"] = f"{parent_dir}-muadil"
        elif category in ["orijinal", "orjinal"]:
            product["category"] = f"{parent_dir}-orijinal"
    return products

def scrape_product_data(driver, url, supercategory, current_title, parent_title, folder_path):
    products = []
    cards = driver.find_elements(By.CSS_SELECTOR, ".productCard-module_productCardRoot__Yf7qs")
    product_links = driver.find_elements(By.CSS_SELECTOR, ".productCard-module_article__HJ97o")

    for idx, card in enumerate(cards):
        model = title = price = "N/A"
        try:
            model = card.find_element(By.CSS_SELECTOR, ".title-module_brandText__GIxWY").text.strip()
        except: pass
        try:
            title = card.find_element(By.CSS_SELECTOR, ".title-module_titleText__8FlNQ").text.strip()
        except: pass
        try:
            price = card.find_element(By.CSS_SELECTOR, ".price-module_finalPrice__LtjvY").text.strip()
        except:
            try:
                price = card.find_element(By.CSS_SELECTOR, "[data-test-id='price-current-price']").text.strip()
            except: pass
        try:
            link_element = product_links[idx].find_element(By.TAG_NAME, "a")
            product_url = link_element.get_attribute("href").strip()
        except:
            product_url = url

        adjusted_category = current_title

        products.append({
            "model": model,
            "title": title,
            "price": price,
            "category_url": url,
            "product_url": product_url,
            "category": adjusted_category,
            "supercategory": supercategory
        })

    products = fix_categories(products, folder_path)

    return products

def scrape_category(driver, url, folder_path, current_title, supercategory, parent_title):
    super_slug = slugify(supercategory or "").lower()
    is_supercat_bulk = super_slug in [slugify(name) for name in SUPER_CATEGORY_BULK_SAVE]

    os.makedirs(folder_path, exist_ok=True)
    all_products = []
    seen_urls = set()
    page = 1

    while True:
        paged_url = f"{url}?sayfa={page}"
        print(f"\nSayfa {page} yükleniyor: {paged_url}")
        driver.get(paged_url)
        human_like_delay(2.0, 4.0)

        products = scrape_product_data(driver, paged_url, supercategory, current_title, parent_title, folder_path)
        if not products:
            print("Yeni ürün bulunamadı, duruluyor.")
            break

        new_unique = [p for p in products if p["product_url"] not in seen_urls]
        if not new_unique:
            print("Yeni ürün kalmadı (URL'e göre), duruluyor.")
            break

        for p in new_unique:
            seen_urls.add(p["product_url"])

        if is_supercat_bulk:
            all_products.extend(new_unique)
        else:
            page_filename = f"page_{page}.json"
            page_path = os.path.join(folder_path, page_filename)
            with open(page_path, "w", encoding="utf-8") as f:
                json.dump(new_unique, f, ensure_ascii=False, indent=2)
            print(f"Sayfa kaydedildi: {page_path}")

        page += 1
        human_like_delay(1.0, 2.5)

    if is_supercat_bulk and all_products:
        title_slug = slugify(current_title)
        file_name = f"{title_slug}_{len(all_products)}.json"
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        print(f"\nTüm ürünler topluca kaydedildi: {file_path}")

def process_category_tree(driver, node, parent_path, depth=0, parent_title=None):
    current_title = node["title"]
    current_slug = slugify(current_title)
    current_path = os.path.join(parent_path, current_slug)
    supercategory = node.get("supercategory", "Bilinmeyen")

    if node.get("children"):
        for child in node["children"]:
            process_category_tree(driver, child, current_path, depth + 1, parent_title=current_title)

        # Alt klasörleri birleştir
        merged = []
        for path in glob.glob(os.path.join(current_path, "*", "*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged.extend(data)
            except Exception as e:
                print(f"Hata: {path} ({e})")

        if merged:
            output_file = os.path.join(current_path, f"all_products_{slugify(current_title)}_{len(merged)}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            print(f"\nAlt kategoriler birleştirildi: {output_file}")
    else:
        scrape_category(
            driver=driver,
            url=node["href"],
            folder_path=current_path,
            current_title=current_title,
            supercategory=supercategory,
            parent_title=parent_title
        )

def merge_all_product_files(base_dir):
    merged = []
    for path in glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True):
        if "all_products" in path:
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    data = fix_categories(data, path)
                    merged.extend(data)
        except Exception as e:
            print(f"Hata: {path} ({e})")

    output = os.path.join(base_dir, f"all_products_{len(merged)}.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\nTüm ürünler birleştirildi: {output} ({len(merged)} ürün)")

if __name__ == "__main__":
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        with open(CATEGORY_JSON_PATH, "r", encoding="utf-8") as f:
            tree = json.load(f)

        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        process_category_tree(driver, tree, BASE_OUTPUT_DIR)

    finally:
        merge_all_product_files(BASE_OUTPUT_DIR)
        driver.quit()
        print("\nTüm işlemler tamamlandı.")
