from django.contrib import admin
from .models import BotUser, Instance, InstanceAccess, Manager, Project
from django.contrib.auth.models import User, Group


class UserAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    list_display = ('id', 'user_id', 'name', 'email', 'channel_id')
    search_fields = ('id', 'user_id', 'name', 'email', 'channel_id')
    list_display_links = ('id', 'name')
    readonly_fields = ('id', 'user_id', 'name', 'channel_id')
    list_per_page = 20


class InstanceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    list_display_links = ('id', 'name')
    list_per_page = 20


class InstanceAccessAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'instance_id')
    search_fields = ('user_id', 'instance_id')
    list_display_links = ('user_id',)
    list_filter = ('instance_id__name', 'user_id__name')
    list_per_page = 20


class ManagerAdmin(admin.ModelAdmin):
    list_display = ('manager_id', 'instance_id')
    search_fields = ('manager_id', 'instance_id')
    list_display_links = ('manager_id',)
    list_filter = ('instance_id__name', 'manager_id__name')
    list_per_page = 20


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('codeship_project_name', 'gitlab_project_id')
    list_display_links = ('codeship_project_name', 'gitlab_project_id')
    list_per_page = 20


admin.site.register(BotUser, UserAdmin)
admin.site.register(Instance, InstanceAdmin)
admin.site.register(InstanceAccess, InstanceAccessAdmin)
admin.site.register(Manager, ManagerAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.unregister(User)
admin.site.unregister(Group)
