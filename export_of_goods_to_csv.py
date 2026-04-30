# export_of_goods_to_yml.py

import os
import csv
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from time import sleep
from dotenv import load_dotenv
from module.logger_config import LoggerConfig
import module.msclad_api as msclad_api
import module.moysclad as moysclad

# Настройки логирования
logger = LoggerConfig('logs/export_of_goods_to_csv').get_logger(__name__)
# logger.info(f"Найдено {len()} товаров")
# logger.warning(f"Не найдены товары")
# logger.error(f"Ошибка: {e}")


def main(sclad, setting):
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/product?filter={sclad['filter_name']}={sclad['filter_value']}"
    products = msclad_api.make_request("GET", url, sclad["token"]) # Получаем список товаров по фильтру
    if "rows" in products:
        if len(products["rows"]) > 0:
            logger.info(f"Найдено {len(products['rows'])} товаров.")
            items = moysclad.format_products(logger, sclad, products["rows"])
            file_path = create_csv_file(items, setting, setting["file_path"])
            logger.info(f"CSV файл успешно создан: {file_path}")
        else:
            logger.warning(f"Товары не найдены.")
    else:
        logger.error(f"Ошибка получения товаров: {products}.")


      
            
def create_csv_file(items, setting, file_path="export_of_goods.csv"):
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
                    "Category": setting["default_category"],
                    "Brand": setting["default_brand"],
                    "SKU": item["code"],
                    "Title": item["name"],
                    "Price": None,
                    "Quantity": None,
                    "Editions": None,
                    "External ID": item["externalCode"],
                    "Parent UID": None,
                })

                for variant in item["variants"][:4]:
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
                        "Quantity": int(setting["default_quantity"]),
                        "Editions": editions,
                        "External ID": variant["externalCode"],
                        "Parent UID": item["id"],
                    })
            else:
                writer.writerow({
                    "Tilda UID": item["id"],
                    "Category": setting["default_category"],
                    "Brand": setting["default_brand"],
                    "SKU": item["code"],
                    "Title": item["name"],
                    "Price": item["salePrice"],
                    "Quantity": int(setting["default_quantity"]),
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
    setting = {
        "file_path": os.getenv('file_path_csv'),
        "default_category": os.getenv('default_category'),
        "default_brand": os.getenv('default_brand'),
        "default_quantity": os.getenv('default_quantity'),
    }
    main(sclad, setting)
