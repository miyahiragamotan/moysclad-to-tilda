# export_of_goods_to_yml.py

import os
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
from time import sleep
from dotenv import load_dotenv
from module.logger_config import LoggerConfig
import module.msclad as msclad

# Настройки логирования
logger = LoggerConfig('logs/export_of_goods_to_yml').get_logger(__name__)
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
            file_path = create_yml_file(items)
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
                    item["salePrice"] = salePrice["value"]
                    break

            items.append(item)
    return items


def create_yml_file(items, file_path="export_of_goods.yml"):
    yml_catalog = ET.Element(
        "yml_catalog",
        attrib={
            "date": datetime.now(timezone(timedelta(hours=3))).isoformat(timespec="seconds")
        },
    )
    shop = ET.SubElement(yml_catalog, "shop")

    ET.SubElement(shop, "name").text = "LONES"
    ET.SubElement(shop, "company").text = "lones"
    ET.SubElement(shop, "url").text = "https://lones-computers.ru"
    ET.SubElement(shop, "platform").text = "Tilda Publishing"
    ET.SubElement(shop, "version").text = "1.0"

    currencies = ET.SubElement(shop, "currencies")
    ET.SubElement(currencies, "currency", attrib={"id": "RUR", "rate": "1"})

    categories = ET.SubElement(shop, "categories")
    ET.SubElement(categories, "category", attrib={"id": "1", "parentId": "2"}).text = "Настольные компьютеры"

    offers = ET.SubElement(shop, "offers")

    for item in items:
        if "variants" not in item or not item["variants"]:
            continue

        variant = item["variants"][0]
        offer = ET.SubElement(
            offers,
            "offer",
            attrib={
                "id": variant["id"],
                "group_id": item["id"],
            },
        )
        ET.SubElement(offer, "name").text = variant["name"]
        ET.SubElement(offer, "vendor").text = "LONESPC"
        ET.SubElement(offer, "count").text = "9999"
        ET.SubElement(offer, "price").text = str(variant["salePrice"])
        ET.SubElement(offer, "currencyId").text = "RUR"
        ET.SubElement(offer, "categoryId").text = "140451609632"

        characteristics = list(variant.get("characteristics", {}).items())
        for name, value in characteristics[:4]:
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
    main(sclad)
