import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from PIL import Image
import time
from paddleocr import PaddleOCR, draw_ocr
from io import BytesIO
from PIL import Image

ocr = PaddleOCR(use_angle_cls=True, lang='en')
def solve_captcha(image_element):
    # Capture image screenshot and convert to base64
    image_png = image_element.screenshot_as_png
    image = Image.open(BytesIO(image_png)).convert('RGB')
    
    # Step 2: Convert PIL image to numpy array
    img_np = np.array(image)
    
    # Step 3: Run OCR
    result = ocr.ocr(img_np, rec=True)
    
    # Step 4: Extract text from result
    if not result or not result[0]:
        print("[OCR] No text detected.")
        return ""
    
    detected_text = result[0][0][1][0]  # First block's first line's text
    print(f"[OCR] CAPTCHA text: {detected_text}")
    try:
        # Optional: Visualize and save the result
        boxes = [line[0] for line in result[0]]
        txts = [line[1][0] for line in result[0]]
        scores = [line[1][1] for line in result[0]]
        im_show = draw_ocr(img_np, boxes, txts, scores)
        im_show = Image.fromarray(im_show)
        im_show.save('captcha_result.jpg')
    except Exception as e:
        print(e)
    return detected_text

# === Selenium setup ===
chromedriver_autoinstaller.install()
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 15)

try:
    driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
    court_orders_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#leftPaneMenuCO")))
    court_orders_btn.click()
    time.sleep(5)
    close_the_add = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#validateError > div > div > div.modal-header.text-center.align-items-start > button')))
    if close_the_add:
        close_the_add.click()
    # Wait for state dropdown
    wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
    state_select = Select(driver.find_element(By.ID, "sess_state_code"))
    state_options = state_select.options[1:]  # skip "Select State"

    for state_option in state_options:
        state_value = state_option.get_attribute("value")
        state_name = state_option.text.strip()
        print(f"\n🔹 State: {state_name}")
        state_select.select_by_value(state_value)
        time.sleep(1.5)

        district_select = Select(wait.until(EC.presence_of_element_located((By.ID, "sess_dist_code"))))
        district_options = district_select.options[1:]

        for district_option in district_options:
            district_value = district_option.get_attribute("value")
            district_name = district_option.text.strip()
            print(f"   - District: {district_name}")
            district_select.select_by_value(district_value)
            time.sleep(1.5)
            Complax_select = Select(wait.until(EC.presence_of_element_located((By.ID, "court_complex_code"))))
            court_select_options = Complax_select.options[1:]
            for c_idx in court_select_options:
                c_idx_value = c_idx.get_attribute("value")
                Court_complax_name = c_idx.text.strip()
                print(f"   - Complax: {Court_complax_name}")
                try:
                    Complax_select.select_by_value(c_idx_value)
                except:c_idx= None
                time.sleep(1.5)
                order_date_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#orderdate-tabMenu")))
                order_date_tab.click()
                time.sleep(5)
                order_date_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#radBothorderdt")))
                order_date_tab.click()
                time.sleep(5)
                # Fill in order date
                date_value = "01-05-2024"
                date_from = driver.find_element(By.ID, "from_date")
                date_to = driver.find_element(By.ID, "to_date")
                date_from.send_keys(date_value)
                date_to.send_keys(date_value)

                # Solve CAPTCHA
                captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))
                captcha_text = solve_captcha(captcha_img)
                print(f"      - CAPTCHA Solved: {captcha_text}")

                captcha_input = driver.find_element(By.ID, "order_date_captcha_code")
                # captcha_input.clear()
                captcha_input.send_keys(captcha_text)
                time.sleep(2)
                court_orders_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#frm_search_od_date > div:nth-child(5) > div.col-md-auto > button")))
                court_orders_btn.click()
                time.sleep(10)
                print(f"Extracted PDF links:-")
                if 'Record not found' in driver.page_source:
                    break
                # here extract pdf links
                pdf_links = Select(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, " a.someclass"))))
                extract_pdf_links = pdf_links.options[1:]
                for pdf_link in extract_pdf_links:
                    aa = pdf_link.get_attribute("onclick")
                    pdf_linksss = f"https://services.ecourts.gov.in/ecourtindia_v6/?p={aa}"
                    print(f"      -{pdf_link}")
                #break here to test only the first district per state
                break
            # break to test only the first state
            break
finally:
    time.sleep(10)
    driver.quit()
