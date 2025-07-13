import time, json
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
wait = WebDriverWait(driver, 10)

def get_depth(div):
    style = div.get_attribute("style") or ""
    if "padding-left" in style:
        px = int(style.split("padding-left:")[1].split("px")[0])
        return px // 16
    return 0


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

# kategori toggle butonunu tespit etme
def find_toggle(div):
    try:
        return div.find_element(By.XPATH, ".//i[contains(@class,'tree-b_')]")
    except:
        return None

# kategori ağacını çıkar 
def scrape_recursive(url, visited=None, skip_titles=None):
    if visited is None:
        visited = set()
    if skip_titles is None:
        skip_titles = set()

    if url in visited:
        return []

    visited.add(url)
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

        if info and info["title"] not in skip_titles:
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

    # alt kategorileri de tara
    for cat in categories:
        new_skip = skip_titles.union({cat["title"]})
        cat["children"] = scrape_recursive(cat["href"], visited, skip_titles=new_skip)

    return categories


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


def scrape_full_tree(start_url):
    root = get_root_category(start_url)
    if not root:
        print("Root kategori alınamadı.")
        return {}

    print(f"Başlangıç: {root['title']}")
    skip_titles = {root["title"]}
    root["children"] = scrape_recursive(start_url, skip_titles=skip_titles)
    return root

# Her node'a category ve supercategory alanlarını ekle
def add_category_and_supercategory_fields(node, depth=0, depth1_title=None):
    node["category"] = node["title"]

    if depth == 1:
        depth1_title = node["title"]
    if depth >= 2 and depth1_title:
        node["supercategory"] = depth1_title

    for child in node.get("children", []):
        add_category_and_supercategory_fields(child, depth + 1, depth1_title)


# Başlat
start_url = "https://www.hepsiburada.com/bilgisayar-sistemleri-ve-ekipmanlari-c-2147483646"
full_tree = scrape_full_tree(start_url)

# category & supercategory alanlarını ekle
add_category_and_supercategory_fields(full_tree)

# Dosyaya yaz
with open("category_v2.json", "w", encoding="utf-8") as f:
    json.dump(full_tree, f, indent=2, ensure_ascii=False)

print("Tüm kategori ağacı çıkarıldı ve kaydedildi.")
driver.quit()