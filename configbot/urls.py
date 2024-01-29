from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path

from django.contrib.auth.decorators import user_passes_test
from configbot import settings
from configbot.views import my_view, update_nodes_view, account_view, AppView, ChartView, \
    ServerView, GenerateExelReport, price_view, update_tickets

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('sms/', my_view),
                  path('accounts/', account_view),
                  path('update/price', price_view),
                  path('update/nodes', update_nodes_view),
                  path('update/tickets', update_tickets),

                  re_path('app/', user_passes_test(lambda u: u.is_superuser)(AppView.as_view()), name='app'),
                  path('chart/', ChartView.as_view(), name='chart'),
                  path('server/', ServerView.as_view(), name='server'),

                  path('exel_report/', GenerateExelReport.as_view(), name='exel_report'),

              ] + \
              static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
