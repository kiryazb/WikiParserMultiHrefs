import requests
from parameters import URL, direct, multiproc
import multiprocessing
from math import ceil
import re
from bs4 import BeautifulSoup
from datetime import datetime
import csv

LANG = '/'.join(URL.split("/")[0:3])


def get_page(url):
    return requests.get(url).text if requests.get(url) != 200 else print(
        f"Ошибка, Статус код: {requests.get(url).status_code}")


def get_columns(page):
    hrefs = []
    for columns in page:
        main_page_li = columns.find_all("li")
        for item in main_page_li:
            hrefs.append(f"{LANG}/" + item.find("a").get("href"))
    return hrefs


def get_wide(page):
    hrefs = []
    for item in page:
        all_tr = item.find_all("tr")
        for tr in all_tr:
            try:
                hrefs.append(f"{LANG}/" + tr.find("td").find("a").get("href"))
            except:
                pass
    return hrefs


def get_wikitable(page):
    hrefs = []
    for item in page:
        all_tr = item.find_all("tr")
        for tr in all_tr:
            try:
                hrefs.append(f"{LANG}/" + tr.find("td").find("a").get("href"))
            except:
                pass
    return hrefs


def page_count_foo(page):
    numbers_text = page.find(class_="mw-category-generated").find(id="mw-pages").find("p").text
    digits = re.findall(r'\d+', numbers_text)
    number1, number2 = int(digits[0]), int(digits[1])
    page_count = int(ceil(number2 / number1))
    return page_count


def get_mw_category():
    hrefs = []
    next_url = URL
    new_page = BeautifulSoup(get_page(next_url), "lxml")
    page_count = page_count_foo(new_page)
    for count in range(page_count):
        new_page = BeautifulSoup(get_page(next_url), "lxml")
        new_page_alphabet = new_page.find(class_="mw-category-columns")
        try:
            all_categories_class = new_page_alphabet.find_all(class_="mw-category-group")
        except:
            break
        for item in all_categories_class:
            all_li = item.find_all("li")
            for li in all_li:
                hrefs.append(f"{LANG}/" + li.find("a").get("href"))
        new_page = BeautifulSoup(get_page(next_url), "lxml")
        if count == 0:
            next_url = LANG + new_page.find(class_="mw-category-generated").find(id="mw-pages").find_all("a")[1].get(
                "href")
        if count > 0:
            next_url = LANG + new_page.find(class_="mw-category-generated").find(id="mw-pages").find_all("a")[2].get(
                "href")
    return hrefs


def check_human(statements_list):
    for item in statements_list[:5]:
        key = item.find(class_="wikibase-statementgroupview-property-label")
        if key:
            key = key.text
            if key == "instance of":
                info_statements = item.find(
                    class_=["wikibase-snakview-value", "wikibase-snakview-variation-valuesnak"])
                if info_statements:
                    if info_statements.find(string=True).text == "human":
                        return True
    return False


def get_info(url):
    info = {"date of birth": "Не указано",
            "place of birth": "Не указано",
            "date of death": "Не указано"}
    url_page = BeautifulSoup(get_page(url), "lxml")
    name = url_page.find("span", class_="mw-page-title-main")
    if name:
        name = name.text
    if url_page.find(id="t-wikibase", class_="mw-list-item"):
        wikidata_href = url_page.find(id="t-wikibase", class_="mw-list-item").find("a").get("href")
        statements_src = BeautifulSoup(get_page(wikidata_href), "lxml")
        statements_list = statements_src.find_all(class_=["wikibase-statementgroupview", "listview-item"])
        if check_human(statements_list):
            for item in statements_list[:14]:
                key = item.find(class_="wikibase-statementgroupview-property-label")
                if key:
                    key = key.text
                    if key in info:
                        info_statements = item.find(
                            class_=["wikibase-snakview-value", "wikibase-snakview-variation-valuesnak"])
                        if info_statements:
                            info[key] = info_statements.find(string=True).text
            info["FIO"] = name
            return info
        return 0
    return 0


def record_csv(url):
    info = get_info(url)
    if info != 0:
        try:
            with open(direct, "a", newline="") as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow((info["FIO"], info["date of birth"],
                                 info["place of birth"], info["date of death"]))
        except:
            with open(direct, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow((info["FIO"], info["date of birth"],
                                 info["place of birth"], info["date of death"]))


if __name__ == "__main__":

    start = datetime.now()
    with open(direct, "w", newline="") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(("ФИО", "Дата рождения", "Место рождения", "Дата смерти"))

    main_page_url = get_page(URL)

    main_page_src = BeautifulSoup(main_page_url, "lxml")

    all_url = []

    main_page_columns = main_page_src.select('.columns:not([class*=" "])')
    if main_page_columns:
        all_url = get_columns(main_page_columns)

    main_page_tr = main_page_src.find_all(class_="wide")
    if main_page_tr:
        all_url = get_wide(main_page_tr)

    main_page_tr1 = main_page_src.select('.wikitable:not([class*=" "])')
    if main_page_tr1:
        all_url = get_wikitable(main_page_tr1)

    main_page_alphabet = main_page_src.find(class_="mw-category-columns")
    if main_page_alphabet:
        all_url = get_mw_category()

    if multiproc < 1 or multiproc > 5:
        print("Incorrect multiproc value")
    if multiproc == 1:
        count_curr = 0
        count = len(all_url)
        while count > 0:
            record_csv(all_url[count_curr])
            count -= multiproc
            count_curr += multiproc
    if multiproc == 2:
        count_curr = 0
        count = len(all_url)
        while count > 0:
            if count == 1:
                record_csv(all_url[count_curr])
                break
            if count >= 2:
                urls = [all_url[count_curr], all_url[count_curr + 1]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            count -= multiproc
            count_curr += multiproc
    if multiproc == 3:
        count_curr = 0
        count = len(all_url)
        while count > 0:
            if count == 1:
                record_csv(all_url[count_curr])
                break
            if count == 2:
                urls = [all_url[count_curr], all_url[count_curr + 1]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            if count >= 3:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            count -= multiproc
            count_curr += multiproc
    if multiproc == 4:
        count_curr = 0
        count = len(all_url)
        while count > 0:
            if count == 1:
                record_csv(all_url[count_curr])
                break
            if count == 2:
                urls = [all_url[count_curr], all_url[count_curr + 1]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
                break
            if count == 3:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
                break
            if count >= 4:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2], all_url[count_curr + 3]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            count -= multiproc
            count_curr += multiproc
    if multiproc == 5:
        count_curr = 0
        count = len(all_url)
        while count > 0:
            if count == 1:
                record_csv(all_url[count_curr])
                break
            if count == 2:
                urls = [all_url[count_curr], all_url[count_curr + 1]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
                break
            if count == 3:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
                break
            if count == 4:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2],
                        all_url[count_curr + 3]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            if count >= 5:
                urls = [all_url[count_curr], all_url[count_curr + 1], all_url[count_curr + 2],
                        all_url[count_curr + 3], all_url[count_curr + 4]]
                with multiprocessing.Pool(len(urls)) as pool:
                    pool.map(record_csv, urls)
            count -= multiproc
            count_curr += multiproc

        print(datetime.now() - start)
