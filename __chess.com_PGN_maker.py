
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import random


username = 'afonsonoia'

target_url = "https://www.chess.com/games/archive/" + username

global client

SELENIUM = True
DEBUG = False
incremento_expresso = 0.0005
MINIMIZAR = False

options = Options()
options.add_experimental_option('detach', False)

proxies_database = []
proxies_database.append('104.16.241.204:80')
proxies_database.append('195.93.200.140:80')
proxies_database.append('51.75.173.161:1080')
proxies_database.append('138.201.92.34:1080')
proxies_database.append('2.137.22.252:4153')
proxies_database.append('51.52.205.98:4153')
proxies_database.append('185.97.122.253:4153')
proxies_database.append('103.83.36.1:5678')
proxies_database.append('50.47.75.220:5678')
proxies_database.append('176.74.118.133:5678')
proxies_database.append('108.28.33.157:8080')
proxies_database.append('65.21.131.87:14141')
proxies_database.append('62.94.218.90:15589')
proxies_database.append('46.101.159.7:31162')
proxies_database.append('68.183.221.156:34297')
proxies_database.append('185.66.59.77:42647')


und_options = uc.ChromeOptions()
proxie_index = random.randint(0, len(proxies_database)-1)
und_options.add_argument(str("proxy-server=" + proxies_database[proxie_index]))

if SELENIUM:
    driver = webdriver.Chrome()
else:
    driver = uc.Chrome(options=und_options)

if MINIMIZAR:
    driver.minimize_window()
else:
    driver.maximize_window()

driver.get(target_url)

arr_games = []
time.sleep(1)

# remove cookies
worked = False
while not worked:
    try:
        elem_refuse_cookies = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/button[3]')
        worked = True
    except:
        print("didn't work")
        time.sleep(1)
elem_refuse_cookies.click()
time.sleep(1)



# set to live
live_btn = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/main/div[1]/div[2]/div[1]/div[1]/a[3]')
live_btn.click()

time.sleep(2)



# click in a game
# //*[@id="games-root-index"]/div[2]/div/div[2]/nav/button[7]

games_urls = []
first_page = True
while True:
    try:
        for i in range(50):
            xpath = '//*[@id="games-root-index"]/div[3]/table/tbody/tr[' + str(i+1) + ']/td[2]/a'
            game_elem = driver.find_element(By.XPATH, xpath)  # Fix the XPath expression here
            link = game_elem.get_attribute('href')
            if link not in games_urls:
                games_urls.append(link)
                print(link)

        # get next page
        # /html/body/div[1]/div[2]/main/div[1]/div[2]/div[2]/div/div[2]/nav/button[6]
        # /html/body/div[2]/div[2]/main/div[1]/div[2]/div[2]/div/div[2]/nav/button[6]
        if first_page:
            next_page_btn = driver.find_element(By.XPATH, '//*[@id="games-root-index"]/div[2]/div/div[2]/nav/button[6]')
        else:
            next_page_btn = driver.find_element(By.XPATH, '//*[@id="games-root-index"]/div[2]/div/div[2]/nav/button[7]')

        next_page_btn.click()
        first_page = False
        time.sleep(2)
    except:
        break

time.sleep(12345)


if download_btn.get_attribute("aria-label") == 'Download':
    download_btn.click()
    print("pressed btn")

print("getting textbox pgn")
# get pgn from textbox
xpath = '/html/body/div[7]/div/div[2]/div/section/div[1]/div[2]/textarea'
tb_pgn = driver.find_element(By.XPATH, xpath)

if tb_pgn.get_attribute("name") != 'pgn':
    print(f"ERROR: wrong tb_pgn.name - {tb_pgn.get_attribute('name')}")

print("\npgn bellow:\n")

pgn_txt = tb_pgn.get_attribute('value')
print(pgn_txt)

time.sleep(5)
driver.close()








