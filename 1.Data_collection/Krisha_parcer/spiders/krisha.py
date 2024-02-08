import scrapy
from scrapy_playwright.page import PageMethod
# import requests


def should_abort_request(request):
    if request.resource_type in ('image', 'imageset', 'media'):
        return True
    return False


class KrishaSpider(scrapy.Spider):
    name = "krisha"
    allowed_domains = ["krisha.kz"]
    custom_settings = {
        'PLAYWRIGHT_ABORT_REQUEST': should_abort_request
    }
    # start_urls = ["https://krisha.kz/arenda/kvartiry/"]

    def start_requests(self):
        # GET request
        urls = [
            "https://krisha.kz/arenda/kvartiry/almaty/",
            "https://krisha.kz/arenda/kvartiry/astana/",
            "https://krisha.kz/arenda/kvartiry/abay-oblast/",
            "https://krisha.kz/arenda/kvartiry/akmolinskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/aktjubinskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/almatinskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/atyrauskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/vostochno-kazahstanskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/zhambylskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/jetisyskaya-oblast/",
            "https://krisha.kz/arenda/kvartiry/zapadno-kazahstanskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/karagandinskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/kostanajskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/kyzylordinskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/mangistauskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/pavlodarskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/severo-kazahstanskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/juzhno-kazahstanskaja-oblast/",
            "https://krisha.kz/arenda/kvartiry/ulitayskay-oblast/"
        ]
        for url in urls:
            yield scrapy.Request(
                url,
                meta={"playwright": True}
            )

    def parse(self, response):
        cars = response.css('.a-card')
        for card in cars:
            initial_data = self.card_parse(card)

            yield response.follow(initial_data['url'],
                                  callback=self.parse_car_page,
                                  meta={'playwright': True,
                                        'initial_info': initial_data
                                        }
                                  )

        next_page = response.css('.paginator__btn::attr(data-page)')[-1].get()

        if next_page is not None:
            base = f'?rent-period-switch=%2Farenda%2Fkvartiry&page={next_page}'
            next_page_url = f'{base}'
            yield response.follow(next_page_url, callback=self.parse)

    def parse_car_page(self, response):
        page_info = {}
        page_info['название'] = response.css('h1::text').get().strip()
        page_info['цена'] = response.css('.offer__price::text').get().strip()
        # sidebar table
        page_info = self.sidebar_parse(response, page_info)
        # about apartment
        page_info = self.about_apart_parse(response, page_info)
        # initial info
        for k, v in response.meta.get('initial_info').items():
            page_info[k] = v
        yield page_info

    @staticmethod
    def card_parse(card):
        car_url = 'https://krisha.kz' \
            + card.css('.a-card__title::attr(href)').get()

        initial_data = {}
        initial_data['Цвет'] = card.css('::attr(data-color)').get()
        initial_data['url'] = car_url
        initial_data['Владелец'] = card.css('.a-card__owner .label::text')\
            .getall()[1].strip()

        icons = card.css('.paid-labels .paid-icon')

        initial_data['×15 просмотров на месяц'] = 0
        initial_data['×5 просмотров на неделю'] = 0
        initial_data['В горячих'] = 0
        initial_data['ТОП объявление'] = 0
        initial_data['Срочно, торг'] = 0

        for icon in icons:
            initial_data[
                (f'{icon.css(".kr-tooltip__title ::text").get().strip()}')
                ] = 1
        return initial_data

    @staticmethod
    def sidebar_parse(response, page_info):
        titles, values = [], []

        for title_info in response.css('.offer__info-title'):
            x = title_info.css('::text').getall()
            x = ''.join(map(lambda y: y.strip(), x))
            titles.append(x)

        for value_info in response.css('.offer__advert-short-info'):
            x = value_info.css('::text').getall()
            x = ' '.join(map(lambda y: y.strip(), x))
            values.append(x)
        for title, value in zip(titles, values):
            page_info[title] = value
        return page_info

    @staticmethod
    def about_apart_parse(response, page_info):
        for row in response.css('.offer__parameters dl'):
            title = row.css('dt ::text').get().strip()
            value = row.css('dd ::text').get().strip()
            page_info[title] = value

        view_count = response \
            .css('.offer__views .nb-views-number ::text') \
            .get()
        if view_count:
            page_info['просмотры'] = view_count.strip()
        else:
            page_info['просмотры'] = view_count

        return page_info
