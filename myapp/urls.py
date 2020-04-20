from django.conf.urls import url
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = 'myapp'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^test-noisy/', views.test_view_noisy, name='test-noisy'),
    url(r'^test-attack/', views.test_view_attack, name='test-attack'),

    url(r'^signup/', views.signup, name='signup'),
    url(r'^login/', views.login, name='login'),
    url(r'^logout/', views.logout, name='logout'),
    url(r'^captcha/', views.captcha, name='captcha'), 

    url(r'^train/', views.train_view, name='train'),
    url(r'^train-vae/', views.train_view_vae, name='train-vae'),
    url(r'^trainmethod-rule/', views.trainmethod_rule,name='trainmethod-rule'),
    url(r'^trainmethod-vae/', views.trainmethod_vae,name='trainmethod-vae'),
    url(r'^testmethod-noisy/', views.testmethod_noisy,name='testmethod-noisy'),
    url(r'^testmethod-attack/', views.testmethod_attack,name='testmethod-attack'),
    # url(r'^trainmethod3/', views.trainmethod3,name='trainmethod3'),
    # url(r'^trainmethod4/', views.trainmethod4,name='trainmethod4'),
    url(r'^check-train/', views.check_train, name='check-train'),
    url(r'^check-train-vae/', views.check_train_vae, name='check-train-vae'),
    url(r'^check-test-noisy/', views.check_test_noisy, name='check-test-noisy'),
    url(r'^check-test-attack/', views.check_test_attack, name='check-test-attack'),
    url(r'^personal/',views.personal_view, name='personal_view'),
    
    url(r'^trainupload/', views.trainupload, name='trainupload'),
    url(r'^trainupload-vae/', views.trainupload_vae, name='trainupload-vae'),
    # url(r'^trainupload2/', views.trainupload2, name='trainupload2'),
    # url(r'^testupload/', views.testupload, name='testupload'),
    url(r'^testupload-attack/', views.testupload_attack, name='testupload-attack'),
    url(r'^testupload-noisy/', views.testupload_noisy, name='testupload-noisy'),
    
    # url(r'^testupload2/', views.testupload2, name='testupload2'),
    url(r'^download/(?P<pk>\d+)', views.download, name='download'),
    
    url(r'^show-table/', views.show_table, name='show-table'),
    url(r'^show-child-table1/', views.show_child_table1, name='show-child-table1'),
    url(r'^show-child-table2/', views.show_child_table2, name='show-child-table2'),
    url(r'^show-child-table3/', views.show_child_table3, name='show-child-table3'),
    url(r'^show-table-attack/', views.show_table_attack, name='show-table-attack'),
    url(r'^show-child-table-attack/', views.show_child_table_attack, name='show-child-table-attack'),
    url(r'^show-table-vae-class0/', views.show_table_vae_class0, name='show-table-vae-class0'),
    url(r'^show-table-vae-class1/', views.show_table_vae_class1, name='show-table-vae-class1'),
    url(r'^show-table-vae-class2/', views.show_table_vae_class2, name='show-table-vae-class2'),
    url(r'^show-table-vae-class3/', views.show_table_vae_class3, name='show-table-vae-class3'),
    url(r'^show-table-vae-table/', views.show_table_vae_table, name='show-table-vae-table'),
    url(r'^generate-vae-text/', views.generate_vae_text, name='generate-vae-text'),


    # url(r'^show-page/', views.show_page, name='show-page'),
    # url(r'^preview/(?P<pk>\d+)', views.preview, name='preview'),
    # url(r'^(?P<pk>\d+)/mkdir/', views.mkdir, name='mkdir'), # 创建目录
    # url(r'^(?P<pk>\d+)/rmdir/', views.rmdir, name='rmdir'), # 递归地删除目录
    # url(r'^(?P<pk>\d+)/edit', views.edit, name='edit'), # 编辑文件
    url(r'^(?P<pk>\d+)/delete', views.delete, name='delete'), # 编辑文件
    # 既是文件详情页，又是目录的详情页
    # 因为可以容纳的 URL pattern 类型非常多，所以一定要放到最后
    # url(r'^(?P<username>[_\da-zA-Z]+)/(?P<path>.*)', views.detail, name='detail'),    
]
urlpatterns += staticfiles_urlpatterns()