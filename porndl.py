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
    return json.loads(r.content)


def get_proxy():
    if not len(all_proxies):
        raise AssertionError('No chinese proxy is valid，Please use -x or -s option instead!')
    proxy_index = random.randint(0, len(all_proxies) - 1)
    proxy = all_proxies[proxy_index]
    return {
        'ip': proxy[0],
        'port': proxy[1],
        'index': proxy_index,
        'http': '%s:%s' % (proxy[0], proxy[1])
    }


def remove_proxy(proxy):
    try:
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
                if '你每天只可观看10个视频' in content:
                    print(proxies['http'] + ' 超出限制')
                    remove_proxy(proxies)
                    pass
                elif 'recaptcha' in content:
                    print(proxies['http'] + ' 需要验证码')
                    remove_proxy(proxies)
                    pass
                elif '<source' in content:
                    print(proxies['http'] + ' Succeed!')
                    success = True
                    break
                else:
                    print(content)
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
        print(vid_info)
        save_vid_info(vid_info)
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
    get_real = 'http://91.9p91.com/getfile_jw.php?VID='
    base_url = init_base_url()
    all_proxies = init_proxies(300)

    # view_ids = list(set(craw_lists('top', 5, '&m=2')))
    view_ids = ['552e22b0276be5fe150a', 'ab53e10718a30bb25237', '84eebb5a843d7686e150', 'f307c7e7488e0ff6ebbb',
                'cc1ef92d0ad4bb4fa61f', '184b804bf01bf50088ea', '8319a14bd3c0f7c7ec66', '44d042dc85d8b29b9726',
                'c576f26c729fccaa0ae4', 'd6176a030a8e09c77a08', 'b8b71673e5f95af71635', '8a61ee28819c1831d4b8',
                'c0285364407607b2ab6d', 'fc2579345f21f096e333', 'ab3fb7fb57cd7a7c9c39', 'e3ebad991d210bd6b140',
                'e8ac708e2478c4cc950e', '1f8928706637e3fc460d', '38445ecb2ad6c1eb08f1', '1f2f14465ffc8770c1dd',
                'bac9129f14e21cb557ac', 'd7a0d269fafefa571da4', '1825daa8e514d0a4b046', '3a0ba731626d075f2a90',
                '6593a3f272f211435409', '114fb9e38e09fd6351a2', '676f9b8780792748327d', 'b2444faf935c9a96d249',
                'be0a9df5b96a6433dc9f', '7eb5619bed3b0b3b7bcb', '8936385476f729d70e4f', '7876172bb267958b4b7a',
                '18545734c2ac133e1f9d', '270c228641d4cab07c2d', 'd2fedeace73b3028df1b', 'ff6f22b6d998940b6c62',
                '1bd16a1f4c3139bce8d2', '82ac6b2ee17ccc7cbf45', '779ef48345857b904448', 'a152d3b10460ea665e20',
                '90af23e2d5cf6c75efbe', '0bee2fe2adc8e14434a4', '2071fc6a6b6e3cb86573', '47c3df4115f3d9f8dbd0',
                '20d39f778e3eda58946c', '50b134d8e1eeaf8e153b', '5c6ddc0ea6a74992b754', 'f3a4ffe0f37657ab1c41',
                'd664d66669ae08c7cc0c', '27c0e110a309ca7f669a', '6ca0686a575de6950fde', 'c12f10020fda89a4aed1',
                '8c913454f62732d0e3dc', 'c0998750e797bc13061c', '1b45bbac3056ec5e5dd7', '9774695c4d09ece49aea',
                '941e9411d733d3b0e6a0', '500de3cb1cc0d0391e78', 'fddd964834eef9ed963a', '1d4a863dee089c12f4ff',
                '977def5637a6f8f54e98', '5f7d9259e8ed1c6b604b', '383f7331946994cb38a9', '41984ebbe4443c51e026',
                'a0d4d8557190c5793c9a', '6a6b4efcf8a16d241587', 'cade6052f8ea3a63bfc2', 'b3a79590edfb1dff129c',
                '63bdab6bcdcc7c8b6c38', 'd0f6bdef640691dd0625', '4dcd40e7d66b80243e1f', 'f3967500ddda4a81ca90',
                '19f5479ce57d11787757', '1f31bd30ebab94f5c646', '7562cfc512d1ee4e04c2', 'd1f3ebbc433e2623a4e1',
                '518a618281da5ca67c91', 'b4b295d06a6ddfee621b', '06ecca99b336e62dbe08', '7035a8b7ecbf15e0782f',
                'b3c0ef36824568bfdaba', '3061b9e6960271c04548', 'a9f7e32b92ff1f97cbca', '5cf03dacc06ce3dd04a1',
                '93d3c80d8089db3499d9', 'dce205944ffce73942ef', '64e1b677c64b814cf164', '91b92c65d9d5624ddb80',
                '0a91dcb523bf4c6cdbd6', '2b7bee996bf21dca52da', 'e7ca0ed9cc1ce2eed0a9', '0f9ea7c88cfbef791cfb',
                '399083c0a1b8d05cea31', '21dd42f6642a85acefd3', '3e07b52cfad8c5cf6326', 'd95acaa132aa3b8b1769',
                'ea28db2ba284032743f6', '6a1ddd30a7010e295840', '8ab5ce5337c4393f14f0', '5d778ed049fa71c34910']
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
