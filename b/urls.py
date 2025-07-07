from django.urls import path
from .views import index,purchase,sales,get_products,purchase_details,sale_details,get_batch_info,reports


urlpatterns = [
    path('index/', index, name='index'),
    path('purchase/', purchase, name='purchase'),
    path('sales/', sales, name='sales'),
    path('ajax/get-products/', get_products, name='get_products'),
    path('ajax/purchase-details/<int:pk>/',purchase_details, name='purchase_details'),
    path('ajax/sale-details/<int:sale_id>/', sale_details, name='sale-details'),
    
    path('ajax/get-batch-info/<int:medicine_id>/', get_batch_info, name='get_batch_info'),
    path('reports/', reports, name='reports'),

]