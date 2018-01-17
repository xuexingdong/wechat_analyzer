from enum import Enum

from sqlalchemy import String, Column, Integer, BLOB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Friend(Base):
    __tablename__ = 'Friend'

    username = Column('userName', String, primary_key=True)
    type = Column(Integer)
    local = Column('dbContactLocal', BLOB)
    other = Column('dbContactOther', BLOB)
    remark = Column('dbContactRemark', BLOB)
    social = Column('dbContactSocial', BLOB)


class MsgType(Enum):
    TEXT = 1
    SYSTEM_MESSAGE = 10000
    VOICE = 34
    VIDEO1 = 43
    EMOTION = 47
    VIDEO2 = 62
    CALL = 50
    PICTURE = 3
    POSITION = 48
    CARD = 42
    LINK = 49

    UNHANDLED = -999
