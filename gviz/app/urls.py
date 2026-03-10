from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('load-plugin/', views.load_plugin, name='load_plugin'),
    path('load-graph/', views.load_graph, name='load_graph'),
    path('workspace/', views.create_workspace, name='create_workspace'),
    path('workspace/<str:workspace_id>', views.delete_workspace, name='delete_workspace'),
    path('workspace/<str:workspace_id>/filter/', views.filter, name='delete_workspace'),
    path('workspace/<str:workspace_id>/node/<str:node_id>', views.update_nodes, name='delete_workspace'),
    path('workspace/<str:workspace_id>/edge/<str:edge_id>', views.update_edges, name='delete_workspace'),
]
