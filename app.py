#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import gevent.monkey
gevent.monkey.patch_all()

from bottle import (route, run, template, static_file, request, response,
                    error, install, redirect, BaseRequest)
from bottle.ext.sqlalchemy import Plugin
from math import ceil
from uuid import uuid4
from crypt import crypt
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
    header_image = Column(String(500))
    article = Column(String(), index=True)
    draft = Column(Boolean(), default=False)
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
    firstname = Column(String(15), nullable=False)
    lastname = Column(String(15), nullable=False)
    password = Column(String(25), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    session_id = Column(String(36))
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
    name = Column(String(100), nullable=False)
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
cookie_secret = "`m^2nkxJ>kU}>?NJWb(7'WF}(]p@?/f$2qVS))`"
cookie_age = 604800
BaseRequest.MEMFILE_MAX = 1024 * 1024
#### Functions ####

def check_session():

    session_id = request.get_cookie("sessid", secret=cookie_secret)
    if session_id:
        author = session.query(Author.id, Author.username)
        author = author.filter(Author.session_id == session_id).first()
        if author:
            return author.id, author.username
    return None


def select_articles(page=None, search=None, author=None):
    offset_num = on_page_articles
    if page:
        offset_num = on_page_articles * page

    article_count = session.query(func.count(Article.id))
    article_count = article_count.filter(Article.draft == False)

    articles = session.query(Article.id, Article.title, Article.subtitle,
                             Article.created_on, Author.username, Author.id)
    articles = articles.outerjoin(Author)
    if search:
        search = "%" + search + "%"
        articles = articles.filter(or_(Article.title.ilike(search),
                                       Article.article.ilike(search)))
        article_count = article_count.filter(or_(Article.title.ilike(search),
                                                 Article.article.ilike(search)))
    if author:
        articles = articles.filter(Article.author_id == author)
        article_count = article_count.filter(Article.author_id == author)

    article_count = article_count.first()
    off_num = article_count[0] - offset_num
    off_num = off_num if off_num >= 0 else 0
    articles = articles.order_by(Article.created_on)
    articles = articles.filter(Article.draft == False)
    articles = articles.limit(on_page_articles)
    articles = articles.offset(off_num)
    articles = articles.all()

    pages = ceil(article_count[0] / on_page_articles)

    return articles[::-1], pages

def admin_articles(author_id, draft, page=None):
    offset_num = on_page_articles
    if page:
        offset_num = on_page_articles * page

    article_count = session.query(func.count(Article.id))
    # article_count = article_count.filter(and_(Article.author_id == author_id,
    #                                           Article.draft == draft)).first()
    article_count = article_count.filter(Article.author_id == author_id)
    article_count = article_count.filter(Article.draft == draft).first()
    off_num = article_count[0] - offset_num
    off_num = off_num if off_num >= 0 else 0

    articles = session.query(Article.id, Article.title, Article.created_on)
    articles = articles.filter(Article.author_id == author_id)
    articles = articles.filter(Article.draft == draft)
    articles = articles.order_by(Article.created_on)
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
def index(page=1):
    # page = page if page is not None else 1
    # search = request.query.q if request.query.q else None
    search = request.query.q
    authors = request.query.author

    articles, pages = select_articles(page=page, search=search, author=authors)
    return template("./views/index.html", articles=articles, max_pages=pages,
                    current_page=page, search=search, page="index", au=authors)


@route("/post/<id:int>")
def post(id):
    article = get_article(id)
    return template("./views/post.html", article=article, page="post")


@route("/about")
def about():
    return template("./views/about.html", page="about")


@route("/contact")
def contact():
    return template("./views/contact.html", page="about")


@route("/contact", method="POST")
def contact_me(db):
    name = request.forms.name
    email = request.forms.email
    message = request.forms.message
    ip = request.environ.get("REMOTE_ADDR")

    data = Contact(
        name=name,
        message=message,
        email=email,
        guest_ip=ip
    )
    db.add(data)
    db.commit()
    return {"status": "OK"}


@route("/admin")
def admin(db):
    auth = check_session()
    if auth:
        count_posts = db.query(func.count(Article.id))
        count_posts = count_posts.filter(Article.draft == False).first()

        count_drafts = db.query(func.count(Article.id))
        count_drafts = count_drafts.filter(Article.draft == True).first()

        count_m = db.query(func.count(Contact.id))
        total_new_m = count_m.filter(Contact.seen == False).first()
        total_messages = count_m.first()

        latest_article = db.query(Article.title, Article.article,
                               Article.created_on)
        latest_post = latest_article.filter(Article.draft == False)
        latest_post = latest_post.order_by(Article.id.desc()).limit(1).first()

        latest_draft = latest_article.filter(Article.draft == True)
        latest_draft = latest_draft.order_by(Article.id.desc()).limit(1).first()

        message = db.query(Contact.email, Contact.message, Contact.created_on)
        newest_message = message.filter(Contact.seen == False)
        newest_message = newest_message.order_by(Contact.id.desc()).limit(1)
        newest_message = newest_message.first()

        newest_seen_message = message.filter(Contact.seen == True)
        newest_seen_message = newest_seen_message.order_by(Contact.id.desc())
        newest_seen_message = newest_seen_message.limit(1)
        newest_seen_message = newest_seen_message.first()


        return template("./views/admin/index.html", count_posts=count_posts[0],
                        count_drafts=count_drafts[0], total_new_m=total_new_m[0],
                        total_messages=total_messages[0],
                        latest_post=latest_post, latest_draft=latest_draft,
                        newest_message=newest_message,
                        newest_seen_message=newest_seen_message)
    else:
        redirect("/admin/login")


@route("/admin/editor")
def admin_new_post(db):
    auth = check_session()
    if auth:
        editor = request.query.mode
        mode = "new"
        article = None
        if editor == "edit":
            id = request.query.id
            mode = "edit"

            query = db.query(Article.id, Article.title, Article.subtitle,
                             Article.article, Article.header_image)
            query = query.filter(and_(Article.id == id,
                                      Article.author_id == auth[0]))
            article = query.first()
        return template("./views/admin/editor.html", mode=mode, article=article)
    else:
        redirect("/admin/login")

@route("/admin/editor", method="POST")
def editor_action(db):
    auth = check_session()
    if auth:
        title = request.forms.title
        subtitle = request.forms.subtitle
        img_url = request.forms.imgurl
        article = request.forms.article
        draft = int(request.forms.btnval)
        mode = request.query.m

        if mode == "new":
            new_post = Article(
                title=title,
                subtitle=subtitle,
                article=article,
                header_image=img_url,
                draft=draft,
                author_id=auth[0]
            )
            db.add(new_post)
        elif mode == "edit":
            id = request.forms.id
            if len(id) is 0:
                redirect("/admin/editor")

            post = db.query(Article).filter(and_(Article.id == id,
                                                    Article.author_id == auth[0]))
            post = post.first()
            if post.draft == True and post.draft != draft:
                post.created_on = datetime.now()
            post.title = title
            post.subtitle = subtitle
            post.header_image = img_url
            post.article = article
            post.draft = draft

        db.commit()
        redirect("/admin/view?mode=post")
    else:
        redirect("/admin/login")

@route("/admin/view")
@route("/admin/view/<page:int>")
def admin_view(page=1):
    auth = check_session()
    if auth:
        mode = request.query.mode
        if mode == "post":
            articles = admin_articles(auth[0], draft=False, page=page)
        elif mode == "draft":
            articles = admin_articles(auth[0], draft=True, page=page)
        else:
            redirect("/admin")

        return template("./views/admin/posts.html", articles=articles,
                        page=page, mode=mode)
    else:
        redirect("/admin/login")

@route("/admin/remove", method="POST")
def admin_remove(db):
    auth = check_session()
    if auth:
        id = request.forms.id
        if id:
            query = db.query(Article).filter(and_(Article.id == id,
                                                  Article.author_id == auth[0]))
            article = query.first()
            db.delete(article)
            db.commit()
            return {"status": "success"}
        else:
            return {"status": "fail"}
    else:
        return {"status": "you do not have rights!"}

@route("/admin/messages")
@route("/admin/messages/<page:int>")
def admin_messages(db, page=None):
    auth = check_session()
    if auth:
        show = request.query.show
        if show:
            message = db.query(Contact).filter(Contact.id == show).first()
            message.seen = True
            return template("./views/admin/message-show.html", message=message)
        else:
            page = page if page is not None else 1
            offset_num = 10
            if page:
                offset_num = 10 * page

            messages_count = db.query(func.count(Contact.id)).first()
            off_num = messages_count[0] - offset_num
            off_num = off_num if off_num >= 0 else 0

            messages = db.query(Contact.name, Contact.message, Contact.created_on, Contact.seen, Contact.id)
            messages = messages.limit(10)
            messages = messages.offset(off_num)
            messages = messages.all()

            pages = ceil(messages_count[0] / 10)

            return template("./views/admin/contact.html", messages=messages,
                            pages=pages, page=page)
    else:
        redirect("/admin/login")

@route("/admin/messages", method="POST")
def remove_message(db):
    auth = check_session()
    if auth:
        msgid = request.forms.msgid
        message = db.query(Contact).filter(Contact.id == msgid).first()
        db.delete(message)
        db.commit()
        return {"status": "OK"}
    else:
        redirect("/admin/login")


@route("/admin/settings")
def admin_settings(db):
    auth = check_session()
    if auth:
        mode = request.query.mode
        if mode == "user":
            author = db.query(Author).filter(Author.id == auth[0]).first()

            return template("./views/admin/usersettings.html", user=author)

        redirect("/admin")
    else:
        redirect("/admin/login")

@route("/admin/settings", method="POST")
def admin_settings_update(db):
    auth = check_session()
    if auth:
        mode = request.query.mode
        if mode == "user":
            firstname = request.forms.firstname
            lastname = request.forms.lastname
            username = request.forms.username
            email = request.forms.email
            newpassword = request.forms.newpassword
            oldpassword = request.forms.oldpassword

            if (not firstname and not lastname and not username and not email
                and not newpassword and not oldpassword):
                redirect("/admin")

            author = db.query(Author).filter(Author.id == auth[0]).first()

            if firstname:
                author.firstname = firstname
            if lastname:
                author.lastname = lastname
            if username:
                author.username = username
            if email:
                author.email = email
            if oldpassword:
                md_oldpassword = crypt(oldpassword, salt="MD5")
                if md_oldpassword == author.password:
                    if newpassword:
                        md_newpassword = crypt(newpassword, salt="MD5")
                        author.password = md_newpassword
                    else:
                        redirect("/admin")
                else:
                    redirect("/admin")
            db.commit()
            redirect("/admin/settings?mode=user")


@route("/admin/login")
def admin_login():
    auth = check_session()
    if auth is None:
        return template("./views/admin/login.html")
    else:
        redirect("/admin")


@route("/admin/login", method="POST")
def admin_do_login(db):
    username = request.forms.username
    password = crypt(request.forms.password, salt="MD5")
    if username == "" or password == "":
        return {"status": "FAIL"}

    check_user = db.query(Author).filter(and_(Author.username == username,
                                              Author.password == password))
    check_user = check_user.first()

    if check_user:
        session_id = str(uuid4())
        response.set_cookie("sessid", session_id, secret=cookie_secret,
                            max_age=cookie_age)

        check_user.session_id = session_id
        db.commit()
        return {"status": "OK"}
    else:
        return {"status": "FAIL"}

@route("/admin/logout")
def admin_logout(db):
    auth = check_session()
    if auth is not None:
        author = db.query(Author).filter(Author.id == auth[0])
        author = author.first()
        author.session_id = str(uuid4())
        db.commit()
        response.set_cookie("sessid", "", secret=cookie_secret)
        redirect("/")
    else:
        reirect("/")


#### Static files #####
@route("/images/<filename>")
def get_images(filename):
    """Callback for static files.

    returning static files from img folder.
    """
    response = static_file(filename, root="./views/static/img")
    response.set_header("Cache-Control", "public, max-age=25920000")
    return response

@route("/dummy/<filename:path>")
def get_css_js(filename):
    """Callback for static files.

    return css and js files"""
    response = static_file(filename, root="./views/static/dummy")
    response.set_header("Cache-Control", "public, max-age=25920000")
    return response

@route("/vendor/<filename:path>")
def get_vendor(filename):
    """Callback for static files.

    return vendor files"""
    response = static_file(filename, root="./views/static/vendor")
    response.set_header("Cache-Control", "public, max-age=25920000")
    return response

@route("/fonts/<filename>")
def get_fonts(filename):
    """Callback for static files.

    return font files"""
    response = static_file(filename, root="./views/static/fonts")
    response.set_header("Cache-Control", "public, max-age=25920000")
    return response


if __name__ == "__main__":
    run(host="localhost", port=8080, server="gevent", debug=True,
        reloader=True)
