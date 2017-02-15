#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import gevent.monkey
gevent.monkey.patch_all()

from bottle import (route, run, template, static_file, request, response,
                    error, install, redirect)
from bottle.ext.sqlalchemy import Plugin
from math import ceil
from uuid import uuid4
from datetime import datetime

from sqlalchemy import (Table, Column, Integer, String, DateTime, ForeignKey,
                        Boolean, create_engine, desc, func, Sequence,
                        and_, or_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()
engine = create_engine("sqlite:///./blog.db")
plugin = Plugin(engine, Base.metadata, keyword="db", create=True)
install(plugin)

Session = sessionmaker(bind=engine)
session = Session()


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer(), Sequence("articles_id_seq"), primary_key=True)
    title = Column(String(1000), index=True)
    subtitle = Column(String(500), index=True)
    article = Column(String(), index=True)
    category_id = Column(Integer(), ForeignKey("category.id"), default=1)
    author_id = Column(Integer(), ForeignKey("authors.id"))
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)


    def __repr__(self):
        return "Article(title='{self.title}', " \
            "subitle='{self.subtitle}', " \
            "author_id='{self.author_id}', " \
            "category_id={self.category_id})".format(self=self)

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer(), Sequence("authors_id_seq"), primary_key=True)
    username = Column(String(15), nullable=False, unique=True)
    password = Column(String(25), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return "Author(username='{self.username}', " \
            "email='{self.email}')".format(self=self)

class Category(Base):
    __tablename__ = "category"

    id = Column(Integer(), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_on = Column(DateTime(), default=datetime.now)

    def __repr__(self):
        return "Category_id(name={self.id}, " \
            "name={self.name})".format(self=self)


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer(), Sequence('contact_id_seq'), primary_key=True)
    message = Column(String(500), nullable=False)
    email = Column(String(100), nullable=False)
    guest_ip = Column(String(255), nullable=True)
    seen = Column(Boolean(), default=False)
    created_on = Column(DateTime(), default=datetime.now)

    def __repr__(self):
        return "subject(user_id={self.subject}, " \
            "message={self.message})".format(self=self)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer(), Sequence('settings_id_seq'), primary_key=True)
    site_name = Column(String(300), default="Best blog ever.")
    site_subname = Column(String(300), default="Most amazing things is here.")
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)

#### Settings global variables ####
on_page_articles = 5


#### Functions ####

def select_articles(page=None):
    offset_num = on_page_articles
    if page:
        offset_num = on_page_articles * page

    article_count = session.query(func.count(Article.id)).first()

    off_num = article_count[0] - offset_num
    off_num = off_num if off_num >= 0 else 0

    articles = session.query(Article.id, Article.title, Article.subtitle,
                             Article.created_on, Author.username, Author.id)
    articles = articles.outerjoin(Author)
    # articles = articles.order_by(desc(Article.id))
    articles = articles.limit(on_page_articles)
    articles = articles.offset(off_num)
    articles = articles.all()

    pages = ceil(article_count[0] / on_page_articles)

    return articles[::-1], pages

def get_article(article_id):
    query = session.query(Article, Author.id, Author.username)
    query = query.outerjoin(Author)
    query = query.filter(Article.id == article_id)
    article = query.first()
    return article


@route("/")
@route("/<page:int>")
def index(page=None):
    page = page if page is not None else 1
    articles, pages = select_articles(page=page)
    return template("./views/index.html", articles=articles, max_pages=pages,
                    current_page=page)


@route("/post/<id:int>")
def post(id):
    article = get_article(id)
    return template("./views/post.html", article=article)


@route("/about")
def about():
    return template("./views/about.html")


@route("/contact")
def contact():
    return template("./views/contact.html")


@route("/contact", method="POST")
def contactme(db):
    name = request.forms.name
    email = request.forms.email
    message = request.forms.message
    ip = request.environ.get("REMOTE_ADDR")

    data = Contact(
        message=message,
        email=email,
        guest_ip=ip
    )
    db.add(data)
    db.commit()
    return {"status": "OK"}


#### Static files #####
@route("/images/<filename>")
def get_images(filename):
    """Callback for static files.

    returning static files from img folder.
    """
    return static_file(filename, root="./views/static/img")

@route("/css/<filename>")
def get_css(filename):
    """Callback for static files.

    return css files"""
    return static_file(filename, root="./views/static/css")


@route("/js/<filename>")
def get_js(filename):
    """Callback for static files.

    return scripts files"""
    return static_file(filename, root="./views/static/js")


@route("/fonts/<filename>")
def get_fonts(filename):
    """Callback for static files.

    return font files"""
    return static_file(filename, root="./views/static/fonts")


if __name__ == "__main__":
    run(host="localhost", port=8080, server="gevent", debug=True,
        reloader=True)
