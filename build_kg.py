#!/usr/bin/env python3
# coding: utf-8
# File: build_kg.py
# Author: cjj
# Date: 19-12-23

import json
import os
from py2neo import Graph, Node, Relationship



class GoodsKg:
    def __init__(self):
        cur = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.data_path = os.path.join(cur, 'data/goods_info.json')
        self.g = Graph(
            host="127.0.0.1",  # neo4j 搭载服务器的ip地址，ifconfig可获取到
            http_port=7474,  # neo4j 服务器监听的端口号
            user="neo4j",  # 数据库user name，如果没有更改过，应该是neo4j
            password="111111")
        return

    '''读取数据'''
    def read_data(self):
        rels_goods = []
        rels_brand = []
        goods_attrdict = {}
        concept_goods = set()
        concept_brand = set()
        count = 0
        for line in open(self.data_path,encoding='UTF-8'):
            count += 1
            print(count)
            line = line.strip()
            data = json.loads(line)
            first_class = data['fisrt_class'].replace("'",'')
            second_class = data['second_class'].replace("'",'')
            third_class = data['third_class'].replace("'",'')
            attr = data['attrs']
            concept_goods.add(first_class)
            concept_goods.add(second_class)
            concept_goods.add(third_class)
            rels_goods.append('@'.join([second_class, 'is_a', '属于', first_class]))
            rels_goods.append('@'.join([third_class, 'is_a', '属于', second_class]))

            if attr and '品牌' in attr:
                brands = attr['品牌'].split(';')
                for brand in brands:
                    brand = brand.replace("'",'')
                    concept_brand.add(brand)
                    rels_brand.append('@'.join([brand, 'sales', '销售', third_class]))

            goods_attrdict[third_class] = {name:value for name,value in attr.items() if name != '品牌'}

        return concept_brand, concept_goods, rels_goods, rels_brand

    '''构建图谱'''
    def create_graph(self):
        concept_brand, concept_goods, rels_goods, rels_brand = self.read_data()
        print('creating nodes....')
        self.create_node('Product', concept_goods)
        self.create_node('Brand', concept_brand)
        print('creating edges....')
        self.create_edges(rels_goods, 'Product', 'Product')
        self.create_edges(rels_brand, 'Brand', 'Product')
        return

    '''批量建立节点'''
    def create_node(self, label, nodes):
        pairs = []
        bulk_size = 1000
        batch = 0
        bulk = 0
        batch_all = len(nodes)//bulk_size
        print(batch_all)
        for node_name in nodes:
            sql = """CREATE(:%s {name:'%s'})""" % (label, node_name)
            pairs.append(sql)
            bulk += 1
            if bulk % bulk_size == 0 or bulk == batch_all+1:
                sqls = '\n'.join(pairs)
                self.g.run(sqls)
                batch += 1
                print(batch*bulk_size,'/', len(nodes), 'finished')
                pairs = []
        return


    '''构造图谱关系边'''
    def create_edges(self, rels, start_type, end_type):
        batch = 0
        count = 0
        for rel in set(rels):
            count += 1
            rel = rel.split('@')
            start_name = rel[0]
            end_name = rel[3]
            rel_type = rel[1]
            rel_name = rel[2]
            sql = 'match (m:%s), (n:%s) where m.name = "%s" and n.name = "%s" create (m)-[:%s{name:"%s"}]->(n)' %(start_type, end_type, start_name, end_name,rel_type,rel_name)
            try:
                self.g.run(sql)
            except Exception as e:
                print(e)
            if count%10 == 0:
                print(count)

        return




if __name__ =='__main__':
    handler = GoodsKg()
    handler.create_graph()



