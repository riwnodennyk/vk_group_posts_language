# coding=utf-8
import os
import re
import urllib2
import webbrowser
import GoogleScraper
import urlparse
from google import search
from GoogleScraper import GoogleScraper
from GoogleScraper import GoogleScraperResult
from transliterate.utils import translit
from unidecode import unidecode


class GoogleResultCounter:
    def __init__(self, query, country=None, tbm=None, extended=False):
        if country is None:
            self.query = query
        else:
            self.query = query + " site:." + country
        print self.query
        self.tbm = tbm
        self.extended = extended

        self.request_index = 1

    def open_search_query(self):
        url = "https://www.google.com.ua/search?q=" + urllib2.quote(self.query.encode("utf8")) + "&start=980"
        if self.extended:
            url += "&safe=active&filter=0&psj=1"
        if self.tbm != None:
            url += "&tbm=" + self.tbm
        webbrowser.open(url)

    def count_google_results(self, proposed_count):
        self.request_index += 1
        #print "request #%s" % self.request_index
        return GoogleScraper(self.query, str(self.request_index), start=proposed_count, tbm=self.tbm).count()

    def bisection(self, start, end):
        #print "[" + str(start) + ", " + str(end) + "]"
        middle = (start + end) / 2
        middle_count = self.count_google_results(middle)
        if middle_count.precision_type == GoogleScraperResult.APPROXIMATE:
            if middle_count.value <= middle:
                return self.bisection(start, middle_count.value)
            else:
                return self.bisection(middle, middle_count.value)
        elif middle_count.precision_type == GoogleScraperResult.OUT_OF_RANGE:
            return self.bisection(start, middle)
        else:
            print "(" + self.request_index + ")->",
            return middle_count.value

    #def multiply_estimate(self, estimation=1000):
    #    if self.count_google_results(estimation) != GoogleScraper.GoogleScraperResult.OUT_OF_RANGE:
    #        return self.multiply_estimate(estimation * 2)
    #    else:
    #        return self.bisection(1, estimation)

    def count(self):
        estimation = GoogleScraper(self.query, str(self.request_index), 0, self.tbm).count()
        if estimation.precision_type == GoogleScraperResult.APPROXIMATE:
            return self.bisection(0, estimation.value)
        elif estimation.precision_type == GoogleScraperResult.PRECISE:
            return estimation.value
        else:
            return 0


#def ensure_folder(folder_name):
#    if not os.path.exists(folder_name):
#        os.mkdir(folder_name)
#    os.chdir(folder_name)


if __name__ == '__main__':
    #for url in search('Mariposa botnet', tld='es', lang='es', stop=20):
    #    print(url)
    print "Requesting..."

    counties = ('ua', 'ru')
    queries = (unicode(u'"полиэтиленовый кулек"'), unicode(u'"полиэтиленовый пакет"'))
    for query in queries:
        #ensure_folder(query)
        print
        print query
        #for prefix in prefixes:
        #    ensure_folder(prefix)
        for country in counties:
            #ensure_folder(country)
            GoogleResultCounter(query, country, extended=True).open_search_query()