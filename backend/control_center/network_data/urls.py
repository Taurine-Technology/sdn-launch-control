from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import aggregate_flows, aggregate_flows_by_mac, log_flow, data_used_per_classification, data_used_per_user, data_used_per_user_per_classification

app_name = 'network_data'

router = DefaultRouter()

urlpatterns = [
    path('network/data-per-classification/', data_used_per_classification, name='data-per-classification'),
    path('network/data-per-user/', data_used_per_user, name='data-per-user'),
    path('network/user-flow-data/', data_used_per_user_per_classification, name='user-flow-data'),

    path('network/aggregate-flows/', aggregate_flows, name='aggregate-flows'),
    path('network/aggregate-flows-mac/', aggregate_flows_by_mac, name='aggregate-flows-by-mac'),
    path('network/log-flow-stats/', log_flow, name='log-flow-stats'),
    path('', include(router.urls)),
]
