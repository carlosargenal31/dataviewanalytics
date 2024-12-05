from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    path('', views.index, name='home'),
    path('data-management/', views.data_management, name='data-management'),
    path('api/get-favorite-data/', views.get_favorite_data, name='get_favorite_data'),
    path('api/get-favorite-metric-data/<str:metric_type>/', views.get_favorite_metric_data, name='get_favorite_metric_data'),
    path('toggle-favorite/<int:file_id>/', views.toggle_favorite, name='toggle-favorite'),
    path('data-visualization/<int:file_id>/', views.data_visualization, name='data-visualization'),
    path('data-preview/<int:file_id>/', views.data_preview, name='data-preview'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete-file'),
    path('data-selection/', views.data_selection, name='data-selection'),
    path('edit-data/<int:file_id>/', views.edit_data, name='edit-data'),
    path('save-data-changes/<int:file_id>/', views.save_data_changes, name='save-data-changes'),
    path('delete-rows/<int:file_id>/', views.delete_rows, name='delete-rows'),
    path('update-columns/<int:file_id>/', views.update_columns, name='update-columns'),
   
]

