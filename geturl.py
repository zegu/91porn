from db.DataStore import sqlhelper
import porndl

if __name__ == '__main__':
    res = sqlhelper.select(100, {'downloaded': 0})
    for item in res:
        vid = (item[1])
        vid_info = porndl.decode_video_info(vid)
        print(vid_info)
        sqlhelper.update({'vid': vid_info['vid']}, {'download_url': vid_info['download_url']})
