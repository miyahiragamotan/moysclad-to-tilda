# export_of_goods_to_yml.py

import os
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from time import sleep
from dotenv import load_dotenv
from module.logger_config import LoggerConfig
import module.msclad_api as msclad_api
import module.moysclad as moysclad

# Настройки логирования
logger = LoggerConfig('logs/export_of_goods_to_yml').get_logger(__name__)
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
            file_path = create_yml_file(items, setting, setting["file_path"])
            logger.info(f"YML файл успешно создан: {file_path}")
        else:
            logger.warning(f"Товары не найдены.")
    else:
        logger.error(f"Ошибка получения товаров: {products}.")


def create_yml_file(items, setting, file_path="export_of_goods.yml"):
    yml_catalog = ET.Element(
        "yml_catalog",
        attrib={
            "date": datetime.now(timezone(timedelta(hours=3))).isoformat(timespec="seconds")
        },
    )
    shop = ET.SubElement(yml_catalog, "shop")

    ET.SubElement(shop, "name").text = setting["default_company"]
    ET.SubElement(shop, "company").text = setting["default_company"]
    ET.SubElement(shop, "url").text = "https://online.moysklad.ru/"
    ET.SubElement(shop, "platform").text = "МойСклад"

    currencies = ET.SubElement(shop, "currencies")
    ET.SubElement(currencies, "currency", attrib={"id": "RUR", "rate": "1"})

    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", attrib={"id": "1", "parentId": "2"}).text = setting["default_category"]

    offers = ET.SubElement(shop, "offers")

    for item in items:
        if "variants" not in item or not item["variants"]:
            continue
        
        for variant in item["variants"]:
            offer = ET.SubElement(
                offers,
                "offer",
                attrib={
                    "id": variant["id"],
                    "group_id": item["id"],
                },
            )
            ET.SubElement(offer, "name").text = variant["name"]
            ET.SubElement(offer, "vendor").text = setting["default_brand"]
            ET.SubElement(offer, "count").text = setting["default_quantity"]
            ET.SubElement(offer, "price").text = str(variant["salePrice"])
            ET.SubElement(offer, "currencyId").text = "RUR"
            ET.SubElement(offer, "categoryId").text = "140451609632"

            characteristics = list(variant.get("characteristics", {}).items())
            for name, value in characteristics:
                ET.SubElement(offer, "param", attrib={"name": str(name)}).text = str(value)

    tree = ET.ElementTree(yml_catalog)
    ET.indent(tree, space="\t", level=0)
    tree.write(file_path, encoding="UTF-8", xml_declaration=True)
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
        "file_path": os.getenv('file_path_yml'),
        "default_company": os.getenv('default_company'),
        "default_category": os.getenv('default_category'),
        "default_brand": os.getenv('default_brand'),
        "default_quantity": os.getenv('default_quantity'),
    }
    main(sclad, setting)
