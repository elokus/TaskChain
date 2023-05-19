



"""Loader that uses Selenium to load a page, then uses unstructured to load the html.
"""
import logging
from typing import TYPE_CHECKING, List, Literal, Optional, Union

if TYPE_CHECKING:
    from selenium.webdriver import Chrome, Firefox
    from selenium.webdriver.chrome.service import Service

from langchain.document_loaders.base import BaseLoader
from bs4 import BeautifulSoup
from taskchain.utilities import google_organic_search, load_dotenv_from_parents
import os

logger = logging.getLogger(__name__)


class SearchPDFUrls(BaseLoader):
    """Loader that uses Selenium and to load a page and unstructured to load the html.
    This is useful for loading pages that require javascript to render.

    Attributes:
        search_results (List[dict]): List of Search Results containing links and snippets to load.
        continue_on_failure (bool): If True, continue loading other URLs on failure.
        browser (str): The browser to use, either 'chrome' or 'firefox'.
        executable_path (Optional[str]): The path to the browser executable.
        headless (bool): If True, the browser will run in headless mode.
    """

    def __init__(
            self,
            search_results: List[dict],
            continue_on_failure: bool = True,
            browser: Literal["chrome", "firefox"] = "chrome",
            executable_path: Optional[str] = None,
            headless: bool = True,
    ):
        """Load a list of URLs using Selenium and unstructured."""
        try:
            import selenium  # noqa:F401
        except ImportError:
            raise ValueError(
                "selenium package not found, please install it with "
                "`pip install selenium`"
            )

        try:
            import unstructured  # noqa:F401
        except ImportError:
            raise ValueError(
                "unstructured package not found, please install it with "
                "`pip install unstructured`"
            )
        self.search_results = search_results
        self.continue_on_failure = continue_on_failure
        self.browser = browser
        self.executable_path = executable_path
        self.headless = headless
        self.urls = []

    def _get_driver(self) -> Union["Chrome", "Firefox"]:
        """Create and return a WebDriver instance based on the specified browser.

        Raises:
            ValueError: If an invalid browser is specified.

        Returns:
            Union[Chrome, Firefox]: A WebDriver instance for the specified browser.
        """
        if self.browser.lower() == "chrome":
            from selenium.webdriver import Chrome
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.chrome.service import Service

            chrome_options = ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless")
            if self.executable_path is None:
                return Chrome(options=chrome_options)
            return Chrome(service=Service(self.executable_path), options=chrome_options)
        elif self.browser.lower() == "firefox":
            from selenium.webdriver import Firefox
            from selenium.webdriver.firefox.options import Options as FirefoxOptions

            firefox_options = FirefoxOptions()
            if self.headless:
                firefox_options.add_argument("--headless")
            if self.executable_path is None:
                return Firefox(options=firefox_options)
            return Firefox(
                executable_path=self.executable_path, options=firefox_options
            )
        else:
            raise ValueError("Invalid browser specified. Use 'chrome' or 'firefox'.")


    @staticmethod
    def _pdf_in_text(text):
        for pdf in ["pdf", "PDF", "Pdf"]:
            if pdf in text:
                return True
        return False

    @staticmethod
    def pdf_url_from_research_gate(url: str):
        from parsel import Selector
        from playwright.sync_api import sync_playwright
        link_tag = ".research-detail-header-cta__buttons"
        urls = [url]
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, slow_mo=150)
            for url in urls:
                try:
                    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36")
                    page.goto(url)
                    selector = Selector(text=page.content())
                    pdf_url = f'https://www.researchgate.net/{selector.css(link_tag).css("a::attr(href)").get()}'
                except:
                    raise ValueError
            browser.close()
        return pdf_url


    def pdf_url_from_website(self, url: str):
        driver = self._get_driver()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        res = []
        for link in soup.find_all('a'):
            current_link = link.get('href')
            if current_link.endswith('pdf'):
                res.append(current_link)
        return res

    @classmethod
    def from_query(cls, query: str):
        load_dotenv_from_parents(["WEBDRIVER_PATH"])
        search_results = google_organic_search(query)
        exec_path = os.getenv("WEBDRIVER_PATH")
        return cls(search_results, executable_path=exec_path)

    def pdf_url_from_url(self, url):
        if "researchgate" in url:
            pdf_url = self.pdf_url_from_research_gate(url)
        elif url.endswith('pdf'):
            pdf_url = url
        else:
            pdf_url = self.pdf_url_from_website(url)
        return pdf_url

    def load(self) -> list[str]:
        pdf_urls = []
        website_urls = []
        for o in self.search_results:
            url = o["link"]
            if url.endswith('pdf'):
                pdf_urls.append(url)
            elif self._pdf_in_text(o["title"]) or self._pdf_in_text(o["snippet"]):
                website_urls.append(url)

        for url in website_urls:
            try:
                pdf_url = self.pdf_url_from_url(url)
                pdf_urls.extend(pdf_url)
            except Exception as e:
                if not self.continue_on_failure:
                    raise e
                print("Failed to load url: ", url)
                continue

        return pdf_urls


if __name__ == "__main__":
    scraper = SearchPDFUrls.from_query("research automotive .pdf paper")
    links = scraper.load()
    print(links)