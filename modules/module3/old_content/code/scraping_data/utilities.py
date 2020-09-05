import requests
from cStringIO import StringIO
import time

def fix_page(t, base):
    for br in t.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    for a in t.xpath('//a'):
        try:
            a.tail = ' ({}) '.format(a.attrib['href']) + a.tail if a.tail else ' ({}) '.format(a.attrib['href'])
        except:
            pass
    for img in t.xpath("*//img"):
        try:
            if img.attrib['alt'] and (base in img.attrib['src'] or not img.attrib['src'].startswith('http')):
                img.tail = " " + img.attrib['alt'] + img.tail
            else:
                img.tail = '\n( {} )\n'.format(img.attrib['src']) + img.tail
        except:
            pass
    return t


def get_page(url):
    resp = requests.get(url)
    retry, max = 0, 20
    while not ( resp.status_code == 200 or resp.status_code == 301 or resp.status_code == 303 ):
        print 'retrying', url
        time.sleep(10)
        resp = requests.get(url)
        retry += 1
        if retry > max:
            break
    return StringIO(resp.text.encode('UTF8'))