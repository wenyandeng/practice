#-*- coding: utf-8 -*-

# Version 0.1

import re #正则表达式
import os
import time
import stat
import platform
import sys

#import lxml
from lxml import etree
import requests

ROOT_DIR = "2018"
RECORD_ALL = "record_all.txt"
DEALED = "dealed.txt"
FAILED_RECORD = "failed.txt"

TARGET_ALL_URL = '//ul[@class="archives"]/li/p[@class]/a[@target="_blank"]/@href'
TARGET_PER_PAGE = '//div[@class="main-image"]/p/a/img/@*'
TARGET_PER_PAGE_NUM = '//div[@class="pagenavi"]/a/span/text()'

TARGET_URL = "http://www.mzitu.com/all"

MY_HEADERS = {
        'Referer':'http://www.mzitu.com',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }

def show_plat():
    """
    显示当前运行环境的一些信息
    """
    week = ["一", "二", "三", "四", "五", "六", "日"]
    nowtime = time.strftime('%Y年%m月%d日 %H点%M分  星期', time.localtime(time.time()))  + week[time.localtime(time.time()).tm_wday]
    print("===========================================================")
    print("当前操作系统:{}".format(platform.platform()))
    print("计算机名称:  {}".format(platform.node()))
    print("当前系统时间:{}".format(nowtime))
    print("工程目录:    {}".format(os.getcwd()))
    print("===========================================================")

def get_page(url, header):
    #page = requests.Session()
    for i in range(7):
        try:
            resp = requests.get(url = url, headers = header)
        except:
            if i < 6:
                print("请求url:[{}]第{}次".format(url, i))
                time.sleep(i + 3)
            else:
                print("请求url：{}失败！！！".format(url))
                save_record(FAILED_RECORD, url)
                return "N/A"
        else:
            break
    return resp.content

def save_file(name, content):
    with open(name, "wb") as fp:
        fp.write(content)

def save_record(name, content):
    with open(name, "at") as fp:
        fp.write(content)
        fp.write('|')

def read_record(name):
    """
    读取下载过网站的配置文件
    返回下载过网站url列表
    """
    #判断文件是否存在，不存在则建立
    if os.path.exists(DEALED) == False:
        os.mknod(DEALED, mode=0o774)

    with open(name, "rt") as fp:
        return fp.read().split('|')

def deal_per_page(per_page):
    per_resp = get_page(per_page, MY_HEADERS)
    per_page_tree = etree.HTML(per_resp)
    #一共多少张
    per_page_num = per_page_tree.xpath(TARGET_PER_PAGE_NUM) 
    #目标地址和名字
    now_page = per_page_tree.xpath(TARGET_PER_PAGE) 
    
    try:
        cnt = int(per_page_num[-2])
    except:
        print("num is 0")
        cnt = 0
    page_list = list(now_page)
    page_list.append(cnt)

    #page_url, page_name, page_num = page_list
    #print("url:{}, num:{}, name:{}".format(page_url, page_num, page_name))
    return page_list

def get_web_source(my_url):
    """
    处理请求
    """
    resp = get_page(my_url, MY_HEADERS)

    #page_decode_re = re.compile(r'charset=(.+)', re.IGNORECASE)
    #testtest = resp.headers['Content-Type']
    #decode_page = page_decode_re.findall(testtest)
    #resp.encoding = decode_page[0]
    
    #初始化页面为文档结构
    tree_page = etree.HTML(resp)
    target_url_list = tree_page.xpath(TARGET_ALL_URL)


    #读取下载过的url,和总的新的url对比,如果下载过则去除
    dealed_list = read_record(DEALED)
    list_all = set(target_url_list) ^ set(dealed_list)
    now_list =  [url for url in list_all if url.startswith('http://')]

    print("待爬去网页:{}".format(len(now_list)))
    j = 0
    for page in now_list:
        j += 1
        print("==========当前第{}.页URl:{}===========".format(j, page))
        #获取url,照片数目,还有名字
        try:
            page_list = deal_per_page(page)
            page_url, page_name, page_num = page_list

            if os.path.exists(page_name) == False:
                os.mkdir(page_name)
            file_name = os.path.join(page_name, page_url.split('/')[-1])
        except:
            print("继续下一页")
            continue

        print("正在保存:{}".format(page_url))
        page_headers = MY_HEADERS
        page_headers["Referer"] = page_url
        save_file(file_name, get_page(page_url, page_headers))

        #每个page中有多个照片进行循环下载
        for i in range(page_num):
            url = page + '/' + str(i + 1)
            try:
                page_url, page_name, *_ = deal_per_page(url)
                name = str(i) + page_url.split('/')[-1]
                file_name = os.path.join(page_name, name)
            except:
                print("跳过{},继续下一个".format(url))
                continue
            print("Downloading ... [{}]".format(page_url))
            #防止盗链
            page_headers = MY_HEADERS
            page_headers["Referer"] = page_url
            page_content = get_page(page_url, page_headers)
            print("正在保存:{} 第{}张".format(name, i + 1))
            save_file(file_name, page_content)
            time.sleep(0.5)

        save_record(DEALED, page)
        print("url:[{}]下载成功！！等待下载下一组".format(page))
        time.sleep(8)

def start_spider():
    """
    开始程序
    """
    show_plat()

    if os.path.exists(ROOT_DIR) == False:
        os.mkdir(ROOT_DIR)
    os.chdir(ROOT_DIR)

    print("开始爬取 {} 网站".format(TARGET_URL))
    print("当前目录:{}".format(os.getcwd()))
    get_web_source(TARGET_URL)


if __name__ == '__main__':
    start_spider()
