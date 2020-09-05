from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, DateTime, String, Text, Float, ForeignKey, Boolean
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()
Base.__table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}


'''
TABLE DESCRIPTIONS:
###################
Forum: Tracks the name of the forum, allowing for nested forums
- id
- name - All forums should be named
- description - Forums may optionally have descriptions
- parent - Some forums may be nested

Thread: All forums discussions are organized into threads. Normally, the thread inherits the title, author, date of the top post
- id
- date - date and time when the thread was started
- title - usually the subject of the first post
- author - fk to user table (normally same as first post)
- type - optional, but some threads are "announcements"
- modifier - optional, but some threads are "sticky" or possibly "moved"
- forum - fk to forum table
- last_update - when this record (in the table) was last updated
- views - some platforms record the number of views
- archived - some threads have been archived and are moved to the forum archives
- likes - some platforms record likes from other users. If available, a simple count is all that is required.

Post: All messages are posts
- id
- thread - fk to the thread table
- post_text - the text of this post. Any quoted text should not be included here; instead, quotes should be replaced with the text [QUOTE_N] where N is the zero relative index of the quote in the text
- author - fk to the author table
- date - date and time of post
- likes - if available, the number of likes (or "favorites") this post has received
- dislikes - some forums have dislikes
- reply_to - some platforms afford "replies" - this is different than a quote, and will be available somewhere in the HTML (e.g. BBEdit provides "threadview" which captures this information)
- post_subject - usually the same as the subject of the thread
- sequence - the zero-relative index of the post as it appears on the page.


Quotes: Some platforms afford quoting; in somecases, the id of the quoted post is available. In other cases only the quoted user is available.
- id
- quoting_post - fk to the post table. must never be null
- quoted_post - fk to the post table. may or may not be available
- quoted_author - fk to the user table. always available, but may require a lookup in the user table
- quoted_text - text of the quote, extracted from the text
- sequence - sequence in the post if multiple quotes are included.
- nested - if quote contains other quotes


User: This table should simply organize information about all unique users
- id
- username - the user's handle (please increase column width if you need more characters)
- role - some sites will indicate if a user has a special role on the site (e.g. moderator, expert, staff, etc.). Keep track of that here.
'''


class Forum(Base):
    __tablename__ = "Forum"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(256), default=" ")
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('Forum.id'))
    parent = relationship('Forum', remote_side=[id])
    url = Column(Text) # ALTER TABLE "Forum" ADD COLUMN url TEXT;


class Post(Base):
    __tablename__ = "Post"
    id = Column(Integer, primary_key=True, unique=True)
    thread = Column(Integer, ForeignKey('Thread.id'))
    # thread = relationship('Thread', remote_side=[id])
    post_text = Column(Text)
    # author_id = relationship('User', remote_side=[id])
    author = Column(Integer, ForeignKey('User.id'))
    date = Column(DateTime)
    likes = Column(Integer)
    dislikes = Column(Integer) # ALTER TABLE "Post" ADD COLUMN dislikes INTEGER;
    replyto_id = Column(Integer, ForeignKey('Post.id'))
    replyto = relationship('Post', remote_side=[id])
    post_subject = Column(Text)
    sequence = Column(Integer)
    signature = Column(Text) # ALTER TABLE "Post" ADD COLUMN signature TEXT;


class Quotes(Base):
    __tablename__ = "Quotes"
    id = Column(Integer, primary_key=True, unique=True)
    quoting_post = Column(Integer)
    quoted_author = Column(Integer, ForeignKey('User.id'))
    quoting_post = Column(Integer, ForeignKey('Post.id'))
    quoted_post = Column(Integer, ForeignKey('Post.id'))
    quoted_text = Column(Text)
    sequence = Column(Integer)
    nested = Column(Boolean)



class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True, unique=True)
    username = Column(Text)
    role = Column(Text)
    forum_id = Column(Integer, ForeignKey('Forum.id'))
    forum = relationship('Forum', remote_side="Forum.id")
    # __table_args__ = (UniqueConstraint('forum_id', 'username_'),)


class Thread(Base):
    __tablename__ = "Thread"
    id = Column(Integer, primary_key=True, unique=True)
    date = Column(DateTime)
    title = Column(Text)
    author_id = Column(Integer, ForeignKey('User.id'))
    author = relationship('User', foreign_keys="Thread.author_id", remote_side="User.id")
    type = Column(Text, default="normal")
    archived = Column(Boolean, default=False) # ALTER TABLE "Thread" ADD COLUMN archived BOOLEAN;
    modifier = Column(Text, default="normal")
    forum_id = Column(Integer, ForeignKey('Forum.id'))
    forum = relationship('Forum', remote_side="Forum.id")
    last_update = Column(DateTime)
    views = Column(Integer)
    likes = Column(Integer)
    url = Column(Text)
