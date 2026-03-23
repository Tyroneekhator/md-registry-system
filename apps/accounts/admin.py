from django.contrib import admin
from .models import Users, Groups, Permissions, UserGroups, GroupPermissions

admin.site.register(Users)
admin.site.register(Groups)
admin.site.register(Permissions)
admin.site.register(UserGroups)
admin.site.register(GroupPermissions)
