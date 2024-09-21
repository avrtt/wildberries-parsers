import requests
import pandas as pd
from retry import retry

class Parser:
    def __init__(self, url: str, min_price: int = 1, max_price: int = 1000000, discount: int = 0):
        self.url = url
        self.min_price = min_price
        self.max_price = max_price
        self.discount = discount
        self.catalog_data = self.fetch_full_catalog()
        self.category = self.find_category_in_catalog()

    @staticmethod
    def fetch_full_catalog() -> dict:
        """Fetches the full Wildberries catalog."""
        url = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json'
        headers = {'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        return requests.get(url, headers=headers).json()

    def extract_category_data(self, catalog: dict) -> list:
        """Extracts category data from the Wildberries catalog."""
        categories = []
        if isinstance(catalog, dict) and 'childs' not in catalog:
            categories.append({
                'name': catalog['name'],
                'shard': catalog.get('shard', None),
                'url': catalog['url'],
                'query': catalog.get('query', None)
            })
        elif isinstance(catalog, dict):
            categories.append({
                'name': catalog['name'],
                'shard': catalog.get('shard', None),
                'url': catalog['url'],
                'query': catalog.get('query', None)
            })
            categories.extend(self.extract_category_data(catalog['childs']))
        else:
            for child in catalog:
                categories.extend(self.extract_category_data(child))
        return categories

    def find_category_in_catalog(self) -> dict:
        """Checks if the user-provided URL matches a category in the catalog."""
        catalog_list = self.extract_category_data(self.catalog_data)
        for catalog in catalog_list:
            if catalog['url'] == self.url.split('https://www.wildberries.ru')[-1]:
                print(f'Match found: {catalog["name"]}')
                return catalog
        raise ValueError('Invalid URL or category not found in the catalog.')

    @staticmethod
    def extract_product_data(json_data: dict) -> list:
        """Extracts product data from the given JSON response."""
        products = []
        for item in json_data['data']['products']:
            products.append({
                'id': item.get('id'),
                'name': item.get('name'),
                'price': int(item.get("priceU") / 100),
                'salePriceU': int(item.get('salePriceU') / 100),
                'cashback': item.get('feedbackPoints'),
                'sale': item.get('sale'),
                'brand': item.get('brand'),
                'rating': item.get('rating'),
                'supplier': item.get('supplier'),
                'supplierRating': item.get('supplierRating'),
                'feedbacks': item.get('feedbacks'),
                'reviewRating': item.get('reviewRating'),
                'promoTextCard': item.get('promoTextCard'),
                'promoTextCat': item.get('promoTextCat'),
                'link': f'https://www.wildberries.ru/catalog/{item.get("id")}/detail.aspx?targetUrl=BP'
            })
        return products

    @retry(Exception, tries=-1, delay=0)
    def scrape_page(self, page: int) -> dict:
        """Scrapes data from a single catalog page."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0)"}
        url = (f'https://catalog.wb.ru/catalog/{self.category["shard"]}/catalog?appType=1&curr=rub'
               f'&dest=-1257786&locale=ru&page={page}&priceU={self.min_price * 100};{self.max_price * 100}'
               f'&sort=popular&spp=0&{self.category["query"]}&discount={self.discount}')
        
        response = requests.get(url, headers=headers)
        print(f'Status: {response.status_code} Scraping page {page}...')
        return response.json()

    def collect_products(self) -> list:
        """Collects product data from multiple pages."""
        products = []
        for page in range(1, 51):
            data = self.scrape_page(page)
            product_list = self.extract_product_data(data)
            print(f'Products added: {len(product_list)}')

            if product_list:
                products.extend(product_list)
            else:
                break
        print(f'Finished collecting data. Total products: {len(products)}.')
        return products

    @staticmethod
    def save_to_excel(data: list, filename: str):
        """Saves the result to an Excel file."""
        df = pd.DataFrame(data)
        with pd.ExcelWriter(f'{filename}.xlsx') as writer:
            df.to_excel(writer, sheet_name='data', index=False)
            sheet = writer.sheets['data']

            # Setting column widths for readability
            sheet.set_column(0, 1, width=10)
            sheet.set_column(1, 2, width=34)
            sheet.set_column(2, 3, width=8)
            sheet.set_column(3, 4, width=9)
            sheet.set_column(4, 5, width=8)
            sheet.set_column(5, 6, width=4)
            sheet.set_column(6, 7, width=20)
            sheet.set_column(7, 8, width=6)
            sheet.set_column(8, 9, width=23)
            sheet.set_column(9, 10, width=13)
            sheet.set_column(10, 11, width=11)
            sheet.set_column(11, 12, width=12)
            sheet.set_column(12, 13, width=15)
            sheet.set_column(13, 14, width=15)
            sheet.set_column(14, 15, width=67)

        print(f'Saved to {filename}.xlsx\n')

    def run(self):
        """Main function to run the parser."""
        try:
            # Collect product data
            products = self.collect_products()
            # Save collected data to Excel
            filename = f'{self.category["name"]}_from_{self.min_price}_to_{self.max_price}'
            self.save_to_excel(products, filename)
            print(f'Check this link: {self.url}?priceU={self.min_price * 100};{self.max_price * 100}&discount={self.discount}')
        
        except ValueError as ve:
            print(f'Error: {ve}')
        except PermissionError:
            print('Error! Please close the previously created Excel file and try again.')


if __name__ == '__main__':
    """Main script loop for console execution"""
    while True:
        try:
            url = input('Enter the category URL without filters for collection (or "q" to quit):\n')
            if url == 'q':
                break

            min_price = int(input('Enter the minimum price: '))
            max_price = int(input('Enter the maximum price: '))
            discount = int(input('Enter the minimum discount (enter 0 for no discount): '))

            parser = Parser(url=url, min_price=min_price, max_price=max_price, discount=discount)
            parser.run()

        except Exception as e:
            print(f'Input error: {e}\nRestarting...')
