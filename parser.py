import hashlib
import logging
from enum import IntEnum, unique

import arrow
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Friend

logger = logging.getLogger(__name__)


@unique
class RemarkPos(IntEnum):
    # 微信昵称
    NICKNAME = 10
    # 微信号
    WECHAT_ID = 18
    # 备注
    REMARK = 26
    # 备注的全拼
    REMARK_FULL_PINYIN = 34
    # 备注全拼的首字母缩写
    REMARK_FIRST_LETTER = 42
    # 昵称全拼
    NICKNAME_FULL_PINYIN = 50
    # 未知
    UNKNOWN = 58


class FriendInfo:
    def __init__(self):
        self.username = ''
        self.remark_info = RemarkInfo()


class TypeInfo:
    pass


class RemarkInfo:
    def __init__(self):
        self.nickname = ''
        self.wechat_id = ''
        self.remark = ''
        self.remark_full_pinyin = ''
        self.remark_first_letter = ''
        self.nickname_full_pinyin = ''

        # @property
        # def nickname(self):
        #     return self._nickname
        #
        # @nickname.setter
        # def nickname(self, value):
        #     self._nickname = value
        #
        # @property
        # def wechat_id(self):
        #     return self._nickname
        #
        # @wechat_id.setter
        # def wechat_id(self, value):
        #     self._wechat_id = value
        #
        # @property
        # def remark(self):
        #     return self._remark
        #
        # @remark.setter
        # def remark(self, value):
        #     self._remark = value
        #
        # @property
        # def remark_full_pinyin(self):
        #     return self._remark_full_pinyin
        #
        # @remark_full_pinyin.setter
        # def remark_full_pinyin(self, value):
        #     self._remark_full_pinyin = value
        #
        # @property
        # def remark_first_letter(self):
        #     return self._remark_first_letter
        #
        # @remark_first_letter.setter
        # def remark_first_letter(self, value):
        #     self._remark_first_letter = value
        #
        # @property
        # def nickname_full_pinyin(self):
        #     return self._nickname_full_pinyin
        #
        # @nickname_full_pinyin.setter
        # def nickname_full_pinyin(self, value):
        #     self._nickname_full_pinyin = value


class WechatParser:
    def __init__(self, contact_sqlite, mm_sqlite):
        self.contact_sqlite = contact_sqlite
        self.mm_sqlite = mm_sqlite
        engine1 = create_engine('sqlite:///' + contact_sqlite)
        self.FriendSession = sessionmaker(bind=engine1)

        engine2 = create_engine('sqlite:///' + mm_sqlite)
        self.MMSession = sessionmaker(bind=engine2)

    def analyse(self):
        self._parse_friends()

    def find_friend(self, wechat_id) -> FriendInfo:
        return self.friends.get(wechat_id, None)

    def find_chats(self, wechat_id):
        chats = []
        friend = self.find_friend(wechat_id)
        mm_session = self.MMSession()
        md5_username = self.__md5(friend.username)
        for chat in mm_session.execute('SELECT * FROM Chat_' + md5_username):
            chats.append(list(chat))
        return chats

    def _parse_friends(self):
        self.friends = {}
        friend_session = self.FriendSession()
        for friend in friend_session.query(Friend).all():
            friend_info = self.__parse_friend(friend)
            self.friends[friend_info.remark_info.wechat_id] = friend_info
        friend_session.close()

    def __parse_friend(self, friend) -> FriendInfo:
        friend_info = FriendInfo()
        friend_info.username = friend.username
        friend_info.type_info = self.__parse_type(friend.type)
        friend_info.remark_info = self.__parse_friend_remark(friend.remark)
        return friend_info

    @staticmethod
    def __parse_type(friend_type) -> TypeInfo:
        type_info = TypeInfo()
        # 二进制数
        arr = bin(friend_type)[2:]
        # 最后一位表示是否添加好友
        type_info.is_friend = int(arr[-1]) == 1
        return type_info

    @staticmethod
    def __parse_friend_remark(remark) -> RemarkInfo:
        total_length = len(remark)
        i = 0
        friend_remark_info = RemarkInfo()
        while 1:
            try:
                pos = RemarkPos(remark[i])
            except ValueError:
                logger.warning('标记字段类型错误: ', remark[i])
                continue
            # 第一位是\n，往后移一位
            i += 1
            if i >= total_length:
                break
            # 第二位记录后面的字符串长度，往后移一位
            length = remark[i]
            if length == 0:
                break
            if length == 0:
                continue
            i += 1
            if i >= total_length:
                break
            if i + length >= total_length:
                break
            content = remark[i:i + length].decode()

            if pos == RemarkPos.NICKNAME:
                friend_remark_info.nickname = content
            elif pos == RemarkPos.WECHAT_ID:
                friend_remark_info.wechat_id = content
            elif pos == RemarkPos.REMARK:
                friend_remark_info.remark = content
            elif pos == RemarkPos.REMARK_FULL_PINYIN:
                friend_remark_info.remark_full_pinyin = content
            elif pos == RemarkPos.REMARK_FIRST_LETTER:
                friend_remark_info.remark_first_letter = content
            elif pos == RemarkPos.NICKNAME_FULL_PINYIN:
                friend_remark_info.nickname_full_pinyin = content
            i += length
            if i == total_length:
                break
        return friend_remark_info

    @staticmethod
    def __md5(src):
        m2 = hashlib.md5()
        m2.update(src.encode())
        return m2.hexdigest()


if __name__ == '__main__':
    wp = WechatParser('WCDB_Contact.sqlite', 'MM.sqlite')
    wp.analyse()
    friend = wp.find_friend('wechat_id')
    chats = wp.find_chats('wechat_id')
    df = pd.DataFrame(chats)
    df.columns = [None, None, None, 'createtime', 'message', 'status', None, 'type', 'des']
    print('你好: %s' % friend.remark_info.nickname)
    print('我们成为微信好友是在%s，一个美好的时刻' % arrow.get(df.createtime[0]).format('YYYY年MM月DD日的HH点mm分ss秒'))
    seconds = arrow.now().timestamp - df.createtime[0]
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    print('现在想想，距离那时候已经过去了%d天%02d小时%02d分%02d秒' % (d, h, m, s))
    print('在这期间，我们总共发了%d条信息，其中有%d条由你发出，%d条由我发出' % (len(df), len(df[df.des == 1]), len(df[df.des == 0])))
    print('其中有%d条系统消息，%d条文本，%d条图片，%d条视频，%d条小视频，%d条语音，%d条分享链接，%d条位置，%d条动画表情，%d条名片，%d条语音/视频电话' % (
        len(df[df.type == 10000]), len(df[df.type == 1]), len(df[df.type == 3]), len(df[df.type == 43]),
        len(df[df.type == 62]), len(df[df.type == 34]), len(df[df.type == 49]), len(df[df.type == 48]),
        len(df[df.type == 47]), len(df[df.type == 42]), len(df[df.type == 50])))
