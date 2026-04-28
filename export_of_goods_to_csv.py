# export_of_goods_to_yml.py

import os
import csv
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from time import sleep
from dotenv import load_dotenv
from module.logger_config import LoggerConfig
import module.msclad as msclad

# Настройки логирования
logger = LoggerConfig('logs/export_of_goods_to_csv').get_logger(__name__)
# logger.info(f"Найдено {len()} товаров")
# logger.warning(f"Не найдены товары")
# logger.error(f"Ошибка: {e}")


def main(sclad):
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/product?filter={sclad['filter_name']}={sclad['filter_value']}"
    products = msclad.make_request("GET", url, sclad["token"]) # Получаем список товаров по фильтру
    if "rows" in products:
        if len(products["rows"]) > 0:
            logger.info(f"Найдено {len(products['rows'])} товаров.")
            items = format_products(sclad, products["rows"])
            file_path = create_csv_file(items)
            logger.info(f"YML файл успешно создан: {file_path}")
        else:
            logger.warning(f"Товары не найдены.")
    else:
        logger.error(f"Ошибка получения товаров: {products}.")


# Форматируем товары, собираем всю информацию
def format_products(sclad, products):
    items = []
    for product in products:
        item = {
            "id": product['id'],
            "name": product['name'],
            "externalCode": product['externalCode'],
            "salePrice": 0,
        }

        # Проверяем заполнен ли код товара
        if 'code' in product and product['code']:
            item["code"] = product['code']
        else:
            logger.warning(f"Tовар \"{item['name']}\" пропущен: не заполнен код товара.")
            continue
        
        # Собираем модификации товара
        if 'variantsCount' in product and product['variantsCount'] > 0:
            logger.info(f"У товара \"{item['name']}\" найдено {product['variantsCount']} модификаций.")
            item["variants"] = variants_product(sclad, item["id"])
        else:
            logger.info(f"У товара \"{item['name']}\" не найдены модификации.")
            for salePrice in product['salePrices']:
                if salePrice['priceType']['id'] == sclad["id_sale_price"]:
                    item["salePrice"] = salePrice["value"]
                    break
        items.append(item)
    return items

# Cобираем всю информацию по модификациям
def variants_product(sclad, id):
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/variant?filter=productid={id}"
    variants = msclad.make_request("GET", url, sclad["token"])
    if len(variants["rows"]) > 0:
        items = []

        for variant in variants["rows"]:
            item = {
                "id": variant['id'],
                "name": variant['name'],
                "externalCode": variant['externalCode'],
                "code": variant['code'],
                "characteristics": {},
                "salePrice": 0,

            }

            # Собираем свойства
            if 'characteristics' in  variant:
                for characteristic in variant['characteristics']:
                    item["characteristics"][characteristic["name"]] = characteristic["value"]
                # Пример полученных данных {'SSD': '1000GB SSD', 'CPU': 'I7-14700KF', 'GPU': 'RTX 5060 Ti 16GB', 'RAM': '32GB DDR5'}

            # Получаем цену
            for salePrice in variant['salePrices']:
                if salePrice['priceType']['id'] == sclad["id_sale_price"]:
                    if salePrice["value"] > 0:
                        item["salePrice"] = salePrice["value"]
                    else:
                        item["salePrice"] = 0
                    break

            items.append(item)
    return items        
            
def create_csv_file(items, file_path="export_of_goods.csv"):
    fieldnames = [
        "Tilda UID",
        "Category",
        "Brand",
        "SKU",
        "Title",
        "Price",
        "Quantity",
        "Editions",
        "External ID",
        "Parent UID",
    ]

    with open(file_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for item in items:
            if "variants" in item:
                writer.writerow({
                    "Tilda UID": item["id"],
                    "Category": "Настольные компьютеры",
                    "Brand": "LONES",
                    "SKU": item["code"],
                    "Title": item["name"],
                    "Price": None,
                    "Quantity": None,
                    "Editions": None,
                    "External ID": item["externalCode"],
                    "Parent UID": None,
                })

                for variant in item["variants"]:
                    editions = None
                    if "characteristics" in variant and variant["characteristics"]:
                        editions = ";".join(
                            f"{name}:{value}" for name, value in variant["characteristics"].items()
                        )

                    writer.writerow({
                        "Tilda UID": variant["id"],
                        "Category": None,
                        "Brand": None,
                        "SKU": variant["code"],
                        "Title": variant["name"],
                        "Price": variant["salePrice"],
                        "Quantity": 999,
                        "Editions": editions,
                        "External ID": variant["externalCode"],
                        "Parent UID": item["id"],
                    })
            else:
                writer.writerow({
                    "Tilda UID": item["id"],
                    "Category": "Настольные компьютеры",
                    "Brand": "LONES",
                    "SKU": item["code"],
                    "Title": item["name"],
                    "Price": item["salePrice"],
                    "Quantity": 999,
                    "Editions": None,
                    "External ID": item["externalCode"],
                    "Parent UID": None,
                })

    return file_path





if __name__ == "__main__":
    load_dotenv()
    sclad = {
        "token": os.getenv('token_sclad'),
        "filter_name": os.getenv('filter_name'),
        "filter_value": os.getenv('filter_value'),
        "id_sale_price": os.getenv('id_sale_price')
    }
    main(sclad)
