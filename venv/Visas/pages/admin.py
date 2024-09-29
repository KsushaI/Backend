from django.contrib import admin

# Register your models here.

from .models import Visa, Application, Application_Visa

admin.site.register(Visa)
admin.site.register(Application)
admin.site.register(Application_Visa)