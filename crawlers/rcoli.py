import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from multiprocessing import Process, Queue
from twisted.internet import reactor
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

from dotenv import load_dotenv
import os

load_dotenv()


class InfoPageSpider(scrapy.Spider):
    name = "InfoPageSpider"

    def __init__(self, urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls if isinstance(urls, list) else [urls]

    def parse(self, response):
        result = {"link": response.url}

        title = response.css("div.heading h3::text").get()
        if title:
            result["title"] = title.strip()

        paragraphs = response.css("div.col.info p")

        for i, p in enumerate(paragraphs):
            element_name = None

            paragraph_text = p.xpath("string()").get().strip()
            if "writer" in paragraph_text.lower():
                element_name = "writers"
            elif "artist" in paragraph_text.lower():
                element_name = "artists"
            elif "date" in paragraph_text.lower():
                element_name = "date_published"

            if not element_name:
                continue

            if ":" in paragraph_text:
                paragraph_text = paragraph_text.split(":", 1)[1].strip()

            result[element_name] = paragraph_text

        result["issues"] = []

        issues = response.css("ul.list li")
        for issue in issues:
            issue_title = issue.css("div.col-1 a span::text").get()
            issue_link = issue.css("div.col-1 a::attr(href)").get()
            result["issues"].append(
                {"issue_title": issue_title, "issue_link": issue_link}
            )

        result["issues"] = list(
            filter(
                lambda x: x["issue_title"] is not None and x["issue_link"] is not None,
                result["issues"],
            )
        )

        yield result


def f(q, urls, selected_spider):  # Define f as a global function
    try:
        results = []

        def item_scraped(item, response, spider):
            results.append(item)

        settings = get_project_settings()
        settings["LOG_LEVEL"] = "ERROR"
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


def crawl_issues(issues):
    print(issues)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    # chrome_options.add_argument('--start-minimized')

    service = Service(os.getenv("CHROME_DRIVER_PATH"))
    browser = webdriver.Chrome(service=service, options=chrome_options)
    # browser.minimize_window()

    successes = []
    failures = []

    for issue in issues:
        result = selenium_crawl(browser, issue["link"])

        if "error" in result:
            failures.append({"issue_id": issue["issue_id"], "link": issue["link"]})
        else:
            successes.append(
                {"issue_id": issue["issue_id"], "pages": result, "link": issue["link"]}
            )

    browser.quit()

    return successes, failures


def selenium_crawl(browser, url, image_load_threshold=120):
    start_time = time.time()

    def scroll_until_images_load(browser):
        while True:
            # Scroll to the bottom
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Wait for new content to load

            images = browser.find_elements(
                "xpath", '//img[@rel="noreferrer" and contains(@src, "blank.gif")]'
            )

            if not images or (time.time() - start_time >= image_load_threshold):
                break

    browser.get(url)
    scroll_until_images_load(browser)

    # Parse page source with BeautifulSoup
    soup = BeautifulSoup(browser.page_source, "html.parser")
    images = soup.find_all("img", attrs={"rel": "noreferrer"})

    # Extract img src attributes in order and track index
    result = []
    for index, img in enumerate(images):
        src = img.get("src")
        if not src or "blank.gif" in src:
            return {"error": "Was not able to find src for: " + url}
        if src:
            result.append({"page": int(index + 1), "link": src})

    return result


if __name__ == "__main__":
    pass
