import csv
import logging
import sys
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
SOURCES = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTERS_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONES_URL,
    "touch.csv": TOUCH_URL
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(
        by=By.CLASS_NAME,
        value="title"
    ).get_attribute("title")
    description = product.find_element(
        by=By.CSS_SELECTOR,
        value=".description.card-text"
    ).text
    price = float(product.find_element(
        by=By.CSS_SELECTOR,
        value=".price.float-end"
    ).text.replace("$", ""))
    rating = len(product.find_elements(
        by=By.CSS_SELECTOR,
        value=".ws-icon.ws-icon-star"
    ))
    num_of_reviews = int(product.find_element(
        by=By.CSS_SELECTOR,
        value=".review-count.float-end"
    ).text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_single_page_product(page_products: list) -> list[Product]:
    return [
        parse_single_product(page_product)
        for page_product in page_products
    ]


def get_category_products(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    try:
        more_button = driver.find_element(
            by=By.LINK_TEXT,
            value="More"
        )
    except NoSuchElementException:
        more_button = None

    while more_button:
        driver.execute_script("arguments[0].click();", more_button)
        if more_button.get_attribute("style"):
            more_button = None

    page_products = driver.find_elements(
        by=By.CSS_SELECTOR,
        value=".card.thumbnail"
    )
    all_products = get_single_page_product(page_products)

    return all_products


def parse_all_categories(sources: dict[str, str]) -> dict[str, list[Product]]:
    products_to_save = sources
    for file_path, page_url in sources.items():
        logging.info(f"Start parsing {file_path[:-4]}")
        products = get_category_products(page_url)
        products_to_save[file_path] = products

    return products_to_save


def save_products_to_csv(products: dict[str, list[Product]]) -> None:
    for file_path, products in products.items():
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(products[0].__annotations__.keys())
            for product in products:
                writer.writerow(product.__dict__.values())


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        products = parse_all_categories(SOURCES)
        save_products_to_csv(products)


if __name__ == "__main__":
    get_all_products()
