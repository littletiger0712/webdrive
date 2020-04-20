# -*- coding: utf-8 -*-
import argparse
import json
import os
import sqlite3
from .judicial_augmentation import JudicialAug
# from universal_augmentation import UniversalAug
from .models import get_media_abspath
import copy


def read_json_file(input, doc):
    with open(input, 'a', encoding='utf-8')as fw:
        json.dump(doc, fw, ensure_ascii=False)
        fw.write("\n")
    fw.close()


def write_file(output, doc):
    with open(output, 'a', encoding='utf-8')as fw:
        # json.dump(doc, fw, ensure_ascii=False)
        fw.write(doc + "\n")
    fw.close()

def write_json_file(output, doc):
    with open(output, 'w', encoding='utf-8')as fw:
        json.dump(doc, fw, ensure_ascii=False)
        # fw.write(doc)
    fw.close()


def Taujud(word_list, output, judicial):
    # parser = argparse.ArgumentParser(description='TauJud -- Test Augmentation Tool of Machine Learning in Judicial Documents')

    # parser.add_argument('-i', '--input', dest='input', help="input filename")
    # parser.add_argument('-o', '--output', dest='output', help='output filename')
    # parser.add_argument('-jud', '--judicial', choices = ['blind', 'cf', 'sysnonyms'], dest='judicial', help='judicial augmentation')
    # parser.add_argument('-uni', '--universal', choices = ['backtrans', 'stopworddel'], dest='universal', help='universal augmentation')
    # parser.add_argument('-c', '--clipping', action="store_true", help='clipping documents pattern')
    # args = parser.parse_args()
    # print(args)
    blind_n = 1
    cf_n = 1
    sysnonyms_n = 1
    name = ["赵某", "钱某", "孙某", "李某", "周某", "吴某", "郑某", "王某", "章某", "朱某", "刘某", "陈某", "冯某", "陈某", "胡某", "卫某", "蒋某",
                 "沈某", "韩某", "杨某", "郭某"]
    color = ["黑色", "白色", "红色", "绿色", "黄色", "蓝色", "灰色", "紫色", "橙色", '青色']
    company = ["科技股份有限公司", "网络股份有限公司", "制冷设备股份有限公司", "泵业股份有限公司", "珠宝股份有限公司"]
    time = [str(i) + '年' for i in range(1990, 2019)]
    conn = sqlite3.connect('/home/lw/workspace/zs/webdrive/myapp/dist/data.sqlite')
    cursor = conn.cursor()
    sql_province = 'select name from province'
    cursor.execute(sql_province)
    lst = cursor.fetchall()
    province = [i[0] for i in lst]
    print("creating dicts...")
    color_dict = {}
    province_dict = {}
    time_dict = {}
    for i in color:
        color_dict[i] = [0, 0]
    for i in province:
        province_dict[i] = [0, 0]
    for i in time:
        time_dict[i] = [0, 0]

    print("counting...")

    jud_kind = judicial['check_box_list']
    cf_beishu = int(judicial['cf_beishu'])
    sys_beishu = int(judicial['sys_beishu'])

    media_dir = get_media_abspath() # 所有文件的绝对路径
    show_json_file_name = 'show.json'
    abspath = os.path.join(media_dir, show_json_file_name) # 服务器路径，用于储存

    show_json_list = []

    tmp_dict = {}
    for i in range(len(word_list)):
        tmp_dict['id'] = i
        tmp_dict['name'] = word_list[i]
        show_json_list.append(copy.deepcopy(tmp_dict))


    if 'blind' in jud_kind:
        write_file(output, '------------------------------------')
        cnt = 0
        tmp_dict = {}

        for line in word_list:
            fact = line.strip()
            jud = JudicialAug(fact)
            fact = jud.blind_aug()
            write_file(output, fact)

            tmp_dict['id'] = cnt
            # tmp_dict['name'] = line
            tmp_dict['content'] = fact
            show_json_list.append(copy.deepcopy(tmp_dict))
            # blind_n += 1
            cnt += 1

    if 'cf' in jud_kind:
        write_file(output, '------------------------------------')

        for i in range(cf_beishu):
            cnt = 0
            tmp_dict = {}

            for line in word_list:
                fact = line.strip()
                jud = JudicialAug(fact)
                fact = jud.counterfactural_aug()
                write_file(output, fact)

                tmp_dict['id'] = cnt
                tmp_dict['content2'] = fact
                show_json_list.append(copy.deepcopy(tmp_dict))

                # cf_n += 1
                cnt += 1

    if 'sys' in jud_kind:
        write_file(output, '------------------------------------')
        for i in range(sys_beishu):
            cnt = 0
            tmp_dict = {}

            for line in word_list:
                fact = line.strip()
                jud = JudicialAug(fact)
                fact = jud.synon_aug()
                write_file(output, fact)

                tmp_dict['id'] = cnt
                tmp_dict['content3'] = fact
                show_json_list.append(copy.deepcopy(tmp_dict))

                # sysnonyms_n += 1
                cnt += 1

    print(show_json_list)
    show_json = {'a':show_json_list}
    write_json_file(abspath,show_json)
    return 1, cf_beishu, sys_beishu

    




    # for line in word_list:
    #     # r = json.loads(line)
    #     fact = line.strip()

    #     if judicial != None:
    #         jud = JudicialAug(fact)
    #         if 'blind' in judicial:
    #             fact = jud.blind_aug()

    #         if 'cf' in judicial:
    #             fact = jud.counterfactural_aug()
    #             old_color, new_color, old_province, new_province, old_time, new_time = jud.get_attributes()
    #             if old_color in color_dict.keys():
    #                 color_dict[old_color][0] += 1
    #             try:
    #                 if old_province[0][-1] in province_dict.keys():
    #                     province_dict[old_province[0][-1]][0] += 1
    #             except:
    #                 print(old_province)
    #             if old_time in time_dict.keys():
    #                 time_dict[old_time][0] += 1

    #             if new_color in color_dict.keys():
    #                 color_dict[new_color][1] += 1
    #             if new_province in province_dict.keys():
    #                 province_dict[new_province][1] += 1
    #             if new_time in time_dict.keys():
    #                 time_dict[new_time][1] += 1
    #     # print(fact)
    #     # r['fact'] = fact
    #     write_json_file(output, fact)
    #     print('document',n, fact)
    #     n += 1
    # print('color count:', color_dict)
    # print('province count:', province_dict)
    # print('time count:', time_dict)

