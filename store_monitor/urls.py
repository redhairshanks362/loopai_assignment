from django.urls import path, include
from store_monitor.views import TriggerReportView, GetReportView


urlpatterns = [
    path('trigger_report/', TriggerReportView.as_view(), name='trigger_report'),
    path('get_report/', GetReportView.as_view(), name='get_report'),
]