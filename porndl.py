# -*-coding=utf-8-*-
import requests
import re
import time
import random
from urllib import parse

base_url = 'http://91p05.space'
get_real = 'http://91.9p91.com/getfile_jw.php?VID='
list_url_format = base_url + '/v.php?page=%d&category=rf'
detail_url_format = base_url + '/view_video.php?viewkey=%s'
cookies = {'session_language': 'cn_CN'}

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


def get_proxies():
    all_proxies = [
        '1.83.124.217:8118',
        '221.229.46.177:808',
        '122.90.83.213:80',
        '221.229.45.82:808',
        '115.225.203.199:8118',
        '115.193.199.128:8118',
        '121.204.165.14:8118',
        '116.226.90.12:808',
        '112.87.92.166:8118',
        '180.76.154.5:8888',
        '139.224.237.33:8888',
        '175.0.128.203:80',
        '113.221.252.78:80',
        '110.17.3.102:8118',
        '182.38.172.68:8118',
        '60.176.191.150:8118',
        '221.229.44.7:808',
    ]
    if not len(all_proxies):
        raise AssertionError('No chinese proxy is valid，Please use -x or -s option instead!')
    return random.choice(all_proxies)


def get_lists_content(total_page=1):
    for page in range(1, total_page + 1):
        list_url = list_url_format % page
        print('start parse url: ' + list_url)
        while True:
            try:
                proxies = {
                    'http': 'http//{}'.format(get_proxies())
                }
                content = requests.get(list_url, cookies=cookies, proxies=proxies).content
                return str(content)
            except Exception as e:
                print(e)


def decode_lists(content):
    vid_lists = video_view_id_reg.findall(content)
    return vid_lists


def get_detail_content(view_id, detail_url_format=detail_url_format):
    video_url = detail_url_format % str(view_id)
    while True:
        try:
            proxies = {
                'http': 'http//{}'.format(get_proxies())
            }
            content = requests.get(video_url, cookies=cookies, proxies=proxies).content
        except Exception as e:
            print(e)
        else:
            pass
        finally:
            if '你每天只可观看10个视频' in content:
                print(proxies + ' 超出限制')
                break
                pass
            if 'CAPTCHA' in content:
                print(proxies + ' 需要验证码')
                pass
            if '<source' in content:
                print(proxies + ' Succeed!')
                return content


def get_video_info(vid, extract_info={}, url_only=False):
    api_url = get_real + vid
    vid_info_string = str(requests.get(api_url).content)
    vid_info = parse.parse_qs(vid_info_string)
    vid_no = vid_info['VID'][0]
    download_url = vid_info['file'][0] + '?' + 'st=' + vid_info['st'][0] + '&' + 'e=' + vid_info['e'][0].replace(
        '\'', '')
    
    if url_only:
        return download_url

    info = {
        'vid': vid,
        'vno': vid_no,
        'img_url': '%s/thumb/%s.jpg' % (vid_info['imgUrl'][0], vid_no),
        'download_url': download_url
    }
    info.update(extract_info)
    return info


def decode_download_url(content):
    try:
        vid = vid_reg.findall(content)[0]
        view_id = video_view_id_reg.findall(content)[0]
        title = title_reg.findall(content)[0].strip()
        return get_video_info(vid, {'title': title, 'view_id': view_id})
    except Exception as e:
        print(e)


if __name__ == '__main__':
    with open('list.html', 'r') as f:
        lists_content = str(f.readlines())

    with open('detail.html', 'r') as f:
        detail_content = str(f.readlines())

    vid_lists = decode_lists(lists_content)
    vid_info = decode_download_url(detail_content)
    print(vid_info)
