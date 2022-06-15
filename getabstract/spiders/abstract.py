import csv
import scrapy
from scraper_helper import get_dict
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from getabstract.items import GetAbstractItem
from getabstract.loaders import GetAbstractLoader
from getabstract.settings import DOWNLOADED_PATH, BASE_URL, EMAIL, PASSWORD
from scrapy.shell import inspect_response

class GetAbstractSpider(scrapy.Spider):
    name = 'getabstract'
    login_page_url = 'https://www.getabstract.com/en/login'

    DOWNLOADED_PATH.touch(exist_ok=True)
    with open(DOWNLOADED_PATH, 'r', encoding="utf-8") as csvf:
        reader = csv.reader(csvf, delimiter=',', lineterminator='\n')
        downloaded_urls = {x[0] for x in reader}

    headers = get_dict('''User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0
                          Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
                          Accept-Language: pl,en-US;q=0.7,en;q=0.3
                          Accept-Encoding: gzip, deflate, br
                          Connection: keep-alive''')

    # headers used for login post request
    login_headers = get_dict('''Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                                Accept-Encoding: gzip, deflate, br
                                Accept-Language: en-US,en;q=0.9
                                Cache-Control: max-age=0
                                Connection: keep-alive
                                Content-Length: 142
                                Content-Type: application/x-www-form-urlencoded
                                Host: www.getabstract.com
                                Origin: https://www.getabstract.com
                                Referer: https://www.getabstract.com/en/login
                                Upgrade-Insecure-Requests: 1
                                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36''')

    # moved to pipeline - doesn't work when stopped with keyboard interrupt, requires tricky exception handling
    # when spider finishes save urls of downloaded pages
    # def closed(self, reason):
    #     with open(self.downloaded_path, 'a', encoding="utf-8") as csvf:
    #         writer = csv.writer(csvf, delimiter=',', lineterminator='\n')
    #         [writer.writerow([url]) for url in self.downloaded_urls]

    # start by going to login page
    def start_requests(self):
        yield scrapy.Request(url=self.login_page_url,
                             headers=self.headers,
                             callback=self.login)

    def login(self, response):
        token = response.xpath('//input[@id="_tk"]/@value').get().strip()
        post_request_body = 'onSuccess=&' \
                            f'_tk={token}&' \
                            f'username={EMAIL}&' \
                            f'password={PASSWORD}&' \
                            'remember=true&' \
                            '_remember=on'

        yield response.follow(url='https://www.getabstract.com/en/login',
                              method='POST',
                              headers=self.login_headers,
                              body=post_request_body,
                              callback=self.categories_page)

    def categories_page(self, response):
        yield response.follow(url='https://www.getabstract.com/en/explore/channels',
                              headers=self.headers,
                              callback=self.paginate_categories)

    def paginate_categories(self, response):
        # page=10000 shows all summaries on page, other url values are redundant but needed
        pagination_part = '?page=10000&sorting=relevance&audioFormFilter=false&languageFormFilter=en&minRatingFormFilter=5&minPublicationDateFormFilter=0'
        category_url_parts = list(set(response.xpath('//a[contains(@class, "chov__list-group-item-title")]/h4/../..//div[@class="chov__action-view"]/a[contains(@href, "/en/channels")]/@href').getall()))

        for cat_part in category_url_parts:
            # category name to be saved with scraped data
            category = cat_part.split('/')[-2]

            full_url = BASE_URL + cat_part + pagination_part
            yield response.follow(url=full_url,
                                  headers=self.headers,
                                  callback=self.paginate_summaries,
                                  cb_kwargs={'category': category})

    def paginate_summaries(self, response, category):
        # set to remove duplicate urls
        summary_url_parts = list(set(response.xpath('//span[contains(text(), "Book")]/../..//a[contains(@href, "/en/summary")]/@href').getall()))
        for sum_part in summary_url_parts:
            full_url = BASE_URL + sum_part

            yield response.follow(url=full_url,
                                  headers=self.headers,
                                  callback=self.scrape_summary,
                                  cb_kwargs={'category': category})

    def scrape_summary(self, response: scrapy.http.response.Response, category):
        item_loader = GetAbstractLoader(item=GetAbstractItem(), selector=response)

        # useful values to save in csv
        item_loader.add_value('title', response.url.split('/')[-2])
        item_loader.add_xpath('author', '//div[@class="sumpage-header__authors"]/a/text()')
        item_loader.add_value('category', category)
        item_loader.add_xpath('subtitle', '//h2[@class="lead sumpage-header__subtitle"]/text()')
        item_loader.add_value('response_url', response.url)

        # values used to download web page, dropped later
        item_loader.add_value('response', response)

        yield item_loader.load_item()


if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(GetAbstractSpider)
    process.start()
