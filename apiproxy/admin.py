from django.contrib import admin
from .models import SearchDocument, MatchedDocument, Match, IncorrectTextReport

admin.site.register(SearchDocument)
admin.site.register(MatchedDocument)
admin.site.register(Match)

class IncorrectTextReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'search_document']
    ordering = ['created']
admin.site.register(IncorrectTextReport, IncorrectTextReportAdmin)
