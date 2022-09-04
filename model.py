from sqlalchemy import Column, String, Integer, ForeignKey, BLOB
from sqlalchemy.orm import relationship, backref

from database import Base


class Category(Base):
    __tablename__ = 'Category'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)


class Goods(Base):
    __tablename__ = 'Goods'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    image = Column(BLOB)
    category_id = Column(Integer, ForeignKey('Category.id'))
    category = relationship('Category', backref=backref('Goods', cascade="all, delete-orphan"), lazy='select')


class UserState(Base):
    __tablename__ = 'UserState'
    user_id = Column(Integer, primary_key=True, index=True)
    state = Column(Integer)
    category_id = Column(Integer, nullable=True)
