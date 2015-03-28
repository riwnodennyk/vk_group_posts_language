from collections import namedtuple
from enum import Enum
import statistics
import re
import math

import requests


__author__ = 'aindrias'

Post = namedtuple('Post', 'language like share')


class Language(Enum):
    UKRAINIAN = 1
    RUSSIAN = 2
    UNDEFINED = 3


def load_html(offset):
    url = 'https://vk.com/al_wall.php'
    data = 'act=get_wall&al=1&fixed=5509812&offset=' + offset.__str__() + '&owner_id=-38854900&type=own'
    # headers = ['Origin: https://vk.com', 'X-Requested-With: XMLHttpRequest',
    # 'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36',
    # 'Content-Type: application/x-www-form-urlencoded', 'Accept: */*', 'Referer: https://vk.com/uarevo',
    # 'Accept-Encoding: gzip, deflate',
    # 'Accept-Language: ro,tr;q=0.8,fr;q=0.6,de;q=0.4,be;q=0.2,uk;q=0.2,en-US;q=0.2,en;q=0.2,pl;q=0.2',
    # 'Cookie: remixdt=-3600; remixstid=1997731857_d790546204bbbd6b2f; audio_time_left=0; remixtst=3f60ef96; remixlang=1; remixsid=e7d287cc16c88eaf1ecf035b484ad3106c82df4a5eba70da09999; remixsslsid=1; remixrefkey=23b3c7529ae25b9078; audio_vol=100; remixseenads=1; remixflash=17.0.0; remixscreen_depth=24',
    # 'Cache-Control: no-cache', 'Postman-Token: 4954bd28-4b5c-bd92-7577-3749d7af9667']
    return requests.post(url, data).text


def language(text):
    text = text.replace('Показати повністю', '')
    ukrainian_letters = set('іІїЇєЄґҐ')
    looks_like_ukrainian = any((c in ukrainian_letters) for c in text)

    russian_letters = set('ЁёЪъЭэЫы')
    looks_like_russian = any((c in russian_letters) for c in text)

    if looks_like_ukrainian and looks_like_russian:
        return Language.UNDEFINED
    elif looks_like_ukrainian:
        return Language.UKRAINIAN
    elif looks_like_russian:
        return Language.RUSSIAN
    else:
        return Language.UNDEFINED


def parse_single_post(snippet):
    message = re.search('<div class="wall_post_text">(.*?)</div>', snippet)
    like = re.search('post_like_count fl_l" id="like_count-\d*_\d*">(\d*)</', snippet)
    share = re.search('post_share_count fl_l" id="share_count-\d*_\d*">(\d*)</', snippet)
    if message and like and share:
        return Post(language(message.group(1)), int(like.group(1)), int(share.group(1)))
    else:
        # Either of message, likes count or shares count can't be parsed.
        # Usually it's message. Because posts happen be image-only or video-only.
        return None


def parse_posts(html):
    parsed_posts = []

    for snippet in html.split('post all own'):
        post = parse_single_post(snippet)
        if post:
            parsed_posts.append(post)
    return parsed_posts


def print_list(numbers_list):
    print('[%s]' % ', '.join(map(str, numbers_list)))
    if numbers_list.__len__() == 0:
        pass
    else:
        print('MEAN '
              + (statistics.mean(numbers_list)).__int__().__str__()
              + ' MEDIAN '
              + statistics.median(numbers_list).__int__().__str__())
        if numbers_list.__len__() > 1:
            print(' VARIANCE ' + math.sqrt(statistics.variance(numbers_list)).__int__().__str__())

    print('\n')


def analyze(posts):
    ukrainian_posts = []
    russian_posts = []
    undefined_posts = []
    for post in posts:
        if post.language == Language.UKRAINIAN:
            ukrainian_posts.append(post)
        elif post.language == Language.RUSSIAN:
            russian_posts.append(post)
        elif post.language == Language.UNDEFINED:
            undefined_posts.append(post)

    print("LIKES", "\n")
    print("UKRAINIAN " + (ukrainian_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list(likes(ukrainian_posts))
    print("RUSSIAN " + (russian_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list(likes(russian_posts))
    print("UNDEFINED " + (undefined_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list(likes(undefined_posts))

    print("SHARES", "\n")
    print("UKRAINIAN")
    print_list(shares(ukrainian_posts))
    print("RUSSIAN")
    print_list(shares(russian_posts))
    print("UNDEFINED")
    print_list(shares(undefined_posts))


def likes(posts):
    return [post.like for post in posts]


def shares(posts):
    return [post.share for post in posts]


def load_posts(count=20):
    offset = 10
    posts = []
    while posts.__len__() < count:
        posts.extend(parse_posts(load_html(offset)))
        offset += 10
        print(posts.__len__(), '..')
    print('\n')
    return posts


if __name__ == '__main__':
    analyze(load_posts(50))