from django.contrib import admin
from .models import ActionRequests, AuditLogs

admin.site.register(ActionRequests)
admin.site.register(AuditLogs)
