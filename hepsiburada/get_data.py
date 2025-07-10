import os
import json
import time
import random
import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from slugify import slugify

# === KONFİGÜRASYON ===
DRIVER_PATH = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
CATEGORY_JSON_PATH = "kategori_agaci.json"
BASE_OUTPUT_DIR = "data"
MAX_RETRIES = 3
MAX_PRODUCTS_PER_CATEGORY = 500


"""
Veriler başlangıçta sayfa sonsuz kaydırılarak yükleniyor
ilk 4 sayfadan sonra "Daha fazla göster" butonu oluşuyor
butona 3-5 defa basıldıktan sonra button işlevsiz oluyor

"""
def human_like_delay(min_sec=0.5, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))

def safe_find_element(driver, by, value, timeout=10):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except:
        return None

def safe_click(element, driver, retries=3):
    for _ in range(retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            human_like_delay(0.5, 1.0)
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            human_like_delay(1, 2)
    return False

# === SCROLL VE BUTON KONTROL ===
def scroll_page(driver):
    offset = random.randint(1200, 1800)
    driver.execute_script(f"window.scrollBy(0, {offset});")
    human_like_delay(1.0, 2.5)

def handle_load_more_button(driver, click_limit=5):
    try:
        button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='load-more-button']:not([disabled])"))
        )
        if button.is_displayed():
            print("  'Daha fazla ürün göster' butonu bulundu, tıklanıyor...")
            success = safe_click(button, driver)
            if success:
                human_like_delay(2.0, 4.0)
                return True
            else:
                print("Butona tıklanamadı.")
    except:
        pass
    return False

def load_all_products(driver, max_products=None):
    last_count = 0
    no_progress_attempts = 0
    load_more_clicks = 0
    MAX_NO_PROGRESS = 5
    MAX_LOAD_MORE_CLICKS = 5

    while True:
        scroll_page(driver)

        current_products = driver.find_elements(By.CSS_SELECTOR, ".productCard-module_productCardRoot__Yf7qs")
        current_count = len(current_products)

        if current_count > last_count:
            print(f"  Yeni ürünler yüklendi! Toplam: {current_count} (+{current_count - last_count})")
            last_count = current_count
            no_progress_attempts = 0
        else:
            no_progress_attempts += 1
            print(f"  Yeni ürün yüklenmedi. Deneme: {no_progress_attempts}/{MAX_NO_PROGRESS}")

        if load_more_clicks < MAX_LOAD_MORE_CLICKS:
            if handle_load_more_button(driver):
                load_more_clicks += 1
                print(f"  Butona tıklama sayısı: {load_more_clicks}/{MAX_LOAD_MORE_CLICKS}")
                continue

        if max_products and current_count >= max_products:
            print(f"  Limit {max_products} ürüne ulaşıldı. Yükleme sonlandırılıyor.")
            break

        if no_progress_attempts >= MAX_NO_PROGRESS:
            print("  Ürün yüklenmesi durdu, buton yok ya da tıklanamadı. İşlem bitiyor.")
            break

        human_like_delay(1.5, 3.0)

    print(f"\nToplam {last_count} ürün yüklendi.")
    return last_count

# === ÜRÜN VERİSİ ÇEKME ===
def scrape_product_data(driver, url, max_products=None):
    products = []
    cards = driver.find_elements(By.CSS_SELECTOR, ".productCard-module_productCardRoot__Yf7qs")

    for index, card in enumerate(cards, 1):
        try:
            model = card.find_element(By.CSS_SELECTOR, ".title-module_brandText__GIxWY").text.strip()
        except:
            model = "N/A"

        try:
            title = card.find_element(By.CSS_SELECTOR, ".title-module_titleText__8FlNQ").text.strip()
        except:
            title = "N/A"

        try:
            price = card.find_element(By.CSS_SELECTOR, ".price-module_finalPrice__LtjvY").text.strip()
        except:
            try:
                price = card.find_element(By.CSS_SELECTOR, "[data-test-id='price-current-price']").text.strip()
            except:
                price = "N/A"

        try:
            product_url = card.find_element(By.CSS_SELECTOR, "a[href]").get_attribute("href")
        except:
            product_url = url

        products.append({
            "model": model,
            "title": title,
            "price": price,
            "url": product_url
        })

        if index % 20 == 0:
            print(f"  {index}/{len(cards)} ürün işlendi...")
            human_like_delay(1, 2)

        if max_products and len(products) >= max_products:
            break

    return products

# === Her kategoriyi tek tek scrape işlemi ===
def scrape_category(url, folder_path, category_title, max_products=None):
    for attempt in range(MAX_RETRIES):
        try:
            print(f"\nScraping başlatılıyor (Deneme {attempt + 1}/{MAX_RETRIES}): {url}")
            driver.get(url)
            human_like_delay(3, 5)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".productCard-module_productCardRoot__Yf7qs"))
            )

            load_all_products(driver, max_products=max_products)
            products = scrape_product_data(driver, url, max_products=max_products)

            if products:
                os.makedirs(folder_path, exist_ok=True)
                file_name = f"{slugify(category_title)}_{len(products)}.json"
                save_path = os.path.join(folder_path, file_name)

                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)

                print(f"\nBaşarıyla kaydedildi: {file_name} ({len(products)} ürün)")
                return True

        except Exception as e:
            print(f"\nHata oluştu (Deneme {attempt + 1}): {str(e)}")
            human_like_delay(5, 10)

    print(f"\n{MAX_RETRIES} deneme sonunda başarısız oldu: {url}")
    return False


def process_category_tree(node, parent_path):
    title = node["title"]
    title_slug = slugify(title)
    current_path = os.path.join(parent_path, title_slug)

    scrape_category(
        url=node["href"],
        folder_path=current_path,
        category_title=title,
        max_products=MAX_PRODUCTS_PER_CATEGORY
    )

    for child in node.get("children", []):
        process_category_tree(child, current_path)

# === Tüm ürünleri json olarak birleştirme ===
def merge_all_product_files(base_dir):
    merged_products = []
    for file_path in glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged_products.extend(data)
        except Exception as e:
            print(f"Dosya okunamadı: {file_path} ({e})")

    output_file = os.path.join(base_dir, f"all_products_{len(merged_products)}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_products, f, ensure_ascii=False, indent=2)

    print(f"\nTüm ürünler birleştirildi: {output_file} ({len(merged_products)} ürün)")

# === Main ===
if __name__ == "__main__":
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")

    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ? 
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
    })

    try:
        with open(CATEGORY_JSON_PATH, "r", encoding="utf-8") as f:
            category_tree = json.load(f)

        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        process_category_tree(category_tree, BASE_OUTPUT_DIR)

    finally:
        merge_all_product_files(BASE_OUTPUT_DIR)
        driver.quit()
        print("\nTüm scraping işlemi tamamlandı.")
