"""
    和 django 本身关系比较近的函数
    需要依赖 django 环境才能运行
    辅助 view 的函数
    如果都定义在 utils，容易出现 utils 里面导入 models
    models 里面导入 utils 的情况，就会报错
"""

from django.conf import settings
from django.db.models import F
from .models import File, Link, get_media_abspath
import hashlib
import uuid
import os
import re
from hdfs.client import Client
from .taujud import Taujud
from .gen_noisy import gen_noisy
# from pyspark import SparkConf ,SparkContext
# sparkConf = SparkConf().setAppName('Python').setMaster('local')
# sc = SparkContext.getOrCreate(sparkConf)

import jieba

def handle_repetitive_file(file):
    """
        处理同名的或者重复的文件
        file: File object

        通过遍历看是否有重复路径，如果有重复，则返回带序号的 path
    """

    # 同一个用户的重名文件，与 digest 无关
    # if File.objects.filter(owner=file.owner, name=file.name).count() > 1:
    #     base, ext = os.path.splitext(file.name)
    #     file.name = '{}_{}{}'.format(base, file.pk, ext)
    #     file.save()

    Link.add_one(file)

def put_to_hdfs(local_path, hdfs_path):
    client = Client('http://irip5138-System-Product-Name:50070')
    client.upload(hdfs_path, local_path, overwrite=True)
    os.remove(local_path)


def get_from_hdfs(hdfs_path, local_path):
    client = Client('http://irip5138-System-Product-Name:50070')
    client.download(hdfs_path, local_path, overwrite=True)


def read_hdfs_file(filename):
    client = Client('http://irip5138-System-Product-Name:50070')
    lines = []
    with client.read(filename, encoding='utf-8', delimiter='\n') as reader:
        for line in reader:
            #pass
            #print line.strip()
            lines.append(line.strip())
    return lines





def handle_uploaded_files(file, owner, file_kind):
    """
        files: 接收到来自用户上传的一组文件
        owner: 用户的 user 对象
        directory: 用户上传文件时所在的目录

        先给一个随机名字，然后一边接收，一边 hash，
        最后用 hash 值来命名文件
    """
    # import pdb; pdb.set_trace()
    media_dir = get_media_abspath() # 所有文件的绝对路径

    digest = hashlib.sha1()
    temp_filename = os.path.join(media_dir, str(uuid.uuid1())) #　临时文件
    with open(temp_filename, 'wb+') as destination:

        for chunk in file.chunks(chunk_size=1024):
            destination.write(chunk)
            destination.flush()
            digest.update(chunk)

    digest = digest.hexdigest() # hash 对象转字符串
    abspath = os.path.join(media_dir, digest) # 服务器路径，用于储存

    file = File.objects.create( # 返回 file 对象
        name = re.sub(r'[%/]', '_', file.name), # 给用户看的名字，去掉正斜杠和百分号，just in case
                                            # 亲测 mac 下，名字带正斜杠的文件无法被上传
        owner = owner,
        # parent = directory,
        digest = digest,    # 服务器上真正的名字
        # path = directory.path, # 用户路径，用户给用户展示，不包含文件名
        size = file.size,
        kind = file_kind,
    )

    os.rename(temp_filename, abspath)
    hdfs_path = '/user/webdir/' + digest
    put_to_hdfs(abspath, hdfs_path)
    handle_repetitive_file(file)
    return file
    # print(file)
    # print('file name:', file.name)
    # print('file real name: ',file.digest)
    # print('file path: ',file.path)



def handle_uploaded_files_test(files, owner):
    """
        files: 接收到来自用户上传的一组文件
        owner: 用户的 user 对象
        directory: 用户上传文件时所在的目录

        先给一个随机名字，然后一边接收，一边 hash，
        最后用 hash 值来命名文件
    """
    # import pdb; pdb.set_trace()
    media_dir = get_media_abspath() # 所有文件的绝对路径
    ret_dic = {}
    for file in files:

        digest = hashlib.sha1()
        temp_filename = os.path.join(media_dir, str(uuid.uuid1())) #　临时文件
        with open(temp_filename, 'wb+') as destination:

            for chunk in file.chunks(chunk_size=1024):
                destination.write(chunk)
                destination.flush()
                digest.update(chunk)

        digest = digest.hexdigest() # hash 对象转字符串
        abspath = os.path.join(media_dir, digest) # 服务器路径，用于储存
        print(file.name.split('.')[-1])
        file_kind = ''
        if file.name.split('.')[-1] == 'txt':
            file_kind = 'test-up'
        elif file.name.split('.')[-1] == 'pb':
            file_kind = 'test-model'
        file = File.objects.create( # 返回 file 对象
            name = re.sub(r'[%/]', '_', file.name), # 给用户看的名字，去掉正斜杠和百分号，just in case
                                               # 亲测 mac 下，名字带正斜杠的文件无法被上传
            owner = owner,
            # parent = directory,
            digest = digest,    # 服务器上真正的名字
            # path = directory.path, # 用户路径，用户给用户展示，不包含文件名
            size = file.size,
            kind = file_kind,
        )
        # print(file.digest)
        if file_kind == 'test-up':
            ret_dic['test_up_txt'] = file
        elif file_kind == 'test-model':
            ret_dic['test_up_pb'] = file
        os.rename(temp_filename, abspath)
        handle_repetitive_file(file)
    return ret_dic


def set_captcha_to_session(request, captcha_text):
    """
        将 captcha_text 添加到当前用户的 session 中，
        仅在用户 cookies 中不带 sessionid 时创建 session
    """
    sessionid = settings.SESSION_COOKIE_NAME # 默认值就是 sessionid
    key = request.COOKIES.get(sessionid) # sessionid 的值
    if key is None: # 用户没有任何 sessionid
        request.session.create()
        key = request.session.session_key

    request.session[key] = {'captcha': ''.join(captcha_text).lower()}

def get_session_data(request, key):
    """
        根据 request 返回对应的 data dict，如果无法返回 data 则返回 {}
    """
    return request.session.get(key)

def set_session_data(request, key, value):
    """
        为 session 新增键值对
    """
    request.session.update({key: value})
    request.session.modified = True


def augmentation(file, method, input_param):
    file_name = file.name
    file_digist = file.digest
    file_owner = file.owner
    if method == 'train_method1':
        output_file_name, file_len, n1, n2, n3 = augmentation_method1(file_name, file_owner, file_digist, input_param)
        file_kind = 'train_down1'
    elif method == 'train_method2':
        output_file_name, file_len, n1, n2, n3 = augmentation_method2(file_name, file_owner, file_digist, input_param)
        file_kind = 'train_down2'
    # elif method == 'train_method3':
    #     output_file_name = augmentation_method(file_name, file_owner, file_digist)
    #     file_kind = 'train_down3'
    # elif method == 'train_method3':
    #     output_file_name = augmentation_method(file_name, file_owner, file_digist)
    #     file_kind = 'train_down3'

    output_file_data = handle_output_files(output_file_name, file_owner, file_kind)
    return output_file_data, file_len, n1, n2, n3
    # print('!!!', output_file_data.owner)
    # print(output_file_data.digest)



def augmentation_method1(file_name, file_owner, file_digist, input_param):
    
    file_digist_path = os.path.join("/user/webdir/", file_digist)
    file_path = get_media_abspath()
    output_file_name = str(file_owner) + '_' + str(file_name.split('.')[0]) + '_trainmethod1_outputfile.txt'
    output_file_path = os.path.join(file_path, output_file_name)
    print('output file path: ', output_file_path)
    # output_file = open(output_file_path,'w')

    word_list = read_hdfs_file(file_digist_path)
    file_len = len(word_list)
    # for line in word_list:
    #     output_file.write(line + '\n')
    # output_file.close()
    judical = input_param
    n1, n2, n3 = Taujud(word_list, output_file_path,judical)
    return output_file_name, file_len, n1, n2, n3

def augmentation_method2(file_name, file_owner, file_digist, input_param):
    
    file_digist_path = os.path.join("/user/webdir/", file_digist)
    file_path = get_media_abspath()
    output_file_name = str(file_owner) + '_' + str(file_name.split('.')[0]) + '_trainmethod1_outputfile.txt'
    output_file_path = os.path.join(file_path, output_file_name)
    print('output file path: ', output_file_path)
    # output_file = open(output_file_path,'w')

    word_list = read_hdfs_file(file_digist_path)
    file_len = len(word_list)

    # for line in word_list:
    #     output_file.write(line + '\n')
    # output_file.close()
    gen_list = input_param['check_box_list']
    n1, n2, n3 = gen_noisy(word_list, gen_list, input_param, output_file_path)
    return output_file_name, file_len, n1, n2, n3

def handle_output_files(file_name, owner, file_kind):
    """
        files: 接收到来自用户上传的一组文件
        owner: 用户的 user 对象
        directory: 用户上传文件时所在的目录

        先给一个随机名字，然后一边接收，一边 hash，
        最后用 hash 值来命名文件
    """
    # import pdb; pdb.set_trace()
    media_dir = get_media_abspath() # 所有文件的绝对路径
    # print(file.name)
    # for file in files:
    digest = hashlib.sha1()
    temp_filepath = os.path.join(media_dir, file_name) #　临时文件
    print('temp_filename:',temp_filepath)
    print('temp_file_size:',int(os.path.getsize(temp_filepath)))
    # with open(temp_filepath) as f:
        # print(f.read())

    digest = digest.hexdigest() # hash 对象转字符串
    abspath = os.path.join(media_dir, digest) # 服务器路径，用于储存
    # directory = directory = owner.directory_set.filter(parent=None)[0]
    os.rename(temp_filepath, abspath)

    # with open(abspath) as f:
        # print(f.read())

    file_sql = File.objects.create( # 返回 file 对象
        name = re.sub(r'[%/]', '_', file_name), # 给用户看的名字，去掉正斜杠和百分号，just in case
                                            # 亲测 mac 下，名字带正斜杠的文件无法被上传
        owner = owner,
        # parent = directory,
        digest = digest,    # 服务器上真正的名字
        # path = directory.path, # 用户路径，用户给用户展示，不包含文件名
        size = int(os.path.getsize(abspath)),
        kind = file_kind,
        # size = 0,
    )

    hdfs_path = '/user/webdir/' + digest
    put_to_hdfs(abspath, hdfs_path)

    handle_repetitive_file(file_sql)
    return file_sql






