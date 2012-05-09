from django.contrib import admin
from .models import SearchDocument, MatchedDocument, Match

admin.site.register(SearchDocument)
admin.site.register(MatchedDocument)
admin.site.register(Match)
