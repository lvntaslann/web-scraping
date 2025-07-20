import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver_path = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(driver_path), options=options)
wait = WebDriverWait(driver, 12)

def get_depth(div):
    try:
        spans = div.find_elements(By.XPATH, ".//span[starts-with(@class, 'indent-')]")
        return len(spans)
    except:
        return 0

def extract_info(div):
    try:
        a = div.find_element(By.XPATH, ".//a[@href and @title]")
        title = a.get_attribute("title").strip()
        return {
            "title": title,
            "href": a.get_attribute("href").strip(),
            "category": title,
            "children": [],
            "depth": get_depth(div)
        }
    except:
        return None

def find_toggle(div):
    try:
        return div.find_element(By.XPATH, ".//i[contains(@class,'tree-b_')]")
    except:
        return None

def scrape_recursive(url):
    driver.get(url)
    time.sleep(3)

    try:
        container = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='tree-container']")))
    except:
        print(f"Kategori ağacı bulunamadı: {url}")
        return []

    categories = []
    stack = []
    clicked = set()
    seen = set()
    last_depth2_title = None

    while True:
        divs = container.find_elements(By.XPATH, "./div[contains(@class,'tree-')]")
        changed = False

        for div in divs:
            if div in seen:
                continue
            seen.add(div)

            info = extract_info(div)
            if not info:
                continue

            depth = info["depth"]
            print("  " * depth + f"- {info['title']} (depth: {depth})")

            if depth == 2:
                last_depth2_title = info["title"]

            if depth >=3 and last_depth2_title:
                info["supercategory"] = last_depth2_title

            while stack and stack[-1]["depth"] >= depth:
                stack.pop()

            if stack:
                stack[-1]["children"].append(info)
            else:
                categories.append(info)

            stack.append(info)

            toggle = find_toggle(div)
            if toggle and div not in clicked:
                try:
                    driver.execute_script("arguments[0].click();", toggle)
                    clicked.add(div)
                    time.sleep(2)
                    changed = True
                    break
                except Exception as e:
                    print(f"Tıklama hatası: {e}")

        if not changed:
            break

    def clean_depth(obj):
        obj.pop("depth", None)
        for child in obj["children"]:
            clean_depth(child)
        return obj

    return [clean_depth(cat) for cat in categories]



if __name__ == "__main__":
    url = "https://www.hepsiburada.com/ev-elektronik-urunleri-c-2147483638"
    all_categories = scrape_recursive(url)

    with open("category/elektronik/ev-elektronik.json", "w", encoding="utf-8") as f:
        json.dump(all_categories, f, indent=2, ensure_ascii=False)

    print("Tüm kategori ağacı çıkarıldı ve JSON dosyasına kaydedildi.")
    driver.quit()
