# module/moysclad.py
# Форматируем товары, собираем всю информацию
import module.msclad_api as msclad_api

def format_products(logger, sclad, products):
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
            item["variants"] = variants_product(logger, sclad, item["id"])
        else:
            logger.info(f"У товара \"{item['name']}\" не найдены модификации.")
            for salePrice in product['salePrices']:
                if salePrice['priceType']['id'] == sclad["id_sale_price"]:
                    item["salePrice"] = salePrice["value"] / 100 if salePrice["value"] != 0 else 0
                    break
        items.append(item)
    return items

# Cобираем всю информацию по модификациям
def variants_product(logger, sclad, id):
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/variant?filter=productid={id}"
    variants = msclad_api.make_request("GET", url, sclad["token"])
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
                        item["salePrice"] = salePrice["value"] / 100 if salePrice["value"] != 0 else 0
                    else:
                        item["salePrice"] = 0
                    break

            items.append(item)
    return items  