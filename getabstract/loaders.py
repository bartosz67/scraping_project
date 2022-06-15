from scrapy.loader import ItemLoader
from itemloaders.processors import Compose, MapCompose, Join, TakeFirst
from pathvalidate import sanitize_filename
clean_text = Compose(MapCompose(lambda x: x.strip()), Join())

class GetAbstractLoader(ItemLoader):
    author_out = clean_text
    subtitle_out = clean_text
    response_url_out = TakeFirst()
    # sanitizing files makes them available as file and directory names
    title_out = Compose(clean_text, sanitize_filename, lambda x: x.replace('-', ' ').title())
    category_out = Compose(TakeFirst(), sanitize_filename)

    response_out = TakeFirst()
