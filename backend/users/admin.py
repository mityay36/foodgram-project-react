from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Follow, User


class UserChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'


class ProfileAdmin(UserAdmin):
    form = UserChangeForm
    list_display = ('email', 'username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'username',
                'first_name',
                'last_name'
            ),
        }),
    )
    search_fields = ('username',)
    list_filter = ('username', 'email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, ProfileAdmin)
admin.site.register(Follow)
admin.site.unregister(Group)
