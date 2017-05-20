from bs4 import BeautifulSoup as bs
import requests
import re
import random
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import http
from urllib import parse
import time
from db.DataStore import sqlhelper

cookies = dict(language='cn_CN')
get_real = 'http://91.9p91.com/getfile_jw.php?VID='
base_url = 'http://email.91dizhi.at.gmail.com.t9i.club'
view_ids = []

# re
video_view_id_reg = re.compile('viewkey=(.*?)&')
vid_reg = re.compile('\?VID=(.*?)"')
title_reg = re.compile('<title>([\w\W]*?)-')

# 设置 user-agent列表，每次请求时，可在此列表中随机挑选一个user-agnet
uas = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/58.0.3029.96 Chrome/58.0.3029.96 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0; Baiduspider-ads) Gecko/17.0 Firefox/17.0",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9b4) Gecko/2008030317 Firefox/3.0b4",
    "Mozilla/5.0 (Windows; U; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727; BIDUBrowser 7.6)",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; Trident/7.0; Touch; LCJB; rv:11.0) like Gecko",
]


def init_base_url():
    global base_url
    vid_info = get_video_info()
    base_url = vid_info['domainUrl'][0]
    print('use base url ' + base_url)
    return base_url


def get_video_info(vid=''):
    api_url = get_real + vid
    vid_info_string = get_content(api_url)
    vid_info = parse.parse_qs(str(vid_info_string))
    return vid_info


def setHeader():
    randomIP = str(random.randint(0, 255)) + '.' + str(random.randint(0, 255)) + '.' + str(
        random.randint(0, 255)) + '.' + str(random.randint(0, 255))
    headers = {
        'User-Agent': random.choice(uas),
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        'X-Forwarded-For': randomIP,
    }
    return headers


def get_content(url):
    try:
        print('start craw %s ', url)
        s = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=10,
                        status_forcelist=[500, 502, 503, 504]
                        )
        s.mount('http://', HTTPAdapter(max_retries=retries))
        r = s.get(url, headers=setHeader())
        if r.ok:
            print('[success] craw %s  with status code %d' % (url, r.status_code))
            return r.content.decode('utf-8', 'backslashreplace')
        print('[fail] craw %s fail with status code %d' % (url, r.status_code))
    except ConnectionResetError:
        print('ConnectionResetError')
        time.sleep(0.5)
        get_content(url)
    except http.client.IncompleteRead:
        print('http.client.IncompleteRead')
        time.sleep(0.5)
        get_content(url)


def decode_lists(content):
    return video_view_id_reg.findall(str(content))


def decode_download_info(vid, extract_info={}, url_only=False):
    try:
        vid_info = get_video_info(vid)
        vid_no = vid_info['VID'][0]
        download_url = vid_info['file'][0] + '?' + 'st=' + vid_info['st'][0] + '&' + 'e=' + vid_info['e'][0]

        if url_only:
            return download_url

        info = {
            'vid': vid,
            'vno': vid_no,
            'img_url': '%sthumb/%s.jpg' % (vid_info['imgUrl'][0], vid_no),
            'download_url': download_url
        }
        info.update(extract_info)
        return info
    except Exception as e:
        print('decode_download_info fail', e)


def decode_detail_info(content):
    content = str(content)
    vid = vid_reg.findall(content)[0]
    view_id = video_view_id_reg.findall(content)[0]
    title = title_reg.findall(content)[0].strip()
    return decode_download_info(vid, {'title': title, 'view_id': view_id})


def trans_list_url(cat='rf', page=1):
    return (base_url + 'video.php?category=%s&page=%d') % (str(cat), int(page))


def trans_detail_url(view_id):
    return (base_url + '/view_video.php?viewkey=%s') % str(view_id)


def check_vid_exist(view_id):
    res = sqlhelper.select(1, {'view_id': view_id})
    if len(res):
        print('view id %s exist, skip' % view_id)
        return True
    return False


def save_vid_info(vid_info):
    if not check_vid_exist(view_id=vid_info['view_id']):
        if vid_info:
            res = sqlhelper.insert(vid_info)
        else:
            print('[save fail]')
            print(vid_info)
        return res
    return True


if __name__ == '__main__':
    init_base_url()
    for page in range(1, 6):
        view_ids = view_ids + decode_lists(get_content(trans_list_url('rf', page)))
    print(view_ids)
    for view_id in view_ids:
        if not check_vid_exist(view_id):
            vid_info = decode_detail_info(get_content(trans_detail_url(view_id)))
            save_vid_info(vid_info)
