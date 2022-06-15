import requests
import os
from bs4 import BeautifulSoup
import csv
from scraper_helper import get_dict
from scrapy.http import HtmlResponse
from getabstract.spiders.abstract import GetAbstractSpider
from getabstract.settings import BASE_URL, STYLES_PATH, DOWNLOADED_PATH, SAVE_TO_DIR
from scrapy.shell import inspect_response

class SaveWebPagePipeline:
    def process_item(self, item, spider: GetAbstractSpider):
        response = item.pop('response')  # pop value so it isn't exported to output file
        response_url = item.get('response_url')
        title = item.get('title')
        category = item.get('category')

        # there is only a sample of summary on initial page
        # additional post request is required to get full summary
        cookies = {x.split('=')[0]: x.split('=')[1] for x in
                   response.request.headers[b'Cookie'].decode("utf-8").split('; ')}
        post_url = response_url.split('/')
        post_url.pop(-2)
        post_url = '/'.join(post_url) + '/activate'

        post_headers = get_dict('''POST /en/summary/41782/activate HTTP/1.1
                                        Host: www.getabstract.com
                                        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0
                                        Accept: */*
                                        Accept-Language: en-US,en;q=0.5
                                        Accept-Encoding: gzip, deflate, br
                                        X-Requested-With: XMLHttpRequest
                                        Origin: https://www.getabstract.com
                                        Connection: keep-alive

                                        Sec-Fetch-Dest: empty
                                        Sec-Fetch-Mode: cors
                                        Sec-Fetch-Site: same-origin
                                        Content-Length: 0'''
                                + f'Referer: {response_url}')

        post_resp = requests.post(url=post_url,
                                  headers=post_headers,
                                  cookies=cookies)

        post_response = HtmlResponse(url=post_resp.url, body=post_resp.text, encoding='utf-8')
        post_resp.close()

        # save web page body
        post_page = BeautifulSoup(post_response.text, 'lxml')
        page = BeautifulSoup(response.text, 'lxml')

        # paste full summary to saved web page and change relative urls to absolute
        full_summary = post_page.find('div', {'itemprop': 'review'})
        partial_summary = page.find('div', {'itemprop': 'review'})
        partial_summary.replace_with(full_summary)

        img_src = page.find('img', {'class': 'sumpage-cover'})
        if img_src:
            img_src = img_src.get('src', "")
            img_src = BASE_URL + img_src
            page.find('img', {'class': 'sumpage-cover'})['src'] = img_src

        audio_url = page.find('a', {'class': 'jp-play'})
        if audio_url:
            audio_url = audio_url.get('href', "")
            audio_url = BASE_URL + '/en/summary/' + audio_url.split('/')[-1] + '/audio'
            page.find('a', {'class': 'jp-play'})['href'] = audio_url
            page.find('a', {'class': 'jp-play'})['target'] = '_blank'

        # remove redundant tags from saved web page
        to_del = [page.find('div', {'class': 'row my-5'}).parent,
                  page.find('header'),
                  page.find('div', {'class': 'sumpage-actionbar'}),
                  page.find('div', {'class': 'sumpage-header__fulltext'}),
                  page.find('div', {'class': 'sumpage-download'}),
                  page.find('footer')]
        [el.decompose() for el in to_del if el]
        [i.decompose() for i in page('i')]

        # add css styles to saved web page
        with open(STYLES_PATH, 'r', encoding="utf-8") as styles_file:
            styles = BeautifulSoup(' '.join(styles_file.readlines()), 'lxml').find('style')
            page.find('html').append(styles)

        # save web page to appropriate category directory
        save_to = SAVE_TO_DIR / category
        if not os.path.exists(save_to):
            os.makedirs(save_to)
        with open(save_to / f'{title}.html', 'w', encoding="utf-8") as html_file:
            html_file.write(page.prettify())

        # log that this page was downloaded
        spider.downloaded_urls.add(response_url)
        with open(DOWNLOADED_PATH, 'a', encoding="utf-8") as csvf:
            writer = csv.writer(csvf, delimiter=',', lineterminator='\n')
            writer.writerow([response_url])
        return item
