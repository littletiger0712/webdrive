from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import F

from .utils import get_captcha_text, get_captcha_image
from .handles import (handle_uploaded_files, set_captcha_to_session,
                      get_session_data, set_session_data,augmentation, handle_uploaded_files_test, get_from_hdfs)
from .forms import (LoginForm, SignupForm, UploadForm, 
                    EditForm, CreateDirectoryForm, ConfirmForm, TrainUploadForm, UploadForm_model)
from .models import  File, Link, get_media_abspath

import mimetypes
from io import BytesIO
from urllib.parse import quote
import os
import json
import copy
import time

# you need 'brew install libmagic' under Mac OS
# import magic

"""
    根目录用 '' 表示，以去除 URL 中多余的 / 符号
"""

def test(request):
    """ 专门用于测试的页面 """
    return HttpResponse('<h1>Test successful.</h1>')


# 这里的参数直接相当于用来 reverse 了，就不要再在 login_url 里用 reverse了
@login_required
def index(request):
    """
        用户登录后，直接进入自己的根目录 root_dir
        然后将用户当前目录写入 session data。
        每次访问 index 更改目录时，session data 随之改变
    """
    user = request.user
    # print('request.user:',request.user)
    form = UploadForm()
    # try:
    #     directory = user.directory_set.filter(parent=None)[0] # 根目录
    # except IndexError: # 没有根目录要创建一个
    #     directory = Directory.create_root_dir(user)
    # set_session_data(request, 'directory', directory.pk)
    context = {'user': user, 'form': form}
    # context = {'user': user, 'form': form, 'directory': directory}
    return render(request, 'myapp/index.html', context=context)




def login(request):
    
    next_url = request.GET.get('next', reverse('myapp:index'))
    key = request.session.session_key
    try:
        real_captcha = request.session[key].get('captcha')
    except KeyError:
        real_captcha = ''

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            captcha = form.cleaned_data['captcha'].lower()

            # 判断验证码是否正确
            if real_captcha == captcha:
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    return redirect(next_url)
                # 密码错误
                else:
                    form.add_error('password', ValidationError('您的密码输入错误'))

            # 验证码错误
            else:
                form.add_error('captcha', ValidationError('您的验证码输入错误')) # 参数含义： field 和 错误类型

    elif request.method == 'GET':
        form = LoginForm()
        
    return render(request, 'myapp/login.html', {'form': form})


def logout(request):
    auth.logout(request)
    return redirect('myapp:login')


def signup(request):
    """
        用户注册后，产生一个根目录文件 root_dir 其值为用户名
    """
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # 这里直接返回 User 对象，并保存了用户
            # 并且 user.is_authenticated == True
            user = form.save()
            auth.login(request, user)

            # Directory.create_root_dir(user)

            return redirect('myapp:index')
    else:
        form = SignupForm()
    return render(request, 'myapp/signup.html', {'form': form})


def captcha(request):
    """ 
        验证码保存在 session 数据中，如果随意产生 session，会使得用户退出登录
        因此，需要在 user 的现有 session 中添加，而不是创建 session。
        如果 user 没有带任何 session，那么创建。
    """

    # 自动产生 4 位的验证码，确保是小写
    cap_text = get_captcha_text()
    # 验证码保存到 session 并产生图片
    set_captcha_to_session(request, cap_text)
    cap_img = get_captcha_image(cap_text)
    cap_stream = BytesIO()
    cap_img.save(cap_stream, format='png')
    return HttpResponse(cap_stream.getvalue(), content_type="image/png")




###################
####  文件操作  ####
###################

# @login_required
# def trainupload_origin(request):

#     if request.method == 'POST':
#         owner = request.user
#         # dir_pk = get_session_data(request, 'directory')
#         # directory = Directory.objects.get(pk=dir_pk)

#         form = TrainUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = request.FILES.get('files')
#             # files = request.FILES.getlist('files')
#             file_kind = 'train_up'
#             file_data = handle_uploaded_files(file, owner,file_kind)
#             # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
#             # print('file_data: ', file_data.owner)
#             print('file_data_pk: ',file_data.pk)
#             set_session_data(request, 'file_pk', file_data.pk)
#             return redirect('myapp:train')
#             # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
#     return redirect('myapp:train')





@login_required
def trainupload(request):

    if request.method == 'POST':
        owner = request.user
        
        file = request.FILES.get('file')
        print('!!!!!',file)
        # files = request.FILES.getlist('files')
        file_kind = 'train_up'
        file_data = handle_uploaded_files(file, owner,file_kind)
        # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
        # print('file_data: ', file_data.owner)
        print('file_data_pk: ',file_data.pk)
        set_session_data(request, 'file_pk', file_data.pk)
        return redirect('myapp:train')
        # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
    return redirect('myapp:train')


@login_required
def trainupload_vae(request):

    if request.method == 'POST':
        owner = request.user
        
        file = request.FILES.get('file')
        print('!!!!!',file)
        # files = request.FILES.getlist('files')
        file_kind = 'train_vae_up'
        file_data = handle_uploaded_files(file, owner,file_kind)
        # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
        # print('file_data: ', file_data.owner)
        print('file_data_pk: ',file_data.pk)
        set_session_data(request, 'file_pk', file_data.pk)
        return redirect('myapp:train-vae')
        # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
    return redirect('myapp:train-vae')


@login_required
def testupload_noisy(request):

    if request.method == 'POST':
        owner = request.user
        
        file = request.FILES.get('file')
        print('!!!!!',file)
        # files = request.FILES.getlist('files')
        file_kind = 'test_noisy_up'
        file_data = handle_uploaded_files(file, owner,file_kind)
        # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
        # print('file_data: ', file_data.owner)
        print('file_data_pk: ',file_data.pk)
        set_session_data(request, 'file_pk', file_data.pk)
        return redirect('myapp:test-noisy')
        # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
    return redirect('myapp:test-noisy')




@login_required
def trainupload_vae(request):

    if request.method == 'POST':
        owner = request.user
        
        file = request.FILES.get('file')
        file_valid = request.FILES.get('file-valid')
        file_test = request.FILES.get('file-test')
        print('!!!!!',file)
        print('!!!!!',file_valid)
        print('!!!!!',file_test)
        # files = request.FILES.getlist('files')
        file_kind = 'train_vae_up'
        file_data = handle_uploaded_files(file, owner,file_kind)
        # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
        # print('file_data: ', file_data.owner)
        print('file_data_pk: ',file_data.pk)
        set_session_data(request, 'file_pk', file_data.pk)
        set_session_data(request, 'file-valid', file_valid.name)
        set_session_data(request, 'file-test', file_test.name)
        return redirect('myapp:train-vae')
        # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
    return redirect('myapp:train-vae')



@login_required
def testupload_attack(request):

    if request.method == 'POST':
        owner = request.user
        
        file = request.FILES.get('file')
        file_model = request.FILES.get('file-model')
        file_vocab = request.FILES.get('file-vocab')
        print('!!!!!',file)
        print('!!!!!',file_model)
        print('!!!!!',file_vocab)
        # files = request.FILES.getlist('files')
        file_kind = 'test_attack_up'
        file_data = handle_uploaded_files(file, owner,file_kind)
        # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
        # print('file_data: ', file_data.owner)
        print('file_data_pk: ',file_data.pk)
        set_session_data(request, 'file_pk', file_data.pk)
        set_session_data(request, 'file-model', file_model.name)
        set_session_data(request, 'file-vocab', file_vocab.name)
        return redirect('myapp:test-attack')
        # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
    return redirect('myapp:test-attack')

# def trainupload2(request):

#     if request.method == 'POST':
#         owner = request.user
#         # dir_pk = get_session_data(request, 'directory')
#         # directory = Directory.objects.get(pk=dir_pk)

#         form = TrainUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = request.FILES.get('files')
#             # files = request.FILES.getlist('files')
#             file_kind = 'train_up'
#             file_data = handle_uploaded_files(file, owner,file_kind)
#             # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
#             # print('file_data: ', file_data.owner)
#             print('file_data_pk: ',file_data.pk)
#             set_session_data(request, 'file_pk', file_data.pk)
#             return redirect('myapp:test')
#             # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
#     return redirect('myapp:test')


# @login_required
# def testupload(request):

#     if request.method == 'POST':
#         owner = request.user
#         # dir_pk = get_session_data(request, 'directory')
#         # directory = Directory.objects.get(pk=dir_pk)

#         form = UploadForm_model(request.POST, request.FILES)
#         if form.is_valid():
#             file = request.FILES.getlist('files')
#             # files = request.FILES.getlist('files')
#             # file_kind = 'test_up'
#             file_data_list = handle_uploaded_files_test(file, owner)
#             # file_data_dic = {'file_owner':file_data.owner, 'file_digest':file_data.digest}
#             # print('file_data: ', file_data.owner)
#             # print('file_data_pk: ',file_data.pk)
#             set_session_data(request, 'test_up_txt_pk', file_data_list['test_up_txt'].pk)
#             set_session_data(request, 'test_up_pb_pk', file_data_list['test_up_pb'].pk)
#             print("request.session:",request.session.items())
#             return redirect('myapp:test')
#             # return redirect('myapp:detail', username=owner.username, path=directory.path)
        
#     return redirect('myapp:test')



@login_required
def download(request, pk):
    """ 一般是下载，当附带 preview=True query string 时为预览 """    

    file = get_object_or_404(File, pk=pk)
    hdfs_path = file.get_full_path_hdfs()
    get_from_hdfs(hdfs_path, file.get_full_path())
    buf = open(file.get_full_path(), 'rb')
    response = HttpResponse(buf)   
    response['Content-Length'] = str(file.size)

    if request.GET.get('preview'):
        filetype = mimetypes.guess_type(file.name)[0]
        if not filetype:
           filetype = 'application/octet-stream'   
        response['Content-Type'] = filetype
    else:
        response['Content-Type'] = 'application/force-download'
        response['Content-Disposition'] = 'attachment; filename={}'.format(quote(file.name))
    return response





@login_required
def delete(request, pk):
    """ 提供一个页面，让用户确认 """

    file = get_object_or_404(File, pk=pk)
    # directory = file.parent
    # import pdb; pdb.set_trace()
    # if request.method == 'POST':
    Link.minus_one(file) # 里面包含了删除动作
    return redirect('myapp:personal_view')
    # return redirect(request, 'myapp/personal-page.html')


@login_required
def train_view(request):
    """
        训练数据生成页面展示函数
    """
    user = request.user
    file_pk = get_session_data(request, 'file_pk')
    print('file_pk',file_pk)
    if not file_pk:
        return render(request, 'myapp/train-page-rule.html')
    file = get_object_or_404(File, pk=file_pk)
    return render(request, 'myapp/train-page-rule.html',{'file':file})

@login_required
def train_view_vae(request):
    """
        训练数据生成页面展示函数
    """
    user = request.user
    file_pk = get_session_data(request, 'file_pk')
    file_valid = get_session_data(request, 'file-valid')
    file_test = get_session_data(request, 'file-test')
    print('file_pk',file_pk)
    if not file_pk:
        return render(request, 'myapp/train-page-vae.html')
    file = get_object_or_404(File, pk=file_pk)
    return render(request, 'myapp/train-page-vae.html',{'file':file,'validfile':file_valid,'testfile':file_test})

@login_required
def test_view_noisy(request):
    """
        测试数据生成页面展示函数
    """
    user = request.user
    file_pk = get_session_data(request, 'file_pk')
    if not file_pk:
        return render(request, 'myapp/test-page-noisy.html')
    file = get_object_or_404(File, pk=file_pk)
    return render(request, 'myapp/test-page-noisy.html',{'file':file})





@login_required
def test_view_attack(request):
    """
        测试数据生成页面展示函数
    """
    user = request.user
    file_pk = get_session_data(request, 'file_pk')
    file_model = get_session_data(request, 'file-model')
    file_vocab = get_session_data(request, 'file-vocab')
    if not file_pk:
        return render(request, 'myapp/test-page-attack.html')
    file = get_object_or_404(File, pk=file_pk)
    return render(request, 'myapp/test-page-attack.html',{'file':file,'filemodel':file_model,'filevocab':file_vocab})


@login_required
def trainmethod_rule(request):
    # key = request.session.session_key
    # print('key: ',key)
    file_pk = get_session_data(request, 'file_pk')
    file = get_object_or_404(File, pk=file_pk)
    jud_param = get_session_data(request,'jud_param')
    output_file, file_len, n1, n2, n3 = augmentation(file, 'train_method1',jud_param)
    # set_session_data(request, 'file_pk', output_file.pk)
    # return redirect('myapp:download',pk=output_file.pk)
    file_len_all = file_len*(n1+n2+n3)
    context = {'file_len_input': file_len, 'file_len_all':file_len_all, 'file_len_1': n1*file_len, 'file_len_2': n2*file_len, 'file_len_3': n3*file_len, 'file':output_file, 'method':'train_method1'}
    # return render(request, 'myapp/train-detail.html', context=context)
    return render(request,'myapp/show_data.html',context=context)
    # return redirect('myapp:show-table2')



@login_required
def trainmethod_vae(request):
    
    return render(request,'myapp/show_data_vae.html')
    



@login_required
def testmethod_noisy(request):
    # key = request.session.session_key
    # print('key: ',key)
    file_pk = get_session_data(request, 'file_pk')
    file = get_object_or_404(File, pk=file_pk)
    test_param = get_session_data(request,'test_param')
    output_file , file_len, n1, n2, n3 = augmentation(file, 'train_method2', test_param)
    # set_session_data(request, 'file_pk', output_file.pk)
    # return redirect('myapp:download',pk=output_file.pk)
    # return render(request, 'myapp/train-page.html')
    file_len_all = file_len*(n1+n2+n3)
    context = {'file_len_input': file_len, 'file_len_all':file_len_all, 'file_len_1': n1*file_len, 'file_len_2': n2*file_len, 'file_len_3': n3*file_len, 'file':output_file, 'method':'train_method2'}
    # return render(request, 'myapp/train-detail.html', context=context)
    return render(request,'myapp/show_data.html',context=context)
    


@login_required
def testmethod_attack(request):
    time.sleep(5)
    media_dir = get_media_abspath() # 所有文件的绝对路径
    show_json_file_name = 'show_attack_1000.json'
    abspath = os.path.join(media_dir, show_json_file_name)
    with open(abspath,'r',encoding='UTF-8') as f:
        load_dict = json.load(f)
    context = {}
    context['avg_change'] = float(load_dict['avg_change'])*100
    context['duikang_sucsess'] = load_dict['duikang_sucsess']
    context['input_num'] = load_dict['input_num']
    return render(request,'myapp/show_data_attack.html',context=context)




@login_required
def personal_view(request):
    # key = request.session.session_key
    # print('key: ',key)
    user = request.user 
    file_list = File.objects.filter(owner=user)
    ret_list = []
    for file in file_list:
        tmp_dic = {}
        tmp_dic['name'] = file.name
        tmp_dic['size'] = file.get_size()
        tmp_dic['kind'] = file.kind
        tmp_dic['datetime'] = file.datetime
        tmp_dic['pk'] = file.pk
        ret_list.append(tmp_dic)
    return render(request, 'myapp/personal-page-aaaa.html',{'file_data':ret_list})




@login_required
def check_train(request):
    if request.method=="POST":
        param_dict = request.POST.dict()
        print(param_dict)
        # return HttpResponse("aaa")        
        check_box_list = []
        if 'checkbox1' in param_dict:
            check_box_list.append('blind')
        if 'checkbox2' in param_dict:
            check_box_list.append('cf')
        if 'checkbox3' in param_dict:
            check_box_list.append('sys')
        jud_param = {}
        jud_param['check_box_list'] = check_box_list
        jud_param['cf_beishu'] = str(int(param_dict['cf_beishu'])+1)
        jud_param['sys_beishu'] = str(int(param_dict['sys_beishu'])+1)
        if check_box_list:
            print(check_box_list)
            set_session_data(request, 'jud_param', jud_param)
            return redirect('myapp:trainmethod-rule')
        else:
            print("fail")
            return HttpResponse("fail")
    

@login_required
def check_train_vae(request):
    # if request.method=="POST":
    param_dict = request.POST.dict()
    print('!!!!!!!!!!!!1111',param_dict) 
    return render(request, 'myapp/vae-table.html')
    # else:
    #     print("fail")
    #     return HttpResponse("fail")



@login_required
def check_test_noisy(request):
    if request.method=="POST":
        param_dict = request.POST.dict()
        print(param_dict)
        # return HttpResponse("aaa") 
        test_param = {}
        check_box_list = []
        if 'checkbox1' in param_dict:
            check_box_list.append('luanxu')
        if 'checkbox2' in param_dict:
            check_box_list.append('queshi')
        if 'checkbox3' in param_dict:
            check_box_list.append('rongyu')
        test_param['check_box_list'] = check_box_list        
        test_param['luanxu_beishu'] = str(int(param_dict['luanxu_beishu'])+1)
        test_param['queshi_beishu'] = str(int(param_dict['queshi_beishu'])+1)
        test_param['rongyu_beishu'] = str(int(param_dict['rongyu_beishu'])+1)
        test_param['radio1'] = str(float(param_dict['luanxu_bili'])*0.05)
        test_param['radio2'] = str(float(param_dict['queshi_bili'])*0.05)
        test_param['radio3'] = str(float(param_dict['rongyu_bili'])*0.05)

        print(test_param)

        if check_box_list:
            print(check_box_list)
            set_session_data(request, 'test_param', test_param)
            return redirect('myapp:testmethod-noisy')
        else:
            print("fail")
            return HttpResponse("fail")

@login_required
def check_test_attack(request):
    if request.method=="POST":
        param_dict = request.POST.dict()
        print(param_dict)
        return redirect('myapp:testmethod-attack')




def show_table(request):
    if request.method == 'GET':
        # load_dict = [{"id":0,"name":"被告人杜天禹通过植入木马程序的方式，非法侵入山东省2016年普通高等学校招生考试信息平台网站，取得该网站管理权，非法获取2016年山东省高考考生个人信息64万余条，并向另案被告人陈文辉出售上述信息10万余条，非法获利14 100元，陈文辉利用从杜天禹处购得的上述信息，组织多人实施电信诈骗犯罪，拨打诈骗电话共计1万余次，骗取他人钱款20余万元，并造成高考考生徐玉玉死亡。","content":"aaaa"},{"id":1,"name":"qqqq","content":"aaaaaa"}]
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if 'name' in line and line['name'] != '':
                ret_dict.append(line)
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')


def show_child_table1(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        print(id)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if line['id'] == int(id):
                # print(line)
                if 'content' in line:
                    tmp_dict = {'content':line['content']}               
                    ret_dict.append(copy.deepcopy(tmp_dict))
        # print('ret_dict:',ret_dict)
        # load_dict = [{'content2':'111'},{'content2':'222'}]
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')

def show_child_table2(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        print(id)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if line['id'] == int(id):
                # print(line)
                if 'content2' in line:
                    tmp_dict = {'content2':line['content2']}               
                    ret_dict.append(copy.deepcopy(tmp_dict))
        # print('ret_dict:',ret_dict)
        # load_dict = [{'content2':'111'},{'content2':'222'}]
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')

def show_child_table3(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        print(id)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if line['id'] == int(id):
                # print(line)
                if 'content3' in line:
                    tmp_dict = {'content3':line['content3']}               
                    ret_dict.append(copy.deepcopy(tmp_dict))
        # print('ret_dict:',ret_dict)
        # load_dict = [{'content2':'111'},{'content2':'222'}]
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')    



def show_table_attack(request):
    if request.method == 'GET':
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show_attack_1000.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if 'name' in line and line['name'] != '':
                ret_dict.append(line)
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')

def show_child_table_attack(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        print(id)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'show_attack_1000.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        load_dict = load_dict['a']
        ret_dict = []
        for line in load_dict:
            if line['id'] == int(id):
                # print(line)
                if 'content' in line:
                    tmp_dict = {'content':line['content'],'adv_label':line['adv_label'],'change_num':line['change_num']}             
                    ret_dict.append(copy.deepcopy(tmp_dict))
        # print('ret_dict:',ret_dict)
        # load_dict = [{'content2':'111'},{'content2':'222'}]
        return HttpResponse(json.dumps(ret_dict), content_type='application/json')  


def show_table_vae_table(request):
    if request.method == 'GET':
        # load_dict = [{"data":'a.train.txt,a.valid.txt,a.test.txt',"name":"model_a.bin","num":'22015','ppl':'---','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'b.train.txt,b.valid.txt,b.test.txt',"name":"model_b.bin","num":'22015','ppl':'10.69','time':"2020-3-26 15:58:23","process":"训练完成"},{"data":'c.train.txt,c.test.txt,c.test.txt',"name":"model_c.bin","num":'22015','ppl':'11.34','time':"2020-3-26 14:34:12","process":"训练完成"}]

        load_dict = [{"data":'judical.train.txt,judical.valid.txt,judical.test.txt',"name":"model_judical_2.bin","num":'22015','ppl':'---','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'judical.train.txt,judical.valid.txt,judical.test.txt',"name":"model_judical.bin","num":'22015','ppl':'10.69','time':"2020-3-26 15:58:23","process":"训练完成"},{"data":'tau.train.txt,tau.valid.txt,tau.test.txt',"name":"model_tau.bin","num":'13489','ppl':'11.34','time':"2020-3-26 14:34:12","process":"训练完成"}]
        
        # media_dir = get_media_abspath() # 所有文件的绝对路径
        # show_json_file_name = 'show.json'
        # abspath = os.path.join(media_dir, show_json_file_name)
        # with open(abspath,'r',encoding='UTF-8') as f:
        #     load_dict = json.load(f)
        # load_dict = load_dict['a']
        # ret_dict = []
        # for line in load_dict:
        #     if 'name' in line and line['name'] != '':
        #         ret_dict.append(line)
        return HttpResponse(json.dumps(load_dict), content_type='application/json')



def show_table_vae_class0(request):
    if request.method == 'GET':
        # load_dict = [{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"训练完成"}]
        # print(request.GET)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'a.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        # ret_dict = []
        # for line in load_dict:
        #     if 'name' in line and line['name'] != '':
        #         ret_dict.append(line)
        return HttpResponse(json.dumps(load_dict), content_type='application/json') 

def show_table_vae_class1(request):
    if request.method == 'GET':
        # load_dict = [{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"训练完成"}]
        # print(request.GET)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'b.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        # ret_dict = []
        # for line in load_dict:
        #     if 'name' in line and line['name'] != '':
        #         ret_dict.append(line)
        return HttpResponse(json.dumps(load_dict), content_type='application/json') 

def show_table_vae_class2(request):
    if request.method == 'GET':
        # load_dict = [{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"训练完成"}]
        # print(request.GET)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'c.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        # ret_dict = []
        # for line in load_dict:
        #     if 'name' in line and line['name'] != '':
        #         ret_dict.append(line)
        return HttpResponse(json.dumps(load_dict), content_type='application/json') 

def show_table_vae_class3(request):
    if request.method == 'GET':
        # load_dict = [{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"正在训练"},{"data":'a.txt',"name":"model.bin","loss":'230','ppl':'20','time':"2020-3-26 15:58:23","process":"训练完成"}]
        # print(request.GET)
        media_dir = get_media_abspath() # 所有文件的绝对路径
        show_json_file_name = 'd.json'
        abspath = os.path.join(media_dir, show_json_file_name)
        with open(abspath,'r',encoding='UTF-8') as f:
            load_dict = json.load(f)
        # ret_dict = []
        # for line in load_dict:
        #     if 'name' in line and line['name'] != '':
        #         ret_dict.append(line)
        return HttpResponse(json.dumps(load_dict), content_type='application/json') 



def generate_vae_text(request):
    return render(request, 'myapp/generate-vae-text.html') 