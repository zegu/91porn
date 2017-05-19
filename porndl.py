# -*-coding=utf-8-*-
import requests
import re
import json
import random
import time
from urllib import parse
from config import get_header
from db.DataStore import sqlhelper

cookies = {'language': 'cn_CN'}
requests.adapters.DEFAULT_RETRIES = 3
get_real = 'http://91.9p91.com/getfile_jw.php?VID='
current_proxy = None

# video_url_reg = re.compile('<a target=blank href="(.*?)"')
video_view_id_reg = re.compile('viewkey=(.*?)&')
vid_reg = re.compile('\?VID=(.*?)"')
title_reg = re.compile('<title>([\w\W]*?)-')

# real_reg = re.compile("<embed id='91' name='91' width='700' height='450' src='(.*?)'")
# vhead = 'http://91.9p91.com/9e.swf?autoplay=false&video_id=%s&mp4=999'
# tr = "<tr><td>%s</td><td><form target='_blank' action='hhhhhhhhplayer.html'><input type='hidden' name='url' value='%s'/> <input type='submit' value='view online'/></form></td></tr>\n"

cont_queue = []
video_queue = []
video_list = []
all_proxies = []


def init_proxies(count=100):
    proxy_api = 'http://127.0.0.1:8000/?count=%d&types=0' % count
    r = requests.get(proxy_api, headers=get_header())
    return json.loads(r.content.decode('utf-8'))


def get_proxy():
    if not len(all_proxies):
        raise AssertionError('No chinese proxy is valid，Please use -x or -s option instead!')
    global current_proxy
    if not current_proxy:
        proxy_index = random.randint(0, len(all_proxies) - 1)
        proxy = all_proxies[proxy_index]
        current_proxy = {
            'ip': proxy[0],
            'port': proxy[1],
            'index': proxy_index,
            'http': '%s:%s' % (proxy[0], proxy[1])
        }
    return current_proxy


def remove_proxy(proxy):
    try:
        global current_proxy
        current_proxy = None
        all_proxies.pop(proxy['index'])
        requests.get('http://127.0.0.1:8000/delete?ip=' + proxy['ip'])
        print('remove proxy %s' % proxy['http'])
    except Exception as e:
        print('get_lists_content fail ', e)


def get_lists_content(list_url):
    try:
        print('start parse url: %s' % (list_url))
        content = requests.get(list_url, cookies=cookies).content.decode('utf-8', 'backslashreplace')
        return content
    except Exception as e:
        print('get_lists_content fail ', e)


def decode_lists(content):
    vid_lists = video_view_id_reg.findall(str(content))
    return vid_lists


def get_detail_content(video_url):
    retry = 0
    times = 100
    success = False
    while retry < times:
        try:
            proxies = get_proxy()
            print('start parse url: %s, use proxy %s' % (video_url, proxies['http']))
            r = requests.get(video_url, cookies=cookies, proxies=proxies)
            content = r.content.decode('utf-8', 'backslashreplace')

            if r.status_code is 200:
                print('fetch url %s success' % video_url)
                if '<source' in content:
                    print('Succeed!')
                    success = True
                    break
                if '你每天只可观看10个视频' in content:
                    print(' 超出限制')
                elif 'recaptcha' in content:
                    print(' 需要验证码')
                elif 'blockpage' in content:
                    print(' blocked')
                else:
                    print(content)
                remove_proxy(proxies)
            else:
                print('fetch url %s fail with code %s' % (video_url, r.status_code))
                remove_proxy(proxies)

        except Exception as e:
            print('get_detail_content fail', e)
            remove_proxy(proxies)
        finally:
            retry = retry + 1
    if success:
        return content
    print('get_detail_content fail')


def get_video_info(vid=''):
    api_url = get_real + vid
    vid_info_string = requests.get(api_url).content.decode('utf-8')
    vid_info = parse.parse_qs(str(vid_info_string))
    return vid_info


def init_base_url():
    vid_info = get_video_info()
    url = vid_info['domainUrl'][0]
    print('use base url ' + url)
    return url


def decode_video_info(vid, extract_info={}, url_only=False):
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
        print('decode_video_info fail', e)


def decode_download_url(content):
    try:
        content = str(content)
        vid = vid_reg.findall(content)[0]
        view_id = video_view_id_reg.findall(content)[0]
        title = title_reg.findall(content)[0].strip()
        return decode_video_info(vid, {'title': title, 'view_id': view_id})
    except Exception as e:
        print('decode_download_url fail', e)


def craw_lists_detail(view_ids):
    for view_id in view_ids:
        craw_detail(view_id)


def craw_detail(view_id):
    if not check_vid_exist(view_id):
        detail_url_format = base_url + '/view_video.php?viewkey=%s'
        vid_info = decode_download_url(
            get_detail_content(detail_url_format % view_id)
        )
        if vid_info:
            save_vid_info(vid_info)
        else:
            print('video %s fail' % view_id)
    else:
        print('video %s exist' % view_id)


def check_vid_exist(view_id):
    res = sqlhelper.select(1, {'view_id': view_id})
    if len(res):
        return True
    return False


def save_vid_info(vid_info):
    if not check_vid_exist(view_id=vid_info['view_id']):
        res = sqlhelper.insert(vid_info)
        return res
    return True


def craw_lists(category, total_page=20, params=''):
    view_ids = []
    for page in range(1, total_page + 1):
        list_url = base_url + '/v.php?category=%s&page=%d' % (category, page) + params
        new_view_ids = decode_lists(
            get_lists_content(list_url)
        )
        if len(new_view_ids):
            print('get view counts %d' % len(new_view_ids))
            view_ids = view_ids + new_view_ids
            time.sleep(1)
        else:
            print('get total page %d, video count: %d' % (page, len(view_ids)))
            break
    return view_ids


if __name__ == '__main__':
    # with open('list.html', 'r') as f:
    #     lists_content = str(f.readlines())

    # with open('detail.html', 'r') as f:
    #     detail_content = str(f.readlines())
    base_url = init_base_url()
    all_proxies = init_proxies(300)
    print('init proxies %d' % len(all_proxies))
    if len(all_proxies) <= 0:
        raise Exception('no proxies')
    exit()

    view_ids = list(set(craw_lists('top', 5, '&m=3')))
    print('start craw video total %d' % len(view_ids))
    craw_lists_detail(view_ids)

    # craw_lists_detail(['c4c9d90994731a152596'])

    # info = {'vid': '0c64Ikj2aSTaNRjJM5jWvuE4bhxuslSlLlD7eP8ZeqQ0V4qI', 'vno': '213707',
    #         'img_url': 'http://img2.t6k.co/thumb/213707.jpg',
    #         'download_url': 'http://192.240.120.2//mp43/213707.mp4?st=DCsbwvQ271dhywgEJ211Dw&e=1495189115',
    #         'title': '【申精】跑步机上深插银行客户经理Eva娜娜淫穴（番号008）', 'view_id': 'c4c9d90994731a152596'}
    # if not check_vid_exist(view_id=info['view_id']):
    #     save_vid_info(info)
    #     save_vid_info(info)
    # print(check_vid_exist(view_id=info['view_id']))
