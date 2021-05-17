from django.contrib import admin

from .models import Group, Post

EMPTY = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group', 'image')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = EMPTY


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title')
    search_fields = ('title',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
