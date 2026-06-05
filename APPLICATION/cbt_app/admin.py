from django.contrib import admin
from .models import Question, ExamSession, TestPackage

admin.site.site_header = "CBT Practice Engine Administration"
admin.site.site_title = "CBT Engine Admin Portal"
admin.site.index_title = "Welcome to the CBT Engine Control Panel"

# The user requested ONLY Personal Data (auth.User, registered by default)
# and Mock History (ExamSession) to be in the Admin Panel.


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'total_score', 'is_completed')
    list_filter = ('is_completed', 'start_time')
    readonly_fields = ('id', 'start_time')
    ordering = ('-start_time',)

