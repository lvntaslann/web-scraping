import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Tarayıcı Ayarları ===
driver_path = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(driver_path), options=options)
wait = WebDriverWait(driver, 10)

# === Derinlik (depth) Hesapla ===
def get_depth(div):
    style = div.get_attribute("style") or ""
    if "padding-left" in style:
        px = int(style.split("padding-left:")[1].split("px")[0])
        return px // 16
    return 0

# === Kategori Bilgisi Çıkar ===
def extract_info(div):
    try:
        a = div.find_element(By.XPATH, ".//a[@href and @title]")
        return {
            "title": a.get_attribute("title").strip(),
            "href": a.get_attribute("href").strip(),
            "children": []
        }
    except:
        return None

# === Açılabilir Kategori Toggle Butonu Varsa Bul ===
def find_toggle(div):
    try:
        return div.find_element(By.XPATH, ".//i[contains(@class,'tree-b_')]")
    except:
        return None

# === Kategori Ağacını Rekürsif Olarak Tara ===
def scrape_recursive(url, visited=None):
    if visited is None:
        visited = set()

    driver.get(url)
    time.sleep(2)

    try:
        container = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='tree-container']")))
    except:
        print(f"Kategori ağacı bulunamadı: {url}")
        return []

    categories = []
    stack = []
    clicked = set()
    divs = container.find_elements(By.XPATH, "./div[contains(@class,'tree-')]")
    i = 0

    while i < len(divs):
        div = divs[i]
        depth = get_depth(div)
        info = extract_info(div)
        toggle = find_toggle(div)

        if info:
            key = (info["href"], info["title"])
            if key in visited:
                i += 1
                continue
            visited.add(key)

            while len(stack) > depth:
                stack.pop()

            parent = stack[-1] if stack else None
            if parent:
                if not any(ch["href"] == info["href"] for ch in parent["children"]):
                    parent["children"].append(info)
            else:
                if not any(ch["href"] == info["href"] for ch in categories):
                    categories.append(info)

            stack.append(info)

        if toggle and div not in clicked:
            clicked.add(div)
            driver.execute_script("arguments[0].click()", toggle)
            time.sleep(0.5)
            divs = container.find_elements(By.XPATH, "./div[contains(@class,'tree-')]")
            continue

        i += 1

    for cat in categories:
        # Sadece gerçekten alt kategori varsa ekle
        child_tree = scrape_recursive(cat["href"], visited)
        if child_tree:
            cat["children"] = child_tree

    return categories

# === Ana Kategoriyi Al (Root) ===
def get_root_category(url):
    driver.get(url)
    time.sleep(2)
    try:
        a = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='tree-container']//a[@href and @title]")))
        return {
            "title": a.get_attribute("title").strip(),
            "href": a.get_attribute("href").strip(),
            "children": []
        }
    except:
        return None

# === Kategorileri Başlat ===
def scrape_full_tree(start_url):
    root = get_root_category(start_url)
    if not root:
        print("Root kategori alınamadı.")
        return {}

    print(f"Başlangıç: {root['title']}")
    visited = {(root["href"], root["title"])}
    root["children"] = scrape_recursive(start_url, visited)

    return root

# === Kategori ve Süperkategori Etiketleri Ekle ===
def add_category_and_supercategory_fields(node, depth=0, depth1_title=None):
    node["category"] = node["title"]

    if depth == 1:
        depth1_title = node["title"]
    if depth >= 2 and depth1_title:
        node["supercategory"] = depth1_title

    for child in node.get("children", []):
        add_category_and_supercategory_fields(child, depth + 1, depth1_title)

# === Çalıştır ===
start_url = "https://www.hepsiburada.com/oyunlar-oyun-konsollari-c-2147483602" 

full_tree = scrape_full_tree(start_url)
add_category_and_supercategory_fields(full_tree)

with open("category/oyun-ve-oyun-konsollari.json", "w", encoding="utf-8") as f:
    json.dump(full_tree, f, indent=2, ensure_ascii=False)

print("Tüm kategori ağacı çıkarıldı ve kaydedildi.")
driver.quit()



















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
CATEGORY_JSON_PATH = "category/foto-kameralari.json"
BASE_OUTPUT_DIR = "datav3"
SUPER_CATEGORY_BULK_SAVE = ["Foto / Kamera"]

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
    supercategory = node.get("supercategory",current_title)

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
