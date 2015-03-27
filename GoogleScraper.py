#!/usr/bin/python3
# -*- coding: utf-8 -*-

# This is a little module to use the google search engine
# It compromises the google terms of service. Please note
# that.

# Of course, when searching for suspicious terms (including
# dorks or patterns of vulnerable applicatios) google rec-
# ognizes you pretty fast and blocks your IP address and 
# maybe even your broswer signature (UA the most notorious
# needle here). I could implement proxy (socks 4/5, http/s)
# support, but it seems that urllib3 doesn't support proxies
# yet. Then I could fall back to use urllib.request instead
# of requests, but it seems that the module which provides
# the possibility to socksify your requests (SocksiPy) looks
# pretty much outdated. Therefore I decided not to implement
# any complex partly functional solution. Does this mean we 
# are limited until Google blocks our IP address?

# Absolutely not. There is a wonderful tool called proxychains
# which hooks all the low level socket stuff and reroutes all
# traffic through the proxy (Yes, including DNS queries).

# I will work on a not too slow solution to combine proxychains
# with this module. Seems like it's not a trivial task, since 
# proxychains only supports configuration files and I need a dynamic
# configuration, because I want to call proxychains once for google
# search request with exactly one proxy (no chaining). Proxychains isn't
# directly made for it, maybe I have to hack some additional functionality
# into proxychains...
import os

__VERSION__ = '0.1'
__AUTHOR__ = 'Nikolai'
__WEBSITE__ = 'incolumitas.com'

# TODO
# Need to read that:
# http://docs.python.org/3.2/tutorial/classes.html
# http://docs.python-requests.org/en/latest/
# http://www.jeffknupp.com/blog/2012/10/04/writing-idiomatic-python/
# http://docs.python.org/3.2/library/itertools.html

import sys
import re
import requests
from random import choice
from enum import Enum


class GoogleSearchError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return 'Exception in GoogleSearch class'


class InvalidNumberResultsException(GoogleSearchError):
    def __init__(self, number_of_results):
        self.nres = number_of_results

    def __str__(self):
        return '%d is not a valid number of results per page' % self.nres


class GoogleScraperResult:
    PRECISE = 0
    APPROXIMATE = -1
    OUT_OF_RANGE = -2

    def __init__(self, precision_type, value):
        self.precision_type = precision_type
        self.value = int(value.replace(',', '').replace('.', ''))


class GoogleScraper:
    '''
	Offers a fast way to query the google search engine. It returns a list
	of all found URLs found on x pages with n search results per page.
	You can define x and n, sir!
	'''
    _RESULTS_PER_PAGE = 100

    # Valid URL (taken from django)
    _REGEX_VALID_URL = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    _REGEX_VALID_URL_SIMPLE = re.compile(
        'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    # http://www.blueglass.com/blog/google-search-url-parameters-query-string-anatomy/
    _GOOGLE_SEARCH = 'http://www.google.com/search'

    _GOOGLE_SEARCH_PARAMS = {
        'q': '', # the search term
        'num': _RESULTS_PER_PAGE, # the number of results per page
        'start': '0', # the offset to the search results. page number = (start / num) + 1
        'pws': '0', # personalization turned off'pws':
        'safe': 'active',
        'tbm': None
    }

    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
        'DNT': '1'
    }

    # Keep the User-Agents updated.
    # I guess 9 different UA's is engough, since many users
    # have the same UA (and only a different IP).
    # Get them here: http://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    _UAS = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17',
        'Mozilla/5.0 (Linux; U; Android 2.2; fr-fr; Desire_A8181 Build/FRF91) App3leWebKit/53.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; FunWebProducts; .NET CLR 1.1.4322; PeoplePal 6.2)',
        'Mozilla/5.0 (Windows NT 5.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
        'Opera/9.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.01',
        'Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 3.5.30729)'
    ]

    def __init__(self, search_term, file_name, start=0, tbm=None):
        self.search_term = search_term
        self.start = start
        self.tbm = tbm
        self.file_name=file_name


    # private internal functions who implement the actual stuff

    # When random == True, several headers (like the UA) are chosen
    # randomly.
    def _build_query(self, random=False):
        self._GOOGLE_SEARCH_PARAMS['q'] = self.search_term
        self._GOOGLE_SEARCH_PARAMS['start'] = str(self.start)
        self._GOOGLE_SEARCH_PARAMS['tbm'] = self.tbm

        if random:
            GoogleScraper._HEADERS['User-Agent'] = choice(GoogleScraper._UAS)


    def request(self):
        self._build_query(True)
        try:
            r = requests.get(self._GOOGLE_SEARCH, headers=self._HEADERS,
                             params=self._GOOGLE_SEARCH_PARAMS, timeout=3.0)
        except requests.ConnectionError as cerr:
            print('Network problem occurred')
            sys.exit(1)
        except requests.Timeout as terr:
            print('Connection timeout')
            sys.exit(1)
        if not r.ok:
            print('HTTP Error:', r.status_code)
            if str(r.status_code)[0] == '5':
                print('Maybe google recognizes you as sneaky spammer after'
                      ' you requested their services too inexhaustibly :D')
            sys.exit(1)
        html = r.text
        return html
    LAST_PAGE_INDICATOR = 'In order to show you the most relevant results, we'

    def count(self):
        html = self.request()
        first_try_file = open(self.file_name + ".html", "wb")
        first_try_file.write(html)
        first_try_file.close()
        try:
            precise_count = re.search('Page [0-9]+ of ([0-9]+) results', html).group(1)
            return GoogleScraperResult(GoogleScraperResult.PRECISE, precise_count)
        except:
            try:
                approximate_count = re.search('Page [0-9]+ of about ([0-9,]+) results', html).group(1)
                if html.find(self.LAST_PAGE_INDICATOR) > 0:
                    return GoogleScraperResult(GoogleScraperResult.PRECISE, approximate_count)
                else:
                    return GoogleScraperResult(GoogleScraperResult.APPROXIMATE, approximate_count)
            except:
                try:
                    approximate_count = re.search('About ([0-9,]+) results', html).group(1)
                    if html.find(self.LAST_PAGE_INDICATOR) > 0:
                        return GoogleScraperResult(GoogleScraperResult.PRECISE, approximate_count)
                    else:
                        return GoogleScraperResult(GoogleScraperResult.APPROXIMATE, approximate_count)
                except:
                    return GoogleScraperResult(GoogleScraperResult.OUT_OF_RANGE, '-1')

