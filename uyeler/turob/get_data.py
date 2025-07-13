from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import os
import time

# Chrome ayarları
driver_path = r"C:\Users\kurt_\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

veriler = []

def modal_acik_mi():
    modallar = driver.find_elements(By.CSS_SELECTOR, "div.modal.fade.in")
    for modal in modallar:
        display = modal.value_of_css_property("display")
        if display == "block":
            return True
    return False

sayfa = 0
while True:
    url = f"https://www.turob.com/tr/uyelerimiz/category/tum-uyelerimiz?start={sayfa * 12}"
    print(f"\n📄 Sayfa açılıyor: {url}")
    driver.get(url)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul#listPage")))
    except TimeoutException:
        print("Sayfa yüklenemedi veya liste bulunamadı, bitiriliyor.")
        break

    otel_butonlari = driver.find_elements(By.CSS_SELECTOR, "a.Detail")
    if not otel_butonlari:
        print("Otel listesi boş, bitiriliyor.")
        break

    for index in range(len(otel_butonlari)):
        print(f"\n➡️ {sayfa * 12 + index + 1}. üye işleniyor...")

        try:
            # Eğer açık modal varsa kapat
            if modal_acik_mi():
                try:
                    kapat_btn = driver.find_element(By.CSS_SELECTOR, "div.modal.fade.in button.close")
                    kapat_btn.click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.fade.in")))
                    time.sleep(0.5)
                except:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)

            otel_butonlari = driver.find_elements(By.CSS_SELECTOR, "a.Detail")
            buton = otel_butonlari[index]

            # Buton tıklanabilir olana kadar bekle
            wait.until(EC.element_to_be_clickable(buton))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buton)
            time.sleep(0.5)
            buton.click()

            # Gerçek modal'ı yakala
            def aktif_modal_yuklendi(driver):
                modallar = driver.find_elements(By.CSS_SELECTOR, "div.modal.fade")
                for modal in modallar:
                    display = modal.value_of_css_property("display")
                    class_attr = modal.get_attribute("class")
                    if display == "block" and "in" in class_attr:
                        try:
                            baslik = modal.find_element(By.CSS_SELECTOR, "h2.modal-title").text.strip()
                            if baslik:
                                return modal
                        except:
                            continue
                return False

            aktif_modal = WebDriverWait(driver, 10).until(aktif_modal_yuklendi)

            # Veri çekme
            firma = aktif_modal.find_element(By.CSS_SELECTOR, "h2.modal-title").text.strip()

            try:
                rating_src = aktif_modal.find_element(By.CSS_SELECTOR, "img.Stars").get_attribute("src")
            except NoSuchElementException:
                rating_src = ""

            bilgiler = aktif_modal.find_elements(By.CSS_SELECTOR, "div.HotelProperties p")

            adres = ""
            telefon = ""
            fax = "N/A"
            email = ""
            web = ""

            for p in bilgiler:
                text = p.text.strip()
                # Fax img kontrolü için parent p içindeki img alt text veya src kontrolü yap
                try:
                    img = p.find_element(By.TAG_NAME, "img")
                    img_alt = img.get_attribute("alt").lower()
                    img_src = img.get_attribute("src").lower()
                    if "fax" in img_alt or "fax" in img_src:
                        fax = text
                        continue
                except NoSuchElementException:
                    pass

                if "@" in text and not email:
                    email = text
                elif ("http" in text or "www" in text) and not web:
                    web = text
                elif not adres:
                    adres = text
                elif not telefon:
                    telefon = text

            print(f"🏨 {firma} | 📍 {adres} | ☎️ {telefon} | Fax: {fax} | 📧 {email} | 🌐 {web} | ⭐ {rating_src}")

            veriler.append({
                "title": firma,
                "adress": adres,
                "telefon": telefon,
                "fax": fax,
                "email": email,
                "website": web,
                "rating": rating_src
            })

            # Modalı kapat
            close_btn = aktif_modal.find_element(By.CSS_SELECTOR, "button.close")
            close_btn.click()
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.fade.in")))
            time.sleep(0.5)

        except Exception as e:
            print(f"Hata oluştu: {e}")
            try:
                if modal_acik_mi():
                    kapat_btn = driver.find_element(By.CSS_SELECTOR, "div.modal.fade.in button.close")
                    kapat_btn.click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.fade.in")))
                    time.sleep(0.5)
                else:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
            except:
                pass
            continue

    # Her sayfa verisini klasöre kaydet
    klasor = f"data/page{sayfa+1}"
    os.makedirs(klasor, exist_ok=True)
    with open(os.path.join(klasor, f"page{sayfa+1}_oteller.json"), "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

    sayfa += 1

driver.quit()

# Tüm veriyi tek dosyada kaydet
with open("turob_oteller.json", "w", encoding="utf-8") as f:
    json.dump(veriler, f, ensure_ascii=False, indent=4)
