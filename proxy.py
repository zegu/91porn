#!/usr/bin/python3
# coding:utf-8
'''
Author: Caesar
Email: c_engineer@sina.com
Date: 2017-1-3
Info: urllib模块访问西刺代理获取可用的代理ip
'''

# python lib
from urllib import request
import random
import chardet
from bs4 import BeautifulSoup
import os


# 爬虫：获取网页信息
def spider_get_content(Spider_Items_Data):
    # 添加代理ip
    if Spider_Items_Data['proxyIp'] != '0.0.0.0':
        proxy_handler = request.ProxyHandler({'http': Spider_Items_Data['proxyIp']})
        proxy_auth_handler = request.ProxyBasicAuthHandler()
        opener = request.build_opener(proxy_handler, proxy_auth_handler)
        request.install_opener(opener)

    # 伪造的浏览器头信息
    forged_header = {
        'User-Agent': Spider_Items_Data['UserAgent'],
        'Referer': Spider_Items_Data['Referer'],
        'Host': Spider_Items_Data['Host'],
        Spider_Items_Data['Request_Type']: Spider_Items_Data['URL']
    }

    req = request.Request(Spider_Items_Data['URL'], headers=forged_header)

    # 访问网页, 获取网页编码
    html_coding = request.urlopen(req, timeout=8)
    encoding = chardet.detect(html_coding.read())["encoding"]

    # 访问网页, 获取网页信息
    html_content = request.urlopen(req, timeout=8)

    return html_content.read().decode(encoding)


# 爬虫：设置爬虫的信息
def spider_setitems(proxyIps, UserAgents, Referer, Host, URL, Request_Type):
    # 代理ip
    proxyIps = proxyIps
    # 浏览器客户端
    UserAgents = UserAgents
    # 来源网址
    Referer = Referer
    # 服务器
    Host = Host
    # 要访问的url
    URL = URL
    # 请求类型
    Request_Type = Request_Type

    # 把爬虫信息放在字典中
    spider_items_data = {
        'proxyIp': random.choice(proxyIps),
        'UserAgent': random.choice(UserAgents),
        'Referer': Referer,
        'Host': Host,
        'URL': URL,
        'Request_Type': Request_Type
    }

    return spider_items_data


# 从获取到的网页中提取能使用的ip
def testip_from_content(Html_Content):
    soup = BeautifulSoup(Html_Content, 'lxml')
    ips = soup.findAll('tr')

    save_ip = ''
    for index, ip in enumerate(ips):
        # 第一个信息不是ip
        if index == 0:
            continue

        tds = ip.findAll("td")
        # 检测ip是否可用
        # 被检测的ip
        proxy = 'http://%s:%s' % (tds[1].contents[0], tds[2].contents[0])

        print("total:%s  index:%d    ip:%s" % (len(ips), index, proxy))

        try:
            # 代理ip
            proxyIps = [proxy]
            # 浏览器客户端
            UserAgents = ['Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0',
                     'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 UBrowser/5.6.13705.206 Safari/537.36',
                     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36',
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36']
            # 来源网址
            Referer = 'http://ip.chinaz.com/getip.aspx'
            # 服务器
            Host = 'ip.chinaz.com'
            # 要访问的url
            URL = 'http://ip.chinaz.com/getip.aspx'
            # 请求类型
            Request_Type = 'GET'

            # 爬虫：设置爬虫的信息
            spider_items_data = spider_setitems(proxyIps, UserAgents, Referer, Host, URL, Request_Type)
            # 爬虫：获取网页信息
            html_content = spider_get_content(spider_items_data)

            print(html_content)
        except Exception as e:
            print(e)
            continue
        else:
            # 若可以使用，保存在本地
            save_ip = save_ip + proxy + os.linesep

    # 将ip保存在本地文件中
    ipFile = open('ips.txt', 'w')
    ipFile.write(save_ip)
    ipFile.close()


# 从西刺代理获取网页信息
def getip_from_xici():
    # 代理ip(0.0.0.0 表示不设置代理ip)
    proxyIps = ['0.0.0.0']
    # 浏览器客户端
    UserAgents = ['Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0',
                     'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 UBrowser/5.6.13705.206 Safari/537.36',
                     'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36',
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36']
    # 来源网址
    Referer = 'http://www.xicidaili.com/nn/'
    # 服务器
    Host = 'www.xicidaili.com'
    # 要访问的url
    URL = 'http://www.xicidaili.com/nn/'
    # 请求类型
    Request_Type = 'GET'

    # 爬虫：设置爬虫的信息
    spider_items_data = spider_setitems(proxyIps, UserAgents, Referer, Host, URL, Request_Type)
    # 爬虫：获取网页信息
    xici_html_content = spider_get_content(spider_items_data)

    return xici_html_content


def xiciIp():
    # 从西刺代理获取网页信息
    xici_html_content = getip_from_xici()
    # 从获取到的网页中提取能使用的ip
    testip_from_content(xici_html_content)


if __name__ == '__main__':
    # 西刺代理
    xiciIp()