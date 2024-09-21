#!/usr/bin/env python3

import json
from datetime import date
from os import path
import pandas as pd
import requests


class Parser:
    """
    A parser object for extracting data from wildberries.ru.
    """

    def __init__(self) -> None:
        self.headers = {
            'Accept': "*/*",
            'User-Agent': "Chrome/51.0.2704.103 Safari/537.36"
        }
        self.run_date = date.today()
        self.product_cards = []
        self.directory = path.dirname(__file__)

    def download_current_catalogue(self) -> str:
        """
        Download the catalogue from wildberries.ru and save it in JSON format.
        Returns the path to the downloaded catalogue file.
        """
        local_catalogue_path = path.join(self.directory, 'wb_catalogue.json')
        if not path.exists(local_catalogue_path) or date.fromtimestamp(
                path.getmtime(local_catalogue_path)) > self.run_date:
            url = 'https://static-basket-01.wb.ru/vol0/data/main-menu-ru-ru-v2.json'
            response = requests.get(url, headers=self.headers).json()
            with open(local_catalogue_path, 'w', encoding='UTF-8') as my_file:
                json.dump(response, my_file, indent=2, ensure_ascii=False)
        return local_catalogue_path

    def traverse_json(self, parent_category: list, flattened_catalogue: list) -> None:
        """
        Recursively traverse the JSON catalogue and flatten it to a list.
        """
        for category in parent_category:
            try:
                flattened_catalogue.append({
                    'name': category['name'],
                    'url': category['url'],
                    'shard': category['shard'],
                    'query': category['query']
                })
            except KeyError:
                continue

            if 'childs' in category:
                self.traverse_json(category['childs'], flattened_catalogue)

    def process_catalogue(self, local_catalogue_path: str) -> list:
        """
        Process the locally saved JSON catalogue into a list of dictionaries.
        """
        catalogue = []
        with open(local_catalogue_path, 'r', encoding='UTF-8') as my_file:
            self.traverse_json(json.load(my_file), catalogue)
        return catalogue

    def extract_category_data(self, catalogue: list, user_input: str) -> tuple:
        """
        Extract category data from the processed catalogue.
        Returns a tuple containing the category name, shard, and query.
        """
        for category in catalogue:
            if user_input.split("https://www.wildberries.ru")[-1] == category['url'] or user_input == category['name']:
                return category['name'], category['shard'], category['query']
        return None

    def get_products_on_page(self, page_data: dict) -> list:
        """
        Parse one page of results and return a list with product data.
        """
        products_on_page = [
            {
                'Link': f"https://www.wildberries.ru/catalog/{item['id']}/detail.aspx",
                'ID': item['id'],
                'Name': item['name'],
                'Brand': item['brand'],
                'Brand ID': item['brandId'],
                'Price': int(item['priceU'] / 100),
                'Discounted price': int(item['salePriceU'] / 100),
                'Rating': item['rating'],
                'Reviews': item['feedbacks']
            }
            for item in page_data['data']['products']
        ]
        return products_on_page

    def add_data_from_page(self, url: str) -> bool:
        """
        Add data on products from a page to the class's product_cards list.
        Returns True if there are no products on the page, indicating the end of product loading.
        """
        response = requests.get(url, headers=self.headers).json()
        page_data = self.get_products_on_page(response)
        if page_data:
            self.product_cards.extend(page_data)
            print(f"Items added: {len(page_data)}")
        else:
            print('Loading finished')
            return True
        return False

    def build_catalogue_url(self, category_data: tuple, page: int) -> str:
        """
        Build the URL for a specific catalogue page.
        """
        return (f"https://catalog.wb.ru/catalog/{category_data[1]}/"
                f"catalog?appType=1&{category_data[2]}&curr=rub"
                f"&dest=-1257786&page={page}&sort=popular&spp=24")

    def get_all_products_in_category(self, category_data: tuple) -> None:
        """
        Retrieve all products in a category by going through all pages.
        """
        for page in range(1, 101):
            print(f'Loading items from page {page}')
            url = self.build_catalogue_url(category_data, page)
            if self.add_data_from_page(url):
                break

    def get_sales_data(self) -> None:
        """
        Parse additional sales data for the product cards.
        """
        for card in self.product_cards:
            url = f"https://product-order-qnt.wildberries.ru/by-nm/?nm={card['ID']}"
            try:
                response = requests.get(url, headers=self.headers).json()
                card['Selled'] = response[0]['qnt']
            except requests.ConnectTimeout:
                card['Selled'] = 'no data'
            print(f"Items collected: {self.product_cards.index(card) + 1} of {len(self.product_cards)}")

    def save_to_excel(self, file_name: str) -> str:
        """
        Save the parsed data in xlsx format and return its path.
        """
        data = pd.DataFrame(self.product_cards)
        result_path = f"{path.join(self.directory, file_name)}_{self.run_date}.xlsx"
        with pd.ExcelWriter(result_path, engine='xlsxwriter') as writer:
            data.to_excel(writer, 'data', index=False)
        return result_path

    def build_search_url(self, key_word: str, page: int) -> str:
        """
        Build the URL for a search results page.
        """
        query = '%20'.join(key_word.split())
        return (f"https://search.wb.ru/exactmatch/ru/common/v4/search?"
                f"appType=1&curr=rub&dest=-1257786&page={page}"
                f"&query={query}&resultset=catalog&sort=popular&spp=24")

    def get_all_products_in_search_result(self, key_word: str) -> None:
        """
        Retrieve all products in the search result by going through all pages.
        """
        for page in range(1, 101):
            print(f'Loading items from page {page}')
            url = self.build_search_url(key_word, page)
            if self.add_data_from_page(url):
                break

    def run_parser(self) -> None:
        """
        Run the parser for either category or search-based parsing.
        """
        instructions = """\nSelect a parsing method (enter 1 or 2): \n1: Parse the entire category of items \n2: Parse items found by keywords\n"""
        mode = input(instructions)
        if mode == '1':
            local_catalogue_path = self.download_current_catalogue()
            print(f"Catalogue saved: {local_catalogue_path}")
            processed_catalogue = self.process_catalogue(local_catalogue_path)
            input_category = input("Enter category name or URL: ")
            category_data = self.extract_category_data(processed_catalogue, input_category)
            if category_data:
                print(f"Found category: {category_data[0]}")
                self.get_all_products_in_category(category_data)
                self.get_sales_data()
                print(f"Data saved in {self.save_to_excel(category_data[0])}")
            else:
                print("Category not found.")
        elif mode == '2':
            key_word = input("Enter search keyword: ")
            self.get_all_products_in_search_result(key_word)
            self.get_sales_data()
            print(f"Data saved in {self.save_to_excel(key_word)}")


if __name__ == '__main__':
    app = Parser()
    app.run_parser()
