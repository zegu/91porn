# coding:utf-8

class ISqlHelper(object):
    params = {'view_id': None, 'vno': None, 'vid': None, 'title': None, 'img_url': None, 'download_url': None, 'downloaded': None}

    def init_db(self):
        raise NotImplemented

    def drop_db(self):
        raise NotImplemented

    def insert(self, value=None):
        raise NotImplemented

    def delete(self, conditions=None):
        raise NotImplemented

    def update(self, conditions=None, value=None):
        raise NotImplemented

    def select(self, count=None, conditions=None):
        raise NotImplemented
