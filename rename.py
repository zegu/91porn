import os
from db.DataStore import sqlhelper


def query_title(vno):
    res = sqlhelper.select(1, {'vno': vno})
    if len(res):
        return res[0][3]
    return None


if __name__ == '__main__':
    dir = '/Volumes/Beansme/Download/91/done/'
    for filename in os.listdir(dir):
        file_info = filename.split('.')
        vno = file_info[0]
        title = query_title(vno)
        if title:
            title = title.replace('\n', '').replace('/', '').replace(' ', '')
            os.rename(dir + filename,
                      dir + '%s-%s.%s' % (title, vno, file_info[1]))
