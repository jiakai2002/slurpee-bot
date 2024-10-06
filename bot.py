import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from webdriver_manager.chrome import ChromeDriverManager
import requests


TOKEN = '7517178968:AAGue6Q8ETrZ9jlGhzPSy20rNI7mMHwySCs'
GEOCODING_API_KEY = 'dceab69062714d3292f82b006d0c012b'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = [
    [KeyboardButton("Share Location", request_location=True)]
]


def get_stores(address):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)
    driver.maximize_window()
    driver.get('https://www.7-eleven.com.sg/find-store')
    input_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))
    input_field.send_keys(address)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".no-scrollbar .flex.cursor-pointer"))).click()
    wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__next"]/div[3]/div[2]/div[2]/div[2]/div/div[3]/div[2]'))).click()

    store_elements = driver.find_element(By.XPATH, '//*[@id="__next"]/div[3]/div[2]/div[1]/div[2]/div[2]')
    store_elements = store_elements.find_elements(By.CSS_SELECTOR, '.cursor-pointer')
    # Extract addresses, timings, and distances
    store_data = []
    i = 0
    for store in store_elements:
        if (i == 5):
            break
        address = store.find_element(By.CSS_SELECTOR, 'h5').text.strip()
        timing = store.find_element(By.CSS_SELECTOR, 'p.text-xs').text.strip()
        distance = store.find_element(By.CSS_SELECTOR, 'div.bg-green').text.strip()
        store_data.append(f"1){address}\n{timing}\n{distance}\n\n")
        i += 1
    return store_data


async def start(update: Update, context) -> None:
    reply_markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=True)
    await update.message.reply_text('Please share your location:', reply_markup=reply_markup)


async def location(update: Update, context) -> None:
    user_location = update.message.location
    latitude = user_location.latitude
    longitude = user_location.longitude
    response = requests.get(f'https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={GEOCODING_API_KEY}')
    data = response.json()
    if data['results']:
        postal_code = data['results'][0]['components'].get('postcode', 'Postal code not found')
    else:
        postal_code = 'Postal code not found'
    update.message.reply_text(f'Your postal code is: {postal_code}')
    stores = get_stores(postal_code)
    await update.message.reply_text(f"We found {len(stores)} slurpee locations near you!")
    await update.message.reply_text(stores)


async def error(update: Update, context) -> None:
    logger.warning(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, location))
    app.run_polling()
