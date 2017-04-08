"""mod: 'tispoon.reader'

"""

import os
import re
import requests

from bs4 import BeautifulSoup as bs
from time import sleep
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


__all__ = ('get_post')

extract_dir = str(Path().resolve()) + '/_article'
if not os.path.exists(extract_dir):
    os.makedirs(extract_dir)

headers = {
    'User-Agent':
        'tispoon/0.1'
}

env = Environment(
    loader=PackageLoader('tispoon', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
    )

template = env.get_template('base.html')


def get_post():
    url = input('Please enter a url: ')

    if '/' not in url[-1]:
        url = url + '/'

    post_num = 1
    target = url + str(post_num)
    result = bs(requests.get(target, headers=headers).text, 'lxml')
    latest_num = get_latest_num(result)

    while post_num < latest_num:
        print("Start collecting post " + str(post_num))

        target = url + str(post_num)
        result = bs(requests.get(target, headers=headers).text, 'lxml')

        if is_post_exist(result):
            ext_path = extract_dir + "/" + str(post_num) + "/"
            if not os.path.exists(ext_path):
                os.makedirs(ext_path)

            post_title = get_post_title(result)
            post_article = get_article_image(
                get_post_article(result),
                ext_path)

            make_index(post_title, post_article, ext_path)
            print("Finished post " + str(post_num))

        post_num += 1
        sleep(3)


def get_latest_num(source):
    try:
        result = source.find("body")\
                        .find("span", class_="numbox")\
                        .find("a", class_="num")\
                        .get("href")
    except AttributeError:
        result = source.find("body")\
                        .find("div", class_="num-box")\
                        .find("a")\
                        .get("href")
    if "/" in result:
        result = re.sub(r'/', '', result)
        print(result)
    return int(result)


def is_post_exist(source):
    result = source.find("body")\
                    .find("div", id="content")\
                    .find("div", class_="absent_post")

    if result is None:
        return True
    else:
        print("post not exist, pass.")
        return False


def get_post_title(source):
    result = source.find("body")\
                        .find("div", id="content")\
                        .find_all("a")
    if result is None:
        return "Default title"
    else:
        return result[0].string


def get_post_article(source):
    image_list = []
    result = source.find("body")\
                    .find("div", id="content")\
                    .find("div", class_="article")\
                    .find_all("img")

    if result is not None:
        for image in result:
            if "저작자 표시" in image.get('alt', '') or \
            "신고" in image.get('alt', ''):
                pass
            else:
                image_list.append(image.get('src', ''))
        return image_list


def get_article_image(source, path):
    image_num = 1
    extract_list = []
    path = path + "/img/"
    if not os.path.exists(path):
            os.makedirs(path)

    for img_url in source:
        r = requests.get(img_url)

        if r.status_code is 200:
            file_ext = "." + r.headers['content-type'].split("/", 1)[1]
            file_name = str(image_num) + file_ext
            with open(path + file_name, 'wb') as f:
                f.write(r.content)
            image_num += 1
            extract_list.append(file_name)

    return extract_list


def make_index(title, articles, path):
    result = template.render(title=title, articles=articles)

    with open(path + 'index.html', 'w') as f:
        f.write(result)
