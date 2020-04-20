# -*- coding: utf-8 -*-
import pickle
import json
import re
import sqlite3
import jieba.posseg as pseg
import random
class JudicialAug:
    def __init__(self, doc):
        print('start JudicialAug...')
        self.doc = doc
        self.name = ["赵某", "钱某", "孙某", "李某", "周某", "吴某", "郑某", "王某", "章某", "朱某", "刘某", "陈某", "冯某", "陈某", "胡某", "卫某", "蒋某", "沈某", "韩某", "杨某", "郭某"]
        self.color = ["黑色", "白色", "红色", "绿色", "黄色", "蓝色", "灰色", "紫色", "橙色", '青色']
        self.company = ["科技股份有限公司", "网络股份有限公司", "制冷设备股份有限公司", "泵业股份有限公司", "珠宝股份有限公司"]
        self.time = [str(i)+'年' for i in range(1990, 2019)]
        self.old_province = ''
        self.new_province = ''
        self.old_color = ''
        self.new_color = ''
        self.old_time = ''
        self.new_time = ''

        # self.readFile_path = "test.json"
        # self.writeFile_path = "augmentation.json"
        conn = sqlite3.connect('/home/lw/workspace/zs/webdrive/myapp/dist/data.sqlite')
        self.cursor = conn.cursor()
        sql_city = 'select name from city'
        sql_province = 'select name from province'
        sql_county = 'select name from area'
        self.cursor.execute(sql_city)
        lst = self.cursor.fetchall()
        self.city = [i[0] for i in lst]
        self.cursor.execute(sql_province)
        lst = self.cursor.fetchall()
        self.province = [i[0] for i in lst]
        self.cursor.execute(sql_county)
        lst = self.cursor.fetchall()
        self.county = [i[0] for i in lst]

        with open("/home/lw/workspace/zs/webdrive/myapp/dist/sysnonyms.pickle", 'rb')as f:
            self.sysnonyms = pickle.load(f)
        with open("/home/lw/workspace/zs/webdrive/myapp/dist/sysnonyms_2.pickle", 'rb')as f:
            self.sysnonyms_2 = pickle.load(f)

        stop = open('/home/lw/workspace/zs/webdrive/myapp/dist/stop_words.txt', 'r+', encoding='utf-8')
        self.stopwords = stop.read().split("\n")


    def synon_aug_word(self, word):

        if word in self.sysnonyms:
            return self.sysnonyms[word]
        elif word in self.sysnonyms_2:
            return self.sysnonyms_2[word]
        else:
            return word

    def synon_aug(self):
        fact = self.doc
        words = pseg.cut(fact)
        new_fact = ""
        for word, flag in words:
           sy_word = self.synon_aug_word(word)
           new_fact += sy_word
        fact = new_fact
        self.doc = fact
        return fact


    # def write_json_file(self, doc):
    #     with open(self.writeFile_path, 'a', encoding='utf-8')as fw:
    #         json.dump(doc, fw, ensure_ascii=False)
    #         fw.write("\n")
    #     fw.close()


    def counterfactural_aug(self):
        fact = self.doc
        pattern = re.compile(r'[^陈][某姓]')
        fact = re.sub(pattern, self.name[random.randint(0, self.name.__len__() - 1)], fact)
        pattern = re.compile(r'[^脸]色')

        s = pattern.search(fact)
        if s:
            self.old_colors = s.group()
            self.new_color = random.choice(self.color)
            fact = re.sub(pattern, self.new_color, fact)
        pattern = re.compile(r'股份有限公司')

        fact = re.sub(pattern, self.company[random.randint(0, self.company.__len__() - 1)], fact)
        words = pseg.cut(fact)
        new_fact = ""
        cflag = 0
        for word, flag in words:
            # word = self.synon_aug(word)
            if word in self.stopwords:
                word = ""
            if flag in ['ns', 'nr']:
                if "县" in word or "区" in word and cflag == 0:

                    sql = 'select area.name, city.name, province.name from area ' \
                          'join city ON area.cityCode = city.code ' \
                          'join province ON area.provinceCode = province.code where area.name="%s";' % word
                    self.cursor.execute(sql)
                    self.old_province = self.cursor.fetchall()
                    word = self.county[random.randint(0, self.county.__len__() - 1)]
                    self.new_province = random.choice(self.province)
                    cflag = 1
                elif "市" in word:
                    sql = 'select city.name, province.name from city ' \
                          'join province ON city.provinceCode = province.code where city.name="%s";' % word
                    self.cursor.execute(sql)
                    self.old_province = self.cursor.fetchall()
                    if not self.old_province:
                        sql = 'select area.name, city.name, province.name from area ' \
                              'join city ON area.cityCode = city.code ' \
                              'join province ON area.provinceCode = province.code where area.name="%s";' % word
                        self.cursor.execute(sql)
                        self.old_province = self.cursor.fetchall()
                    if not self.old_province:
                        self.old_province = [(word)]
                    word = self.city[random.randint(0, self.city.__len__() - 1)]
                    self.new_province = random.choice(self.province)
                    cflag = 1
                elif "省" in word:
                    self.old_province = [(word)]
                    word = self.province[random.randint(0, self.province.__len__() - 1)]
                    self.new_province = random.choice(self.province)
                    cflag = 1
                #
                #
                # if "市" in word:
                #    word = self.city[random.randint(0, self.city.__len__() - 1)]
                # elif "省" in word:
                #    word = self.province[random.randint(0, self.province.__len__() - 1)]
                # elif "县" in word:
                #    word = self.county[random.randint(0, self.county.__len__() - 1)]
            new_fact += word
        fact = new_fact
        pattern = re.compile(r'([1,2]\d{3})年')

        s = pattern.search(fact)
        if s:
            self.old_time = s.group()
            self.new_time = random.choice(self.time)
            fact = re.sub(pattern, self.new_time, fact)
        # s = self.sex_token(fact)
        self.doc = fact
        return fact

    def blind_aug(self):
        fact = self.doc
        pattern = re.compile(r'[^陈][某某姓]')
        fact = re.sub(pattern, "name", fact)
        pattern = re.compile(r'[^脸]色')
        fact = re.sub(pattern, "color", fact)
        pattern = re.compile(r'股份有限公司')
        fact = re.sub(pattern, "company", fact)
        words = pseg.cut(fact)
        new_fact = ""
        for word, flag in words:
           if flag == 'ns':
               if "市" in word:
                   word = "city"
               elif "省" in word:
                   word = "province"
               elif "县" in word:
                   word = "county"
           new_fact += word
        fact = new_fact
        pattern = re.compile(r'([1,2]\d{3})年')
        fact = re.sub(pattern, random.choice(self.time), fact)
        self.doc = fact
        return fact

    def get_attributes(self):
        return self.old_color, self.new_color, self.old_province, self.new_province, self.old_time, self.new_time
# s = input()
# u = JudicialAug(s)
# print(u.blind_aug())
