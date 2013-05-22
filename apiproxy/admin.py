from django import forms
from django.db.models import Count
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import SearchDocument, MatchedDocument, Match, IncorrectTextReport

def ForeignKeyAsLinkWidget(cls):
    class ForeignKeyAsLinkWidgetCls(forms.Widget):
        def render(self, name, value, attrs=None):
            url = "/admin/{a}/{m}/{pk}/".format(a=cls._meta.app_label,
                                                m=cls._meta.module_name,
                                                pk=value)
            caption = name
            return u'<a href="{url}">{caption}</a>'.format(url=url, caption=caption)
    return ForeignKeyAsLinkWidgetCls

class UrlAsAnchorWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return mark_safe(u'<a href="{url}">{url}</a>'.format(url=value))

class SearchDocumentTextWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        attr_str = u" ".join([u'{k}="{v}"'.format(k=k, v=v) for (k, v) in attrs.items()])
        return u"<p {a}>{t}</p>".format(a=attr_str, t=value)

class SearchDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'title']
    search_fields = ['uuid', 'title']

admin.site.register(SearchDocument, SearchDocumentAdmin)
admin.site.register(MatchedDocument)
admin.site.register(Match)

class IncorrectTextReportAdminForm(forms.ModelForm):
    document_url = forms.URLField(widget=UrlAsAnchorWidget)
    document_text = forms.CharField(widget=SearchDocumentTextWidget)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            self.base_fields['document_text'].initial = instance.search_document.text
            self.base_fields['document_url'].initial = instance.search_document.url
        super(IncorrectTextReportAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = IncorrectTextReport
        widgets = {
            'search_document': ForeignKeyAsLinkWidget(SearchDocument),
        }

class IncorrectTextDomainFilter(admin.SimpleListFilter):
    title = u'Domain'

    parameter_name = 'searchdocument_domain'

    def lookups(self, request, model_admin):
        query = (SearchDocument.objects
                 .filter(text_problems__isnull=False,
                         domain__isnull=False)
                 .values('domain')
                 .annotate(cnt=Count('pk'))
                 .order_by('-cnt')[:100])
        return [(grp['domain'], u'{cnt} {domain}'.format(**grp)) for grp in query[:20]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(search_document__domain=self.value())
        else:
            return queryset
        

class IncorrectTextReportAdmin(admin.ModelAdmin):
    form = IncorrectTextReportAdminForm
    list_display = ['id', 'created', 'search_document']
    ordering = ['created']
    list_filter = (IncorrectTextDomainFilter,)
    fieldsets = (
        ('Incorrect Text Report', {
            'fields': ('problem_description', 'remote_addr',
                       'user_agent', 'languages', 'encodings')
        }),
        ('Search Document Text', {
            'fields': ('search_document', 'document_url', 'document_text')
        })
    )
    readonly_fields = ('document_text',)

admin.site.register(IncorrectTextReport, IncorrectTextReportAdmin)
