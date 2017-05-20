# coding:utf-8
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, create_engine, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG

from db.ISqlHelper import ISqlHelper

'''
sql操作的基类
包括ip，端口，types类型(0高匿名，1透明)，protocol(0 http,1 https http),country(国家),area(省市),updatetime(更新时间)
 speed(连接速度)
'''

BaseModel = declarative_base()


class Video(BaseModel):
    __tablename__ = 'video'
    id = Column(Integer, primary_key=True, autoincrement=True)
    view_id = Column(VARCHAR(100), nullable=False)
    title = Column(VARCHAR(300), nullable=False, default=0)
    img_url = Column(VARCHAR(100), nullable=False)
    download_url = Column(VARCHAR(300), nullable=False)
    vid = Column(VARCHAR(100), nullable=True)
    vno = Column(VARCHAR(32), nullable=True)
    updatetime = Column(DateTime(), default=datetime.datetime.utcnow)
    downloaded = Column(Integer, default=0)


class SqlHelper(ISqlHelper):
    params = {'view_id': Video.view_id, 'vid': Video.vid, 'vno': Video.vno, 'title': Video.title,
              'img_url': Video.img_url, 'download_url': Video.download_url, 'downloaded': Video.downloaded}

    def __init__(self):
        if 'sqlite' in DB_CONFIG['DB_CONNECT_STRING']:
            connect_args = {'check_same_thread': False}
            self.engine = create_engine(DB_CONFIG['DB_CONNECT_STRING'], echo=False, connect_args=connect_args)
        else:
            self.engine = create_engine(DB_CONFIG['DB_CONNECT_STRING'], echo=False)
        DB_Session = sessionmaker(bind=self.engine)
        self.session = DB_Session()

    def init_db(self):
        BaseModel.metadata.create_all(self.engine)

    def drop_db(self):
        BaseModel.metadata.drop_all(self.engine)

    def insert(self, value):
        video = Video(view_id=value['view_id'], vid=value['vid'], vno=value['vno'], title=value['title'],
                      img_url=value['img_url'], download_url=value['download_url'])
        self.session.add(video)
        self.session.commit()

    def delete(self, conditions=None):
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Video)
            for condition in conditions:
                query = query.filter(condition)
            deleteNum = query.delete()
            self.session.commit()
        else:
            deleteNum = 0
        return ('deleteNum', deleteNum)

    def update(self, conditions=None, value=None):
        '''
        conditions的格式是个字典。类似self.params
        :param conditions:
        :param value:也是个字典：{'ip':192.168.0.1}
        :return:
        '''
        if conditions and value:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Video)
            for condition in conditions:
                query = query.filter(condition)
            updatevalue = {}
            for key in list(value.keys()):
                if self.params.get(key, None):
                    updatevalue[self.params.get(key, None)] = value.get(key)
            updateNum = query.update(updatevalue)
            self.session.commit()
        else:
            updateNum = 0
        return {'updateNum': updateNum}

    def select(self, count=None, conditions=None):
        '''
        conditions的格式是个字典。类似self.params
        :param count:
        :param conditions:
        :return:
        '''
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
        else:
            conditions = []

        query = self.session.query(Video.view_id, Video.vid, Video.vno, Video.title, Video.img_url, Video.download_url, Video.downloaded)
        if len(conditions) > 0 and count:
            for condition in conditions:
                query = query.filter(condition)
            return query.limit(count).all()
        elif count:
            return query.limit(count).all()
        elif len(conditions) > 0:
            for condition in conditions:
                query = query.filter(condition)
            return query.all()
        else:
            return query.all()

    def close(self):
        pass


if __name__ == '__main__':
    sqlhelper = SqlHelper()
    sqlhelper.init_db()
    proxy = {'ip': '192.168.1.1', 'port': 80, 'type': 0, 'protocol': 0, 'country': '中国', 'area': '广州', 'speed': 11.123,
             'types': ''}
    sqlhelper.insert(proxy)
    sqlhelper.update({'ip': '192.168.1.1', 'port': 80}, {'score': 10})
    print(sqlhelper.select(1))
