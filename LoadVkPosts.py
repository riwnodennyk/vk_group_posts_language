from collections import namedtuple
from enum import Enum
import statistics
import re
import math
import requests
import langid

UA_REVO = -38854900
LUHANSK = -2424065
OZIV = -72444174
TROIESHCHYNA = -3933663
TYPICAL_KYIV = -32195333
DYNAMO_KYIV = -4645142
POLTAWA = -1919231

__author__ = 'aindrias'

Post = namedtuple('Post', 'language like share')


class Language(Enum):
    UKRAINIAN = 1
    RUSSIAN = 2
    BOTH = 3
    UNDEFINED = 4


def load_html(group_id, offset):
    url = 'https://vk.com/al_wall.php'
    data = 'act=get_wall&al=1&fixed=&offset=' + offset.__str__() + '&owner_id=' + group_id.__str__() + '&type=own'
    return requests.post(url, data).text


def language_langid(text):
    classify = langid.classify(text)
    lang_code = classify[0]
    probability = classify[1]
    if probability < 0.5:
        return Language.UNDEFINED
    elif lang_code == 'uk':
        return Language.UKRAINIAN
    elif lang_code == 'ru':
        return Language.RUSSIAN
    else:
        return Language.UNDEFINED


def language(text):
    text = text.replace('Показати повністю', '')

    ukrainian_letters = set('іІїЇєЄґҐ')
    looks_like_ukrainian = any((c in ukrainian_letters) for c in text)

    russian_letters = set('ЁёЪъЭэЫы')
    looks_like_russian = any((c in russian_letters) for c in text)

    if looks_like_ukrainian and looks_like_russian:
        return Language.BOTH
    elif looks_like_ukrainian:
        return Language.UKRAINIAN
    elif looks_like_russian:
        return Language.RUSSIAN
    else:
        return language_langid(text)


def parse_single_post(snippet):
    message = re.search('<div class="wall_post_text">(.*?)</div>', snippet)
    like = re.search('post_like_count fl_l" id="like_count-\d*_\d*">(\d*)</', snippet)
    share = re.search('post_share_count fl_l" id="share_count-\d*_\d*">(\d*)</', snippet)
    if message and like and share:
        return Post(language(message.group(1)), int('0' + like.group(1)), int('0' + share.group(1)))
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
              + statistics.median(numbers_list).__int__().__str__(), end="")
        if numbers_list.__len__() > 1:
            print(' SD ' + statistics.stdev(numbers_list).__int__().__str__())

    print('\n[%s]' % ', '.join(map(str, transform(numbers_list))))
    print('\n')


def transform(param):
    param.sort()
    result = []
    while len(param) > 0:
        pop = param.pop(0)
        while result.__len__() <= pop:
            result.append(0)
        result[-1] += 1
    return result


def analyze(posts):
    ukrainian_posts = []
    russian_posts = []
    undefined_posts = []
    both_posts = []
    for post in posts:
        if post.language == Language.UKRAINIAN:
            ukrainian_posts.append(post)
        elif post.language == Language.RUSSIAN:
            russian_posts.append(post)
        elif post.language == Language.UNDEFINED:
            undefined_posts.append(post)
        elif post.language == Language.BOTH:
            both_posts.append(post)

    print("LIKES", "\n")
    print("UKRAINIAN " + (ukrainian_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list((likes(ukrainian_posts)))
    print("RUSSIAN " + (russian_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list((likes(russian_posts)))
    print("BOTH " + (both_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list(likes(both_posts))
    print("UNDEFINED " + (undefined_posts.__len__() * 100 / posts.__len__()).__int__().__str__() + '%')
    print_list(likes(undefined_posts))

    # print("SHARES", "\n")
    # print("UKRAINIAN")
    # print_list(shares(ukrainian_posts))
    # print("RUSSIAN")
    # print_list(shares(russian_posts))
    # print("BOTH")
    # print_list(shares(both_posts))
    # print("UNDEFINED")
    # print_list(shares(undefined_posts))


def likes(posts):
    return [post.like for post in posts]


def shares(posts):
    return [post.share for post in posts]


def load_posts(group_id, count=50):
    offset = 20
    posts = []
    while posts.__len__() < count:
        posts.extend(parse_posts(load_html(group_id, offset)))
        offset += 10
        print(posts.__len__(), '..')
    print('\n')
    return posts


if __name__ == '__main__':
    analyze(load_posts(TYPICAL_KYIV, 5000))