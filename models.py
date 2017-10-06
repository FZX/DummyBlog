#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8


from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String,
                        DateTime, ForeignKey, Boolean, Sequence)

Base = declarative_base()


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

    def __repr__(self):
        return "Settings(site_name={self.site_name}, " \
            "site_subname={self.site_subname})".format(self=self)
