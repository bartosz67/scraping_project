import logging
from datetime import datetime
import pathlib
import dotenv
import os

dotenv.load_dotenv('.env')
EMAIL = os.environ['EMAIL']
PASSWORD = os.environ['PASSWORD']

logging.basicConfig(
    filename=f'log {datetime.today().strftime("%Y-%m-%d")}.txt',
    filemode='a',
    format='%(levelname)s: %(message)s',
    level=logging.WARNING
)

DOWNLOADED_PATH = pathlib.Path('downloaded_urls.csv')
STYLES_PATH = pathlib.Path('styles.html')
SAVE_TO_DIR = pathlib.Path('summaries')
BASE_URL = 'https://www.getabstract.com'

BOT_NAME = 'getabstract'

SPIDER_MODULES = ['getabstract.spiders']
NEWSPIDER_MODULE = 'getabstract.spiders'

AUTOTHROTTLE_ENABLED = True
DOWNLOAD_DELAY = 4

ROBOTSTXT_OBEY = False

HTTPERROR_ALLOWED_CODES = [403]

FEEDS = {
        "items.csv": {
            "format": 'csv'
        }
    }

ITEM_PIPELINES = {
    'getabstract.pipelines.SaveWebPagePipeline': 300,
}