try:
    from django.urls import re_path as url
except ImportError:
    from django.conf.urls import url
from elfinder.views import index, connector_view
from elfinder.views_tinymce import tinymce_filebrowser_script_view, tinymce_filebrowser_dialog_view

urlpatterns = [
    url(r'^(?P<coll_id>\d+)/$', index, name='elfinder_index'),
    url(r'^connector/(?P<coll_id>\d+)/$', connector_view, name='elfinder_connector'),

    url(r'^$', index, name='elfinder_index'),
    url(r'^connector/$', connector_view, name='elfinder_connector'),

    url(r'^tinymce/filebrowser-script/$', tinymce_filebrowser_script_view, name='elfinder_tinymce_filebrowser_script'),
    url(r'^tinymce/filebrowser-dialog/$', tinymce_filebrowser_dialog_view, name='elfinder_tinymce_filebrowser_dialog'),
]
