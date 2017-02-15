from django.contrib import admin

# Register your models here.

from .models import Task, Passwordresetcodes
# Register your models here.


admin.site.register(Task)
admin.site.register(Passwordresetcodes)
