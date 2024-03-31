from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import csv
import pandas as pd

keywords = ["중구", "영화"]

try:
    df_existing = pd.read_csv('activity_info.csv', encoding='utf-8')
except FileNotFoundError:
    df_existing = pd.DataFrame(columns=['name', 'address', 'tags', 'rate', 'ID', 'iamge_URL'])

options = Options()
options.add_experimental_option('detach', True)
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=webdriver.chrome.service.Service(driver_path), options=options)
driver.get("https://m.map.naver.com/search2/search.naver?")
time.sleep(1)

search = driver.find_element(By.CSS_SELECTOR,"input.input_search_keyword._keyword[title='검색어 입력'][placeholder='장소, 주소 검색']")
search.click()
search = driver.find_element(By.CSS_SELECTOR,"input.keyword_search_input._search_input[name='search_query'][title='검색어 입력'][placeholder='장소, 주소 검색']")
search.click()
keyword = ','.join(keywords)
search.send_keys(keyword)
search.send_keys(Keys.ENTER)
time.sleep(1.5)

rate = 5.0
result_list = []
place_info_list = []

for i in range(1, 100):  
    try:
        link_selector = f'a.a_item.a_item_distance._linkSiteview[data-rank="{i}"]'
        search = driver.find_element(By.CSS_SELECTOR, link_selector)
        search.click()
        time.sleep(2.6)

        try:
            # 상호명
            place_name_element = driver.find_element(By.CSS_SELECTOR, 'span.Fc1rA')
            place_name = place_name_element.text

            if place_name in df_existing['name'].values:
                existing_tags = df_existing.loc[df_existing['name'] == place_name, 'tags'].values[0]
                new_tags = ', '.join(list(set(existing_tags.split(', ') + keywords)))
                df_existing.loc[df_existing['name'] == place_name, 'tags'] = new_tags
                print(f"{place_name}은(는) 데이터프레임에 이미 존재합니다. 태그를 업데이트합니다...")
                previous_page_button = driver.find_element(By.CSS_SELECTOR, 'a.DDfpb')
                previous_page_button.click()
                time.sleep(0.1)
                continue

            # 주소 
            place_address_element = driver.find_element(By.CSS_SELECTOR, 'span.LDgIH')
            place_address = place_address_element.text

            # URL에서 숫자만 추출하기
            url = driver.current_url
            restaurant_id_match = re.search(r'/(\d+)/', url)
            if restaurant_id_match:
                restaurant_id = restaurant_id_match.group(1)
            else:
                print("식당 ID를 찾을 수 없습니다.")

            # 이미지 URL
            element = driver.find_element(By.ID, 'ibu_1')
            background_image = element.value_of_css_property('background-image')
            url = re.search(r'url\("(.*)"\)', background_image).group(1)

            result_list.append((place_name, place_address, keywords, rate, restaurant_id, url))
        except NoSuchElementException:
            print(f"rank={i}의 요소를 찾을 수 없습니다.")
        except Exception as e:
            print(f"rank={i}를 처리하는 동안 오류가 발생했습니다: {e}")

        previous_page_button = driver.find_element(By.CSS_SELECTOR, 'a.DDfpb')
        previous_page_button.click()
        time.sleep(0.1)
    except:
        break


# 새로운 데이터 추가
df = pd.DataFrame(result_list, columns=['name', 'address', 'tags', 'rate', 'ID', 'iamge_URL'])
df_all = pd.concat([df_existing, df])

# 데이터프레임을 CSV 파일로 저장
df_all.to_csv('activity_info_v3.csv', index=False, encoding='utf-8')

driver.quit()
