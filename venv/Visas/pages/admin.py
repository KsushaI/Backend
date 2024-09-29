from django.contrib import admin

# Register your models here.

from .models import Visa, Application

admin.site.register(Visa)
admin.site.register(Application)