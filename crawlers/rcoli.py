import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from multiprocessing import Process, Queue
from twisted.internet import reactor


class InfoPageSpider(scrapy.Spider):
    name = "InfoPageSpider"

    def __init__(self, urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls if isinstance(urls, list) else [urls]

    def parse(self, response):
        result = {'link': response.url}

        title = response.css("div.heading h3::text").get()
        if title:
            result['title'] = title.strip()

        paragraphs = response.css('div.col.info p')

        for i, p in enumerate(paragraphs):
            element_name = None

            paragraph_text = p.xpath('string()').get().strip()
            if 'writer' in paragraph_text.lower():
                element_name = 'writers'
            elif 'artist' in paragraph_text.lower():
                element_name = 'artists'
            elif 'date' in paragraph_text.lower():
                element_name = 'date_published'

            if not element_name:
                continue

            if ':' in paragraph_text:
                paragraph_text = paragraph_text.split(':', 1)[1].strip()

            result[element_name] = paragraph_text

        result['issues'] = []

        issues = response.css('ul.list li')
        for issue in issues:
            issue_title = issue.css('div.col-1 a span::text').get()
            issue_link = issue.css('div.col-1 a::attr(href)').get()
            result['issues'].append({'issue_title': issue_title, 'issue_link': issue_link})

        yield result

def f(q, urls, selected_spider):  # Define f as a global function
    try:
        results = []

        def item_scraped(item, response, spider):
            results.append(item)

        settings = get_project_settings()
        settings['LOG_LEVEL'] = 'ERROR'
        runner = CrawlerRunner(settings)
        crawler = runner.create_crawler(selected_spider)
        crawler.signals.connect(item_scraped, signal=scrapy.signals.item_scraped)
        deferred = runner.crawl(crawler, urls=urls)
        deferred.addBoth(lambda _: reactor.stop())
        reactor.run(installSignalHandlers=False)
        q.put(results)
    except Exception as e:
        q.put(e)

def run_spider(urls, selected_spider):
    """
    Runs the specified spider with the given URLs in a separate process and returns the results.

    Args:
        urls: A list of URLs to crawl.
        selected_spider: The spider class to use for crawling.

    Returns:
        A list of dictionaries, where each dictionary represents the results from a crawled page.
    """

    q = Queue()
    p = Process(target=f, args=(q, urls, selected_spider))  # Now uses the global f
    p.start()
    result = q.get()
    p.join()

    if isinstance(result, Exception):
        raise result
    else:
        return result

if __name__ == '__main__':
    pass
