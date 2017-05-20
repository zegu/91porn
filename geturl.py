from db.DataStore import sqlhelper
import porndl


def refresh_download_url_by_tag():
    res = sqlhelper.select(100, {'downloaded': 0})
    for item in res:
        vid = (item[1])
        refresh_download_url(vid)


def refresh_download_url_by_vno(vnos):
    for vno in vnos:
        res = sqlhelper.select(1, {'vno': vno})
        item = res[0]
        vid = (item[1])
        refresh_download_url(vid)


def refresh_download_url(vid):
    vid_info = porndl.decode_video_info(vid)
    print(vid_info['download_url'])
    sqlhelper.update({'vid': vid_info['vid']}, {'download_url': vid_info['download_url']})


if __name__ == '__main__':
    vnos = ['208077']
    refresh_download_url_by_vno(vnos)
