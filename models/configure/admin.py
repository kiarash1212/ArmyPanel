from django.contrib import admin
from solo.admin import SingletonModelAdmin

from models.configure.models import Server, Node, Account, SiteConfiguration


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'address',
        'is_active'
    ]
    readonly_fields = ['token']
    search_fields = ['name']


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'server',
        'domain',
        'port',
        'type',
        'is_active'
    ]
    list_filter = [
        'server',
        'is_active'
    ]
    readonly_fields = ['name', 'provider_id']
    search_fields = ['name']

    def has_add_permission(self, request):
        return False


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        'username',
        'is_active'
    ]
    search_fields = ['username']


admin.site.register(SiteConfiguration, SingletonModelAdmin)
