from django.contrib import admin
from .models import Machine, Case, CaseUpdate, Collection, MachineCollection, Report, APILog



admin.site.register(Machine)
admin.site.register(Case)
admin.site.register(CaseUpdate)
admin.site.register(Collection)
admin.site.register(MachineCollection)
admin.site.register(Report)
admin.site.register(APILog)