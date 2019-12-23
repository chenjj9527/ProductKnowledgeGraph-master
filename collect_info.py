#!/usr/bin/env python3
# coding: utf-8
# File: build_kg.py
# Author: cjj
# Date: 19-12-23

import urllib.request
from urllib.parse import quote_plus
from lxml import etree
import gzip
import chardet
import json
import pymongo

class GoodSchema:
    def __init__(self):
        self.conn = pymongo.MongoClient()
        return

    '''获取搜索页'''
    def get_html(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17"}
        try:
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req).read()
            coding = chardet.detect(data)
            html = data.decode(coding['encoding'])
        except:
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req).read()
            html = data.decode('gbk')


        return html

    '''获取详情页'''
    def get_detail_html(self, url):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "referer": "https://www.jd.com/allSort.aspx",
            "upgrade-insecure-requests": 1,
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/66.0.3359.181 Chrome/66.0.3359.181 Safari/537.36"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req).read()
            html = gzip.decompress(data)
            coding = chardet.detect(html)
            html = html.decode(coding['encoding'])
        except Exception as e:
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req).read()
            html = gzip.decompress(data)
            html = html.decode('gbk')
        return html


    '''根据主页获取数据'''
    def home_list(self):
        url = 'https://www.jd.com/allSort.aspx'
        html = self.get_html(url)
        selector = etree.HTML(html)
        divs = selector.xpath('//div[@class= "category-item m"]')
        for indx, div in enumerate(divs):
            first_name = div.xpath('./div[@class="mt"]/h2/span/text()')[0]
            second_classes = div.xpath('./div[@class="mc"]/div[@class="items"]/dl')
            for dl in second_classes:
                second_name = dl.xpath('./dt/a/text()')[0]
                third_classes = ['https:' + i for i in dl.xpath('./dd/a/@href')]
                third_names = dl.xpath('./dd/a/text()')
                for third_name, url in zip(third_names, third_classes):
                    try:
                        attr_dict = self.parser_goods(url)
                        attr_brand = self.collect_brands(url)
                        attr_dict.update(attr_brand)
                        data = {}
                        data['fisrt_class'] = first_name
                        data['second_class'] = second_name
                        data['third_class'] = third_name
                        data['attrs'] = attr_dict
                        self.conn['goodskg']['data'].insert(data)
                        print(indx, len(divs), first_name, second_name, third_name)
                    except Exception as e:
                        print(e)
        return

    '''解析商品数据'''
    def parser_goods(self, url):
        html = self.get_detail_html(url)
        selector = etree.HTML(html)
        title = selector.xpath('//title/text()')
        attr_dict = {}
        other_attrs = ''.join([i for i in html.split('\n') if 'other_exts' in i])
        other_attr = other_attrs.split('other_exts =[')[-1].split('];')[0]
        if other_attr and 'var other_exts ={};' not in other_attr:
            for attr in other_attr.split('},'):
                if '}' not in attr:
                    attr = attr + '}'
                data = json.loads(attr)
                key = data['name']
                value = data['value_name']
                attr_dict[key] = value
        attr_divs = selector.xpath('//div[@class="sl-wrap"]')
        for div in attr_divs:
            attr_name = div.xpath('./div[@class="sl-key"]/span/text()')[0].replace('：','')
            attr_value = ';'.join([i.replace('  ','') for i in div.xpath('./div[@class="sl-value"]/div/ul/li/a/text()')])
            attr_dict[attr_name] = attr_value

        return attr_dict

    '''解析品牌数据'''
    def collect_brands(self, url):
        attr_dict = {}
        brand_url = url + '&sort=sort_rank_asc&trans=1&md=1&my=list_brand'
        html = self.get_html(brand_url)
        if 'html' in html:
            return attr_dict
        data = json.loads(html)
        brands = []

        if 'brands' in data and data['brands'] is not None:
            brands = [i['name'] for i in data['brands']]
        attr_dict['品牌'] = ';'.join(brands)

        return attr_dict



if __name__ == '__main__':
    handler = GoodSchema()
    handler.home_list()