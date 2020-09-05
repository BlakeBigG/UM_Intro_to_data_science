# -*- coding: utf-8 -*-
from lxml import html
from dateutil.parser import parse
from datetime import datetime
import re
import time
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utilities import fix_page


base='http://lupuscommunity.messageboardchat.com'

def get_subforums():
    for sub in html.parse(base).xpath('//*[@id="main_container"]/div/table[1]/tr[1]/td/table/tr/td[2]')[1:]:
        yield {'url': base+sub.xpath('./a/@href')[0],
               'name': sub.xpath('./a/text()')[0],
               'description': sub.xpath('./span/text()')[0].strip()}

def get_threads(sub):
    page=html.parse(sub)
    def scrape_page():
        for thread in page.xpath('//*[@id="main_container"]/div[2]/form[1]/table/tr[1]/td/table/tr/td[2]/a'):
            modifiers=[]
            if thread.xpath('./../../td[1]/span/@class')[0] == 'locked_thread_icon':
                modifiers.append('locked')
            try:
                if thread.xpath('./../span[1]/@class')[0] == 'pin_img':
                    modifiers.append('pinned')
            except:
                pass
            yield {'url': base+thread.attrib['href'], 'title': thread.text, 'modifiers': modifiers}
    for thread in scrape_page():
        yield thread
    pagination = page.xpath('//div[@id="pagination"]')
    if pagination:
        next = pagination[0].xpath('.//a[text()="Next"]/@href')
        while next:
            time.sleep(5)
            page=html.parse(base+next[0])
            pagination = page.xpath('//div[@id="pagination"]')
            if pagination:
                next = pagination[0].xpath('.//a[text()="Next"]/@href')
            else:
                next = None
            for thread in scrape_page():
                yield thread

def scrape_thread(thread):
    print thread
    id = re.findall('(\d+)$', thread)[0]
    url = 'http://lupuscommunity.messageboardchat.com/printthread/?id={}&perpage=100'.format(id)
    time.sleep(5)
    page = fix_page(html.parse(url), base)
    def scrape_page():
        for row in page.xpath('//table[2]/tr[1]/following-sibling::tr'):
            author = row.xpath('./td[1]/b/text()')[0]
            date = datetime.fromtimestamp(int(row.xpath('./td[2]/i/time/@datetime')[0]))
            post =  "\n".join(i.text_content() for i in row.xpath('./td[2]/*[not(self::i)]')).strip()
            quotes = re.findall('\[QUOTE=(.+?)\](.+)\[/QUOTE\]', post, flags=re.S)
            yield {'author': author,'date': date, 'content': post, 'quotes':quotes}

    for post in scrape_page():
        yield post


if __name__ == '__main__':
    for i in scrape_thread('http://lupuscommunity.messageboardchat.com/post/7264293'):
        print i