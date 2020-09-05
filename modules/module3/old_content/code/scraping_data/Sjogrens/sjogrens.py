# -*- coding: utf-8 -*-
from lxml import html
from retrying import retry
from datetime import datetime
import re
import sys
reload(sys)
sys.setdefaultencoding('UTF8')


@retry(wait_random_min=5000, wait_random_max=10000)
def scrape_thread(thread):
    t = html.parse(thread+"&action=printpage;")
    for br in t.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    posts = zip(t.xpath('//dt[@class="postheader"]'), t.xpath('//dd[@class="postbody"]'))
    for post in posts:
        poster = post[0].xpath('./strong[2]/text()')[0]
        date = datetime.strptime(post[0].xpath('./strong[3]/text()')[0], "%B %d, %Y, %H:%M:%S %p")
        content = post[1].text_content().strip()
        quotes = []
        for q in post[1].xpath('./blockquote'):
            meta = q.xpath('./preceding-sibling::div')[0].text_content()
            author = " ".join(meta.split()[2:-6])
            try:
                date = datetime.strptime(" ".join(meta.split()[-5:]), "%B %d, %Y, %H:%M:%S %p")
            except:
                date = None
            quotes.append({'quoted_text': q.text_content(), 'nested': True if q.xpath('./blockquote') else False,
                           "author": author, "date": date})
        yield {'author': poster, 'date': date, 'post_text': content,  'quotes': quotes}

def get_threads(subforum):
    forum_page = html.parse(subforum)
    while True:
        for thread, views, modclass in zip(forum_page.xpath('//td[contains(@class, "subject")]//span/a'),
                                 forum_page.xpath('//tr/td[4]'), forum_page.xpath('//tr/td[4]/@class')):
            print thread.attrib['href']
            modclass = modclass[0].split()
            modifiers = []
            if 'stickybg' in modclass:
                modifiers.append('sticky')
            if 'lockedbg' in modclass:
                modifiers.append('locked')
            if 'locked_sticky' in modclass:
                modifiers.append('sticky')
                modifiers.append('locked')
            if thread.text.startswith('MOVED: '):
                modifiers.append('moved')
            yield {'url': thread.attrib['href'], 'title': thread.text, 'views': int(views.text_content().split()[-2]),\
                  'posts': scrape_thread(thread.attrib['href']),
                   'modifiers': modifiers}
        next_page = forum_page.xpath('//div[@class="pagelinks"]/strong/following-sibling::a[1]')
        if next_page:
            forum_page = html.parse(next_page[0].attrib['href'])
        else:
            break

def get_subforums():
    page = html.parse("http://sjogrensworld.org/forums/index.php")
    for forum in page.xpath('//td[@class="info"]/a'):
        yield forum.attrib['href'], forum.xpath('../p/text()')[0]
