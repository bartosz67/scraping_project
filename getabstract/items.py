import scrapy

class GetAbstractItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    subtitle = scrapy.Field()
    category = scrapy.Field()
    response_url = scrapy.Field()

    response = scrapy.Field()

