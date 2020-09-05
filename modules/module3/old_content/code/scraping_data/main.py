import sqlalchemy
import argparse
import sys
import itertools
import urllib
import datetime
from datetime import datetime
from sqlalchemy.sql import ClauseElement
from sqlalchemy import create_engine

import PatientInfo.patientinfo as pi
import Additude.add as add
import Netdoctor.netdoctor as netdoctor
import Sjogrens.sjogrens as sj
import CancerForums.cancerforums as cf
import HealthyPlace.healthyplace as hp
import HealingWell.healingwell as  hw
import WhatToExpect.whattoexpect as  what
import LupusCommunity.lupuscommunity as lupus
import TheLupusSite.thelupussite as lupussite
import Fertility.fertility as fertility
import ThisIsMS.thisisms as ms
import eHealthForum.ehealthforum as ehealth
import OurHealth.ourhealth as ourhealth
import HealthBoards.healthboards as healthboards
import Addforums.addforums as addforums
import settings as s
from models import *

print('running sqlalchemy ' + sqlalchemy.__version__)

def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True

def fix_date(date):
    return datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')

def parse_args(args):
    parser = argparse.ArgumentParser(
        description='Manage your scrapers from command line',)
    # parser.add_argument('--letters', dest='letters',  nargs='*', help="which groups starting with a given letter would you like to scrape? (valid only for patientinfo)", choices=string.lowercase)
    parser.add_argument('--scrape', dest='scrape',  type=str, choices=[
                                                                        'add',
                                                                        'patientinfo',
                                                                        'netdoctor',
                                                                        'sjogrensworld',
                                                                        'cancerforums',
                                                                        'healthyplace',
                                                                        'healingwell',
                                                                        'whattoexpect',
                                                                        'lupuscommunity',
                                                                        'thelupussite',
                                                                        'fertility',
                                                                        'thisisms',
                                                                        'ehealth',
                                                                        'ourhealth',
                                                                        'healthboards',
                                                                        'addforums',
                                                                        ],
                               help="Choose which forum to scrape:\n"
                                    "add=additudemag.com "
                                    "netdoctor=forums.netdoctor.co.uk"
                                    "patientinfo=patient.info"
                                    "sjogrensworld=sjogrensworld.org"
                                    "cancerforums=cancerforums.net"
                                    "healthyplace=healthyplace.com"
                                    "healingwell=healingwell.com"
                                    "whattoexpect=whattoexpect.com"
                                    "thelupussite=thelupussite.com"
                                    "fertility=fertility.org"
                                    "thisisms=thisisms.com"
                                    "ehealth=ehealthforum.com"
                                    "ourhealth=ourhealth.com"
                                    "healthboards=healthboards.com"
                                    "addforums=addforums.com"
                        )

    return parser.parse_args(args)

def scrape_patientinfo():
    f = get_or_create(session, Forum, name="patient.info")
    session.commit()
    categories_scraped = []
    for cat in pi.get_categories():
        if cat not in categories_scraped:
            sub = Forum(name=cat[0], description=cat[1], parent=f[0])
            session.add(sub)
            session.flush()
            categories_scraped.append(cat)
            for thread in pi.get_threads(cat[0]):
                th_data = thread.next()
                user = get_or_create(session, User, username=th_data[1], role=th_data[4], forum=f[0])
                session.flush()
                th = Thread(url=th_data[6], forum=sub, last_update=datetime.now(), title=th_data[0], author_id=user[0].id,
                            date=datetime.strptime(th_data[2][:-6], '%Y-%m-%dT%H:%M'), likes=th_data[5])
                session.add(th)
                session.flush()
                first_post = Post(thread=th.id, post_text=th_data[3],
                           author=user[0].id,
                           date=datetime.strptime(th_data[2][:-6], '%Y-%m-%dT%H:%M'),
                           likes=th_data[5], sequence=0)
                session.add(first_post)
                session.flush()
                ids = {0: first_post.id}
                sequence = 0
                for post in thread:
                    author = get_or_create(session, User, username=post['user'], role=post['role'], forum=f[0])[0]
                    session.flush()
                    replyto_id = ids[post['reply_to']] if post['reply_to'] is not None else None
                    p=Post(thread=th.id, post_text=post['post'],
                           author=author.id,
                           date=datetime.strptime(post['date'][:-6], '%Y-%m-%dT%H:%M'),
                           likes=post['vote'], replyto_id=replyto_id, sequence=sequence+1)
                    session.add(p)
                    session.flush()
                    ids[sequence+1] = p.id
                    sequence += 1
                session.commit()
            session.commit()

def scrape_netdoctor():
    forum = get_or_create(session, Forum, name="forums.netdoctor.co.uk")
    session.flush()
    data = netdoctor.get_threads()
    for th in data:
        subforum = get_or_create(session, Forum, name=th['subforum'], parent=forum[0])
        session.flush()
        # first_post = th['posts'].next()
        first_post = th['posts'][0]
        author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
        session.flush()
        thread = Thread(date=fix_date(first_post['date']), title=th['title'], last_update=datetime.now(), author=author[0],
                                    views=th['views'], likes=th['points'], forum=subforum[0], url=th['url']
                                )
        session.add(thread)
        session.flush()
        p=Post(post_text=first_post['post'], author=author[0].id, thread=thread.id, sequence=0,
             date=fix_date(first_post['date']))
        session.add(p)
        session.flush()
        sequence = 1
        for post in th['posts'][1:]:
            author = get_or_create(session, User, username=post['author'], forum=forum[0])
            session.flush()
            last_post = session.add(Post(post_text=post['post'], author=author[0].id, thread=thread.id,
                                         date=fix_date(post['date']), replyto=p, sequence=sequence))
            session.flush()
            sequence+=1
        session.commit()

def scrape_additude():
    forum = get_or_create(session, Forum, name="connect.additudemag.com")
    session.flush()
    for th in add.get_threads():
        subforum = get_or_create(session, Forum, name=th['thread']['subforum'], parent=forum[0])
        session.flush()
        author = get_or_create(session, User, username=th['posts'][0]['author'], forum=forum[0])
        session.flush()
        thread=Thread(date=th['thread']['date'], title=th['thread']['title'], last_update=datetime.now(),
                      author=author[0], forum=subforum[0], url=th['thread']['url']
                  )
        session.add(thread)
        session.flush()
        sequence = 0
        reply_to = None
        for post in th['posts']:
            author = get_or_create(session, User, username=post['author'], forum=forum[0])
            session.flush()
            reply_to = Post(post_text=post['post'], author=author[0].id, thread=thread.id,
                                         date=post['date'], replyto=reply_to, sequence=sequence)
            session.add(reply_to)
            sequence += 1
            session.flush()
        session.commit()

def scrape_sjogrensworld():
    forum = get_or_create(session, Forum, name="sjogrensworld.org")
    session.flush()
    for sub in sj.get_subforums():
        subforum = get_or_create(session, Forum, name=sub[0], description=sub[1],
                      parent=forum[0])
        session.flush()
        for th in sj.get_threads(sub[0]):
            first_post = th['posts'].next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0], modifier=" ".join(th['modifiers']),
                            views=th['views'], forum=subforum[0], url=th['url']
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['post_text'], author=author[0].id,
                     thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            sequence=0
            for post in th['posts']:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['post_text'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p)
                session.add(p)
                session.flush()
                for q_sequence, quote in enumerate(post['quotes']):
                    if quote['date']:
                        quoted_post = session.query(Post).join(User)\
                            .filter(Post.date==quote['date'])\
                            .filter_by(username=quote['author']).first()
                        if quoted_post:
                            session.add(Quotes(quoting_post=p.id, sequence=q_sequence, nested=quote['nested'],
                                               quoted_text=quote['quoted_text'], quoted_post=quoted_post.id,
                                               quoted_author=quoted_post.author
                                               ))
                        else:
                            session.add(Quotes(quoting_post=p.id, sequence=q_sequence, nested=quote['nested'],
                                               quoted_text=quote['quoted_text']
                                               ))
                    else:
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence, nested=quote['nested'],
                                           quoted_text=quote['quoted_text']
                                          ))
                    session.flush()

            session.commit()

def scrape_cancerforums():
    forum = get_or_create(session, Forum, name="cancerfoums.net")
    session.flush()
    for sub in cf.get_subforums():
        # print sub
        subforum = get_or_create(session, Forum, name=sub['name'], description=sub['description'],
                                 url=sub['url'], parent=forum[0])
        session.flush()
        for th in cf.get_threads(sub['url']):
            author = get_or_create(session, User, username=th['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=th['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0], modifier=" ".join(th['modifiers']),
                            views=th['views'], forum=subforum[0], url=th['url']
                            )
            session.add(thread)
            session.flush()
            sequence=0
            for post in cf.scrape_thread(th['url']):
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p if sequence else None)
                session.add(p)
                session.flush()
                sequence += 1
                # for q_sequence, quote in enumerate(post['quotes']):
                #
                #     try:
                #         quoted_author = session.query(User).filter_by(username=quote[0], forum=forum[0]).first()
                #         session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                #                                    quoted_text=quote[1]
                #                                    ))
                #     except:
                #         session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                #                        quoted_text=quote[1]
                #                        ))
                #     session.flush()

            session.commit()

def scrape_healthyplace():
    forum = get_or_create(session, Forum, name="healthyplace.com")
    session.flush()


    def deal_with_subforum(sub, parent):
        subforum = get_or_create(session, Forum, name=sub['name'],
                                 url=sub['url'], parent=parent[0], description=sub['description'])
        session.flush()
        for th in hp.get_threads(sub['url']):
            posts = hp.scrape_thread(th['url'])
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0],
                            views=th['views'], forum=subforum[0], url=th['url']
                            )

            session.add(thread)
            session.flush()
            sequence = 0
            for post in hp.scrape_thread(th['url']):
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p if sequence else None)
                session.add(p)
                session.flush()
                sequence += 1
                for q_sequence, quote in enumerate(post['quotes']):

                    try:
                        quoted_author = session.query(User).filter_by(username=quote['author'], forum=forum[0]).first()
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                                           quoted_text=quote['text']
                                           ))
                    except:
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote['text']
                                           ))
                    session.flush()
            session.commit()

        return subforum



    for sub in hp.get_subforums():
        parent_sub = deal_with_subforum(sub, forum)

        for subsub in sub['subforums']:
            deal_with_subforum(subsub, parent_sub)

def scrape_healingwell():
    forum = get_or_create(session, Forum, name="healingwell.com", url='http://www.healingwell.com/community/default.aspx')
    session.flush()
    for sub in hw.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=forum[0])
        session.flush()
        for th in hw.get_threads(sub['url']):
            posts = hw.scrape_thread(th['url'])
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            if sub['name'] == 'Announcements':
                th['type'].append('announcement')
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0], modifier=" ".join(th['modifiers']), type=" ".join(th['type']),
                            forum=subforum[0], url=th['url']
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['content'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            sequence = 0
            for post in posts:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p)
                session.add(p)
                session.flush()
            session.commit()

def scrape_whattoexpect():
    forum = get_or_create(session, Forum, name="whattoexpect.com", url='http://www.healingwell.com/community/default.aspx')
    session.flush()
    for sub in what.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=forum[0])
        session.flush()
        for th in what.get_threads(sub['url']):
            posts = th['posts']
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0],
                            forum=subforum[0], url=th['url'], archived=th['archived'],
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['content'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            sequence = 0
            for post in posts:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'])
                session.add(p)
                session.flush()
            session.commit()

def scrape_lupuscommunity():
    forum = get_or_create(session, Forum, name="lupuscommunity.messageboardchat.com", url=lupus.base)
    session.flush()
    for sub in lupus.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=forum[0])
        session.flush()
        for th in lupus.get_threads(sub['url']):
            posts = lupus.scrape_thread(th['url'])
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0],
                            forum=subforum[0], url=th['url'],
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['content'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            sequence = 0
            for post in posts:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p)
                session.add(p)
                session.flush()
                for q_sequence, quote in enumerate(post['quotes']):

                    try:
                        quoted_author = session.query(User).filter_by(username=quote[0], forum=forum[0]).first()
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                                           quoted_text=quote[1]
                                           ))
                    except:
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote[1]
                                           ))
                    session.flush()
            session.commit()

def scrape_lupussite():
    forum = get_or_create(session, Forum, name="thelupussite.com")
    session.flush()
    for sub in lupussite.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=forum[0])
        session.flush()
        for th in lupussite.get_threads(sub['url']):
            posts = lupussite.scrape_thread(th['url'])
            try:
                first_post = posts.next()
            except:
                continue
            if first_post:
                author = get_or_create(session, User, username=first_post['author'], forum=forum[0],
                                       role=first_post['role'])
                session.flush()
                thread = Thread(date=th['date'], title=th['title'], last_update=datetime.now(),
                                author=author[0], modifier=" ".join(th['modifiers']),
                                forum=subforum[0], url=th['url']
                                )
                session.add(thread)
                session.flush()
                p = Post(post_text=first_post['content'], author=author[0].id,
                         thread=thread.id, sequence=0,
                         date=first_post['date'])
                session.add(p)
                session.flush()
                sequence = 0
                for post in posts:
                    sequence += 1
                    author = get_or_create(session, User, username=post['author'], forum=forum[0], role=post['role'])
                    session.flush()
                    p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                             date=post['date'], replyto=p)
                    session.add(p)
                    session.flush()
                    for q_sequence, quote in enumerate(post['quotes']):
                        if quote['author']:
                            quoted_author = session.query(User).filter(User.username==quote['author'], User.forum==forum[0]).first()
                        else:
                            quoted_author = None
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote['quoted_text'],
                                           quoted_author=quoted_author.id if quoted_author else None
                                           ))
                        session.flush()
                session.commit()

def scrape_fertility():
    forum = get_or_create(session, Forum, name="fertility.org")
    session.flush()

    def deal_with_subforum(sub, parent):
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=parent)

        session.flush()
        for th in fertility.get_threads(sub['url']):
            posts = fertility.scrape_thread(th['url'])
            try:
                first_post = posts.next()
            except:
                continue
            if first_post:
                author = get_or_create(session, User, username=first_post['author'], forum=forum[0],
                                       role=first_post['role'])
                session.flush()
                thread = Thread(date=th['date'], title=th['title'], last_update=datetime.now(),
                                author=author[0], modifier=" ".join(th['modifiers']),
                                forum=subforum[0], url=th['url'], views=th['views']
                                )
                session.add(thread)
                session.flush()
                p = Post(post_text=first_post['content'], author=author[0].id,
                         thread=thread.id, sequence=0,
                         date=first_post['date'])
                session.add(p)
                session.flush()
                sequence = 0
                for post in posts:
                    sequence += 1
                    author = get_or_create(session, User, username=post['author'], forum=forum[0], role=post['role'])
                    session.flush()
                    p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                             date=post['date'], replyto=p)
                    session.add(p)
                    session.flush()
                    for q_sequence, quote in enumerate(post['quotes']):
                        if quote['author']:
                            quoted_author = session.query(User).filter(User.username == quote['author'],
                                                                       User.forum == forum[0]).first()
                        else:
                            quoted_author = None
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote['quoted_text'],
                                           quoted_author=quoted_author.id if quoted_author else None
                                           ))
                        session.flush()
                session.commit()
        if parent == forum[0]:
            for sub in fertility.get_subforums(sub['url']):
                deal_with_subforum(sub, subforum[0])

    for sub in fertility.get_subforums(fertility.base):
        deal_with_subforum(sub, forum[0])

def scrape_thisisms():
    forum = get_or_create(session, Forum, name="thisisms.com", url='http://www.thisisms.com/forum/')
    session.flush()
    for sub in ms.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'], description=sub['description'],
                                 parent=forum[0])
        session.flush()
        for th in ms.get_threads(sub['url']):
            posts = ms.scrape_thread(th['url'])
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0], role=first_post['role'])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0], views=th['views'],
                            forum=subforum[0], url=th['url'],
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['content'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'], signature=first_post['signature'])
            session.add(p)
            session.flush()
            sequence = 0
            for post in posts:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0], role=post['role'])
                session.flush()
                p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p)
                session.add(p)
                session.flush()
                for q_sequence, quote in enumerate(post['quotes']):

                    try:
                        quoted_author = session.query(User).filter_by(username=quote['author'], forum=forum[0]).first()
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                                           quoted_text=quote['quoted_text'], nested=quote['nested']
                                           ))
                    except:
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote['quoted_text'], nested=quote['nested']
                                           ))
                    session.flush()
            session.commit()

def scrape_ehealth():
    forum = get_or_create(session, Forum, name="ehealthforum.com", url='http://ehealthforum.com/health/health_forums.html')
    session.flush()
    for sub in ehealth.get_subforums():
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'],
                                 parent=forum[0])
        session.flush()
        for th in ehealth.get_threads(sub['url']):
            posts = ehealth.scrape_thread(th['url'])
            lasts = {}
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0], role=first_post['role'])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0], views=th['views'],
                            forum=subforum[0], url=th['url'],
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['content'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            first = p.id
            sequence = 0
            for post in posts:
                if post:
                    sequence += 1
                    author = get_or_create(session, User, username=post['author'], forum=forum[0], role=post['role'])
                    session.flush()
                    if post['indent'] is None:
                        replyto = first
                        lasts = {}
                    else:
                        if post['indent'] >= max(lasts):
                            replyto = lasts[max(lasts)]
                        else:
                            for k in sorted(lasts.keys(), reverse=True):
                                if k >= post['indent']:
                                    del lasts[k]
                                else:
                                    replyto = lasts[k]
                                    break
                    p = Post(post_text=post['content'], author=author[0].id, thread=thread.id, sequence=sequence,
                             date=post['date'], post_subject=post['subject'], replyto_id=replyto)
                    session.add(p)
                    session.flush()
                    lasts[post['indent']] = p.id

                    for q_sequence, quote in enumerate(post['quotes']):

                        try:
                            quoted_author = session.query(User).filter_by(username=quote['author'], forum=forum[0]).first()
                            session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                                               quoted_text=quote['quoted_text']
                                               ))
                        except:
                            session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                               quoted_text=quote['quoted_text']
                                               ))
                        session.flush()
            session.commit()

def scrape_ourhealth():
    forum = get_or_create(session, Forum, name="ourhealth.com", url='http://www.ourhealth.com/')
    session.flush()
    for sub in ourhealth.get_subforums():
        subforum = get_or_create(session, Forum, url=ourhealth.base+sub, name=sub,
                                 parent=forum[0])
        session.flush()
        for th in ourhealth.get_threads(sub):
            author = get_or_create(session, User, username=th['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=th['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0],
                            forum=subforum[0], url=th['url'],
                            )
            session.add(thread)
            sequence = 0
            p = None
            for post in ourhealth.scrape_thread(th['url']):
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['text'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p, likes=post['likes'],
                         dislikes=post['dislikes'])
                session.add(p)
                session.flush()
            session.commit()

def scrape_healthboards():
    forum = get_or_create(session, Forum, name="healthboards.com", url='http://www.healthboards.com/boards')
    session.flush()
    for sub in healthboards.get_subforums_from_sitemap():
        if sub['parent']:
            parent = session.query(Forum).filter(Forum.parent == forum[0],
                                                 Forum.name == sub['parent']).first()
        else:
            parent = forum[0]
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'],
                                 parent_id=parent.id)
        session.flush()
        for th in healthboards.get_threads(sub['url']):
            posts = healthboards.scrape_thread(th['url'])
            first_post = posts.next()
            author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
            session.flush()
            thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                            author=author[0],
                            forum=subforum[0], url=th['url'],
                            )
            session.add(thread)
            session.flush()
            p = Post(post_text=first_post['text'], author=author[0].id, thread=thread.id, sequence=0,
                     date=first_post['date'])
            session.add(p)
            session.flush()
            sequence = 0
            for post in posts:
                sequence += 1
                author = get_or_create(session, User, username=post['author'], forum=forum[0])
                session.flush()
                p = Post(post_text=post['text'], author=author[0].id, thread=thread.id, sequence=sequence,
                         date=post['date'], replyto=p)
                session.add(p)
                session.flush()
                for q_sequence, quote in enumerate(post['quotes']):
                    try:
                        quoted_author = session.query(User).filter_by(username=quote[0].split(';')[0], forum=forum[0]).first()
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence, quoted_author=quoted_author.id,
                                           quoted_text=quote[1]
                                           ))
                    except:
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                           quoted_text=quote[1]
                                           ))
                    session.flush()
            session.commit()

def scrape_addforums():
    forum = get_or_create(session, Forum, name="addforums.com", url='http://www.addforums.com/forums/')
    session.flush()
    for sub in addforums.get_subforums():
        if sub['parent']:
            parent = session.query(Forum).filter(Forum.parent == forum[0],
                                                 Forum.name == sub['parent']).first()
            if not parent:
                parent = session.query(Forum).filter(Forum.name == sub['parent']).first()
        else:
            parent = forum[0]
        subforum = get_or_create(session, Forum, url=sub['url'], name=sub['name'],
                                 parent_id=parent.id)
        session.flush()
        threads = addforums.get_threads(sub['url'])
        if threads:
            for th in threads:
                posts = addforums.scrape_thread(th['url'])
                try:
                    first_post = posts.next()
                except:
                    continue
                author = get_or_create(session, User, username=first_post['author'], forum=forum[0])
                session.flush()
                thread = Thread(date=first_post['date'], title=th['title'], last_update=datetime.now(),
                                author=author[0],
                                forum=subforum[0], url=th['url'],
                                )
                session.add(thread)
                session.flush()
                p = Post(post_text=first_post['text'], author=author[0].id, thread=thread.id, sequence=0,
                         date=first_post['date'])
                session.add(p)
                session.flush()
                sequence = 0
                for post in posts:
                    sequence += 1
                    author = get_or_create(session, User, username=post['author'], forum=forum[0])
                    session.flush()
                    p = Post(post_text=post['text'], author=author[0].id, thread=thread.id, sequence=sequence,
                             date=post['date'], replyto=p)
                    session.add(p)
                    session.flush()
                    for q_sequence, quote in enumerate(post['quotes']):
                        session.add(Quotes(quoting_post=p.id, sequence=q_sequence,
                                               quoted_text=quote
                                               ))
                        session.flush()
                session.commit()
    session.close()
    return None


if __name__ == '__main__':

    print('running sqlalchemy ' + sqlalchemy.__version__)
    if s.DATABASE == 'postgres':
        engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(
            urllib.quote(s.DBUSER), urllib.quote(s.DBPASS), s.DBHOST, s.DBPORT, s.DBNAME))
    elif s.DATABASE == 'mysql':
        engine = create_engine('mysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
            urllib.quote(s.DBUSER), urllib.quote(s.DBPASS), s.DBHOST, s.DBPORT, s.DBNAME), pool_recycle=3600)
        print 'connected to mysql database'
    else:
        engine = create_engine(r'sqlite:///health.db', echo=True)
        print('database created: health.db')
    Base.metadata.create_all(engine)

    args = parse_args(sys.argv[1:])
    Session = sessionmaker(bind=engine)
    session = Session()
    if args.scrape == 'patientinfo':
        scrape_patientinfo()
    if args.scrape == 'netdoctor':
        scrape_netdoctor()
    if args.scrape == 'add':
        scrape_additude()
    if args.scrape == 'sjogrensworld':
        scrape_sjogrensworld()
    if args.scrape == 'cancerforums':
        scrape_cancerforums()
    if args.scrape == 'healthyplace':
        scrape_healthyplace()
    if args.scrape == 'healingwell':
        scrape_healingwell()
    if args.scrape == 'whattoexpect':
        scrape_whattoexpect()
    if args.scrape == 'lupuscommunity':
        scrape_lupuscommunity()
    if args.scrape == 'thelupussite':
        scrape_lupussite()
    if args.scrape == 'fertility':
        scrape_fertility()
    if args.scrape == 'thisisms':
        scrape_thisisms()
    if args.scrape == 'ehealth':
        scrape_ehealth()
    if args.scrape == 'ourhealth':
        scrape_ourhealth()
    if args.scrape == 'healthboards':
        scrape_healthboards()
    if args.scrape == 'addforums':
        scrape_addforums()
