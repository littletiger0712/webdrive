import jieba
import random
from .models import get_media_abspath
import os
import copy
import json


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



def gen_noisy(line_list, gen_list, param, output_name):

    print('gen_list:',gen_list)
    cut_list = []
    for line in line_list:
        tmp_list = line.split('__label__')
        cut = list(jieba.cut(tmp_list[0]))
        if len(tmp_list) > 1:
            label = line.split('__label__')[1]
        else:
            label = '0'
        cut_list.append([cut, label])
    
    media_dir = get_media_abspath() # 所有文件的绝对路径
    show_json_file_name = 'show.json'
    abspath = os.path.join(media_dir, show_json_file_name) # 服务器路径，用于储存
    vocabs, weight = json.load(open(os.path.join(media_dir, 'data_vocab.json')))


    show_json_list = []

    tmp_dict = {}

    for i in range(len(line_list)):
        tmp_dict['id'] = i
        tmp_dict['name'] = line_list[i]
        show_json_list.append(copy.deepcopy(tmp_dict))



    if 'luanxu' in gen_list:
        write_file(output_name, '--------------------------------------------')
        for i in range(int(param['luanxu_beishu'])):
            random_percent = float(param['radio1'])
            cnt = 0
            tmp_dict = {}
            for line, label in cut_list:
                # print(line)
                random_cnt = int(random_percent*len(line))
                for j in range(random_cnt):
                    tmp_num = random.randint(0,len(line)-2)
                    line[tmp_num], line[tmp_num+1] = line[tmp_num+1], line[tmp_num]
                label_str = '__label__' + label
                write_str = ''.join(line) + label_str
                write_file(output_name, write_str)

                tmp_dict['id'] = cnt
                # tmp_dict['name'] = line
                tmp_dict['content'] = write_str
                # print(tmp_dict)
                show_json_list.append(copy.deepcopy(tmp_dict))
                cnt += 1



    if 'queshi' in gen_list:
        write_file(output_name, '--------------------------------------------')
        for i in range(int(param['queshi_beishu'])):
            random_percent = float(param['radio2'])
            cnt = 0
            tmp_dict = {}
            for line, label in cut_list:
                random_cnt = int(random_percent*len(line))
                for j in range(random_cnt):
                    tmp_num = random.randint(0,len(line)-2)
                    line = line[:tmp_num] + line[tmp_num+2:]
                label_str = '__label__' + label
                write_str = ''.join(line) + label_str
                write_file(output_name, write_str)

                tmp_dict['id'] = cnt
                # tmp_dict['name'] = line
                tmp_dict['content2'] = write_str
                show_json_list.append(copy.deepcopy(tmp_dict))
                cnt += 1


    if 'rongyu' in gen_list:
        write_file(output_name, '--------------------------------------------')
        for i in range(int(param['rongyu_beishu'])):
            random_percent = float(param['radio3'])
            cnt = 0
            tmp_dict = {}
            for line, label in cut_list:        
                random_cnt = int(random_percent*len(line))
                for j in range(random_cnt):

                    # tmp_num = random.randint(0,len(line)-1)
                    # line = line[:tmp_num] + line[tmp_num:] 
                    tmp_num = random.randint(0,len(line)-1)
                    words = random.choices(vocabs, weights=weight)
                    line = line[:tmp_num] + words + line[tmp_num+1:] 


                label_str = '__label__' + label
                write_str = ''.join(line) + label_str
                write_file(output_name, write_str)

                tmp_dict['id'] = cnt
                # tmp_dict['name'] = line
                tmp_dict['content3'] = write_str
                show_json_list.append(copy.deepcopy(tmp_dict))
                cnt += 1

    # print(show_json_list)
    show_json = {'a':show_json_list}
    write_json_file(abspath,show_json)
    return int(param['luanxu_beishu']), int(param['queshi_beishu']), int(param['rongyu_beishu'])


# input = open('tau.txt','r')
# line_list = []
# for line in input:
#     line_list.append(line.strip()) 
# gen_list = {'lack','rongyu','luanxu'}
# param = {'radio1':0.2,'radio2':0.3,'radio3':0.4}
# gen_noisy(line_list, gen_list, param, 'a.txt')


