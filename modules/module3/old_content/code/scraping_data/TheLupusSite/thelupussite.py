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


base='http://www.thelupussite.com/forum/'

def get_subforums():
    start = html.parse(base)
    subs = start.xpath('//ol[@class="nodeList"]//h3[@class="nodeTitle"]/a')
    descriptions = start.xpath('//blockquote/text()')
    for sub, description in zip(subs, descriptions):
        yield {'url': base+sub.xpath('./@href')[0],
               'name': sub.xpath('./text()')[0],
               'description': description}

def get_threads(sub):
    print '\n', sub, '\n'
    page=html.parse(sub)
    def scrape_page():
        # for thread in page.xpath('//h3[@class="title"]/a'):
        for thread in page.xpath('//div[@class="titleText"]'):
            modifiers=[]
            if thread.xpath('.//span[@class="sticky"]'):
                modifiers.append('sticky')
            if thread.xpath('.//span[@class="locked"]'):
                modifiers.append('locked')
            try:
                date = parse(thread.xpath('.//span[@class="DateTime"]/text()')[0])
            except:
                date = datetime.fromtimestamp(int(thread.xpath('.//abbr/@data-time')[0]))
            title = thread.xpath('.//h3[@class="title"]/a/text()')[0]
            url = base+thread.xpath('.//h3[@class="title"]/a/@href')[0]
            yield {'url': url,
                   'title': title,
                   'date': date,
                   'modifiers': modifiers}
    for th in scrape_page():
        yield th
    pagination = page.xpath('//div[@class="PageNav"]/@data-last')
    if pagination:
        for i in xrange(2, int(pagination[0])+1):
            url = sub+'page-'+str(i)
            print '\n', url, '\n'
            page = html.parse(url)
            for th in scrape_page():
                yield th

def scrape_thread(thread):
    print thread
    try:
        page = fix_page(html.parse(thread), base)
    except:
        yield None
    def scrape_page():
        for row in page.xpath('//li[@class="message   "]'):
            author = row.xpath('.//h3/a/text()')[0]
            role = row.xpath('.//em/text()')[0]
            try:
                date = parse(row.xpath('.//span[@class="DateTime"]/@title')[0])
            except:
                date = parse(row.xpath('.//abbr/text()')[0])
            post = row.xpath('.//article')[0].text_content().strip()
            quotes = []
            for q in row.xpath('.//div[@class="bbCodeBlock bbCodeQuote"]'):
                try:
                    author = q.attrib['data-author']
                except:
                    author = None
                quoted_text = q.xpath('./aside/blockquote')[0].text_content()[:-len('Click to expand...')]
                quotes.append({'quoted_text': quoted_text, "author": author,})
            yield {'author': author,'date': date, 'content': post, 'role': role,
                   'quotes': quotes}

    for post in scrape_page():
        yield post
    pagination = page.xpath('//div[@class="PageNav"]/@data-last')
    if pagination:
        for i in xrange(2, int(pagination[0])+1):
            try:
                page = fix_page(html.parse(thread+'page-'+str(i)), base)
            except:
                yield None
            for post in scrape_page():
                yield post

if __name__ == '__main__':
    # for i in get_subforums():
    #     print i
    # for i in get_threads('http://www.thelupussite.com/forum/index.php?forums/not-diagnosed-yet.12/'):
    #     print i
    for i in scrape_thread('http://www.thelupussite.com/forum/index.php?threads/still-searching.23128/'):
        print i['date']