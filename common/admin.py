from django.db import models
from django.contrib import admin
from django.apps import apps
from unfold.admin import (
    ModelAdmin,
    StackedInline as BaseStackedInline,
    TabularInline as BaseTabularInline,
)
from unfold.widgets import (
    UnfoldAdminSelectWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminFileFieldWidget,
)


class BaseInlineAdmin:
    exclude = ["created_at", "updated_at", "created_by", "updated_by"]
    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
        models.TextField: {"widget": UnfoldAdminTextInputWidget},
        models.ForeignKey: {"widget": UnfoldAdminSelectWidget},
        models.FileField: {"widget": UnfoldAdminFileFieldWidget},
    }

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class StackedInline(BaseInlineAdmin, BaseStackedInline):
    pass


class TabularInline(BaseInlineAdmin, BaseTabularInline):
    pass


class BaseModelAdmin(ModelAdmin):
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    exclude = ["created_by", "updated_by"]
    formfield_overrides = {
        models.CharField: {"widget": UnfoldAdminTextInputWidget},
        models.TextField: {"widget": UnfoldAdminTextInputWidget},
        models.ForeignKey: {"widget": UnfoldAdminSelectWidget},
        models.FileField: {"widget": UnfoldAdminFileFieldWidget},
    }

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
