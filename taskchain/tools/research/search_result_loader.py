"""Loader that uses Selenium to load a page, then uses unstructured to load the html.
"""
import os
import re
from typing import TYPE_CHECKING, List, Literal, Optional, Union

if TYPE_CHECKING:
    from selenium.webdriver import Chrome, Firefox
    from selenium.webdriver.chrome.service import Service

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader

from bs4 import BeautifulSoup

from taskchain.utilities import google_organic_search, load_dotenv_from_parents
from taskchain.schema.base import SearchResultItems


# from task_chain.processing.documents import text_splitter_by_token, chunks_from_documents



class SearchResultLoader(BaseLoader):
    """Loader that uses Selenium and to load a page and unstructured to load the html.
    This is useful for loading pages that require javascript to render.

    Attributes:
        search_results (List[dict]): List of Search Results containing links and snippets to load.
        continue_on_failure (bool): If True, continue loading other URLs on failure.
        browser (str): The browser to use, either 'chrome' or 'firefox'.
        executable_path (Optional[str]): The path to the browser executable.
        headless (bool): If True, the browser will run in headless mode.
    """

    MAX_TOKENS_PER_CHUNK = 400
    STEP_COLOR: str = "pink"
    START_COLOR: str = "yellow"
    verbose: bool = False

    def __init__(
            self,
            search_results: List[dict],
            continue_on_failure: bool = True,
            browser: Literal["chrome", "firefox"] = "chrome",
            executable_path: Optional[str] = None,
            headless: bool = True,
            load_pdfs: bool = False,
            run_in_thread: bool = False,
            **kwargs,
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
        self.load_pdfs = load_pdfs
        self.run_in_thread = run_in_thread
        self.search_items = []
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    def _load_unstructured(self, page_content: str) -> str:
        from unstructured.partition.html import partition_html
        elements = partition_html(text=page_content)
        return "\n\n".join([str(el) for el in elements])

    def _load_bs4(self, page_content: str) -> str:
        soup = BeautifulSoup(page_content, "html.parser")
        return soup.get_text()

    def _load_pdf(self, url: str) -> list[Document]:
        from taskchain.tools.research.search_pdf_urls import SearchPDFUrls
        from taskchain.tools.research.pdf_loader import load_pdf_documents_from_url
        scraper = SearchPDFUrls([])
        url = scraper.pdf_url_from_url(url)
        return load_pdf_documents_from_url(url)

    def load_playwright(self, url) -> list[Document]:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._load_playwright, url)
            docs = future.result()
        return docs


    def _load_playwright(self, url: str, *args) -> list[Document]:
        from langchain.document_loaders import PlaywrightURLLoader
        loader = PlaywrightURLLoader([url])
        return loader.load()


    def validate_text(self, text: str, snippet: str) -> bool:
        """Validate the text against google search snippet.
        finds the longest alphanumeric sequence in snippet
        and checks if it is in text

        Args:
            text (str): The text to validate.
            snippet (str): The validator to use.

        Returns:
            bool: True if the text is valid, False otherwise.
        """

        validator = max(re.findall(r'(?:[a-zA-Z0-9\s])+', snippet), key=len)
        return validator in text

    def parse_page_content(self, page_content: str, snippet) -> str:
        """Parse and validate the page content."""

        text = self._load_bs4(page_content)
        if self.validate_text(text, snippet):
            return text

        text = self._load_unstructured(page_content)
        if self.validate_text(text, snippet):
            return text
        raise ValueError("Could not parse page content")


    @classmethod
    def from_query(cls, query: str, **kwargs) -> "SeleniumSearchResultLoader":
        search_results = google_organic_search(query)
        load_dotenv_from_parents(["WEBDRIVER_PATH"])
        exec_path = os.getenv("WEBDRIVER_PATH")
        return cls(search_results, executable_path=exec_path, **kwargs)

    def get_search_items(self) -> list[SearchResultItems]:
        return [SearchResultItems(result.get("link"), result.get("snippet")) for result in self.search_results]

    def load_search_results(self, search_results: list[SearchResultItems]):
        self.search_items = search_results
        return self.load()

    def load_url(self, url: str, docs: list=None, driver=Union["Chrome", "Firefox"], snippet: str=None):
        if driver is None:
            driver = self._get_driver()

        if docs is None:
            docs = []

        if snippet is None:
            snippet = ""

        try:
            if url.endswith(".pdf") and self.load_pdfs:
                docs.extend(self._load_pdf(url))
            else:
                driver.get(url)
                page_content = driver.page_source
                text = self.parse_page_content(page_content, snippet)
                metadata = {"source": url}
                chunks = text_splitter_by_token(text, self.MAX_TOKENS_PER_CHUNK)
                for chunk in chunks:
                    docs.append(Document(page_content=chunk, metadata=metadata))


        except Exception as e:
            try:
                _docs = self.load_playwright(url)
                _docs = chunks_from_documents(_docs, self.MAX_TOKENS_PER_CHUNK)
                docs.extend(_docs)
            except Exception as e:
                if self.continue_on_failure:
                    pass
                else:
                    raise e
        return docs

    def load(self) -> List[Document]:
        """Load the specified URLs using Selenium and create Document instances.

        Returns:
            List[Document]: A list of Document instances with loaded content.
        """

        docs: List[Document] = list()
        driver = self._get_driver()

        for url, snippet in self.search_items:
            docs.extend(
                self.load_url(url, docs, driver, snippet)
            )


        driver.quit()
        return docs