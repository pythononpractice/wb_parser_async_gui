import asyncio
import datetime
import time

import aiohttp
import requests
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.wildberries.ru",
    'Content-Type': 'application/json; charset=utf-8',
    'Transfer-Encoding': 'chunked',
    "Connection": "keep-alive",
    'Vary': 'Accept-Encoding',
    'Content-Encoding': 'gzip',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site"
}
CATALOG_URL = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v2.json'


def get_catalogs_wb() -> dict:
    """получаем полный каталог Wildberries"""
    return requests.get(CATALOG_URL, headers=HEADERS).json()


def get_data_category(catalogs_wb: dict) -> list:
    """сбор данных категорий из каталога Wildberries"""
    catalog_data = []
    if isinstance(catalogs_wb, dict) and 'childs' not in catalogs_wb:
        catalog_data.append({
            'name': f"{catalogs_wb['name']}",
            'shard': catalogs_wb.get('shard', None),
            'url': catalogs_wb['url'],
            'query': catalogs_wb.get('query', None)
        })
    elif isinstance(catalogs_wb, dict):
        catalog_data.extend(get_data_category(catalogs_wb['childs']))
    else:
        for child in catalogs_wb:
            catalog_data.extend(get_data_category(child))
    return catalog_data


def search_category_in_catalog(url: str, catalog_list: list) -> dict:
    """проверка пользовательской ссылки на наличии в каталоге"""
    for catalog in catalog_list:
        if catalog['url'] == url.split('https://www.wildberries.ru')[-1]:
            return catalog


def get_data_from_json(json_file: dict) -> list:
    """извлекаем из json данные"""
    data_list = []
    for data in json_file['data']['products']:
        data_list.append({
            'id': data.get('id'),
            'Наименование': data.get('name'),
            'Цена': int(data.get("priceU") / 100),
            'Цена со скидкой': int(data.get('salePriceU') / 100),
            'Скидка': data.get('sale'),
            'Бренд': data.get('brand'),
            'Рейтинг': data.get('rating'),
            'Продавец': data.get('supplier'),
            'Рейтинг продавца': data.get('supplierRating'),
            'Кол-во отзывов': data.get('feedbacks'),
            'Рейтинг отзывов': data.get('reviewRating'),
            'Промо текст карточки': data.get('promoTextCard'),
            'Промо текст категории': data.get('promoTextCat'),
            'Ссылка': f'https://www.wildberries.ru/catalog/{data.get("id")}/detail.aspx?targetUrl=BP'
        })
    return data_list


async def scrap_page(page: int, shard: str, query: str, low_price: int, top_price: int, discount: int = None, log_output = None) -> dict:
    """Сбор данных со страниц"""
    url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub' \
          f'&dest=-1257786' \
          f'&locale=ru' \
          f'&page={page}' \
          f'&priceU={low_price * 100};{top_price * 100}' \
          f'&sort=popular&spp=0' \
          f'&{query}' \
          f'&discount={discount}'

    async with aiohttp.ClientSession() as session:
        r = await session.get(url=url)
        log_output.append(f'[+] Страница {page}')
        for _ in range(5):
            if r.status == 200:
                break
            r = await session.get(url=url)

        if r.status != 200:
            return {}
        return await r.json(content_type=None)


def save_excel(data: list, filename: str, log_output):
    """сохранение результата в excel файл"""
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'{filename}.xlsx')
    df.to_excel(writer, sheet_name='data', index=False)
    # указываем размеры каждого столбца в итоговом файле
    writer.sheets['data'].set_column(0, 1, width=10)
    writer.sheets['data'].set_column(1, 2, width=34)
    writer.sheets['data'].set_column(2, 3, width=8)
    writer.sheets['data'].set_column(3, 4, width=9)
    writer.sheets['data'].set_column(4, 5, width=4)
    writer.sheets['data'].set_column(5, 6, width=10)
    writer.sheets['data'].set_column(6, 7, width=5)
    writer.sheets['data'].set_column(7, 8, width=25)
    writer.sheets['data'].set_column(8, 9, width=10)
    writer.sheets['data'].set_column(9, 10, width=11)
    writer.sheets['data'].set_column(10, 11, width=13)
    writer.sheets['data'].set_column(11, 12, width=19)
    writer.sheets['data'].set_column(12, 13, width=19)
    writer.sheets['data'].set_column(13, 14, width=67)
    writer.close()
    log_output.append(f'Все сохранено в {filename}.xlsx\n')


async def parser(log_output, url: str, low_price: int = 1, top_price: int = 1000000, discount: int = 0, save_path: str = ''):
    """основная функция"""
    start = time.time()  # запишем время старта
    # получаем данные по заданному каталогу
    catalog_data = get_data_category(get_catalogs_wb())
    try:
        # поиск введенной категории в общем каталоге
        category = search_category_in_catalog(url=url, catalog_list=catalog_data)
        data_list = []
        tasks = []
        for page in range(1, 51):  # вб отдает 50 страниц товара
            tasks.append(
                asyncio.create_task(
                    scrap_page(
                        page=page,
                        shard=category['shard'],
                        query=category['query'],
                        low_price=low_price,
                        top_price=top_price,
                        discount=discount,
                        log_output=log_output
                    )
                )
            )
        result_list = await asyncio.gather(*tasks)
        for data in result_list:
            if len(get_data_from_json(data)) > 0:
                data_list.extend(get_data_from_json(data))

        log_output.append(f'Сбор данных завершен. Собрано: {len(data_list)} товаров.')
        # сохранение найденных данных
        save_excel(data_list, f'{category["name"]}_from_{low_price}_to_{top_price}', log_output)
        log_output.append(f'Ссылка для проверки: {url}?priceU={low_price * 100};{top_price * 100}&discount={discount}')
        end = time.time()  # запишем время завершения кода
        total = end - start  # расчитаем время затраченное на выполнение кода
        log_output.append(f"Затраченное время: {str(round(total, 2))} c")
    except TypeError as e:
        log_output.append(f'Ошибка! Возможно не верно указан раздел. Удалите все доп фильтры и ссылки {e}')
    except PermissionError:
        log_output.append('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')


async def main():
    url = 'https://www.wildberries.ru/catalog/dlya-doma/mebel/kronshteiny'  # сюда вставляем вашу ссылку на категорию
    low_price = 100  # нижний порог цены
    top_price = 1000000  # верхний порог цены
    discount = 10 # скидка в %
    start = datetime.datetime.now()  # запишем время старта

    await parser(url=url, low_price=low_price, top_price=top_price, discount=discount)

    end = datetime.datetime.now()  # запишем время завершения кода
    total = end - start  # расчитаем время затраченное на выполнение кода
    print("Затраченное время:" + str(total))


if __name__ == '__main__':
    asyncio.run(main())
