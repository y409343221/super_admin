import datetime
import functools
from typing import Optional

from django.conf import settings
from django.contrib import admin
from django.apps import AppConfig, apps

# Register your models here.
from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import format_html, strip_tags
from django.utils.translation import gettext_lazy

from super_admin.admin_permissions import ReadOnlyAdmin
from super_admin.register_table.apps import RegisterTableConfig
from super_admin.register_table.forms import RegisterTableAddForm
from super_admin.register_table.models import AdminCustomRecord, InspectDbRecord, DbSourcePermission
from super_admin.utils.approx_count import LargeTablePaginator

"""
old version
"""
# def create_models():
#     from super_admin.register_table.models import AdminCustomRecord
#     from super_admin.utils.autocreate_model import new_stock
#
#     # created_by
#     # TODO 需要考虑一下如何过滤 只生成本人填写的model
#     records = AdminCustomRecord.objects.all().values()
#     for record in records:
#         if record["search_fields"]:
#             search_fields = record["search_fields"].splitlines(keepends=False)
#         else:
#             search_fields = []
#         # print(search_fields)
#         yield new_stock(
#             record["table_name"],
#             record["list_fields"].splitlines(keepends=False),
#             record["db_source"],
#             record["verbose_name"],
#         ), search_fields
#
#
# models = create_models()
# for model, search_fields in models:
#     ReadOnlyAdmin.search_fields = search_fields
#     admin_class = type(
#         "AdminClass", (ReadOnlyAdmin,), {"search_fields": search_fields}
#     )
#     try:
#         admin.site.register(model, admin_class)
#     except admin.sites.AlreadyRegistered:
#         pass


@admin.register(AdminCustomRecord)
class RegisterTableAdmin(admin.ModelAdmin):

    # def auto_register_admins(self):
    #     app_labels = settings.LOCAL_APPS
    #     for label in app_labels:
    #         label = label.split(".")[-1]
    #         models = apps.get_app_config(label).get_models()
    #         for model in models:
    #             # ReadOnlyAdmin.search_fields = search_fields
    #             admin_class = type(
    #                 "AdminClass", (ReadOnlyAdmin,), {"search_fields": []}
    #             )
    #             try:
    #                 admin.site.register(model, admin_class)
    #             except admin.sites.AlreadyRegistered:
    #                 pass

    __module__ = AdminCustomRecord
    list_display = [
        "db_source",
        "table_name",
        "verbose_name",
        "list_style",
        "search_style",
        "alter_fields_style",
        "can_delete",
        "admin_name",
    ]
    readonly_fields = [
        "admin_name",
        "created_by",
        "created_date",
        "last_updated_date",
        "last_updated_by",
        "active_flag",
    ]
    form = RegisterTableAddForm

    change_form_template = "admin/register_change_form.html"
    list_per_page = 50

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        self.form.request = request
        return super(RegisterTableAdmin, self).changeform_view(request, object_id, extra_context=extra_context)

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super(RegisterTableAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user.id)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        obj.created_date = datetime.datetime.now()
        obj.last_updated_date = datetime.datetime.now()
        obj.last_updated_by = request.user
        # if request.method.upper() == "POST":
        #     self.reload(obj)
            # super(RegisterTableAdmin, self).save_model(request, obj, form, change)
            #
            # return redirect(
            #     reverse("admin:register_table_admincustomrecord_changelist")
            # )
        super(RegisterTableAdmin, self).save_model(request, obj, form, change)
        # TODO 邮件发送功能，提醒管理员审批。
        self.message_user(request, "创建成功，请联系管理员进行审批。")

    def delete_queryset(self, request, queryset):
        for q in queryset:
            q.active_flag = "N"
            q.save()
            perm = ".".join([q.db_source, "view_" + q.admin_name])
            if request.user.has_perm(perm):
                _permission_name = "_".join(f"Can view {q.admin_name}".split(" ")[1:])
                p = Permission.objects.filter(codename=_permission_name).first()
                if p:
                    request.user.user_permissions.remove(p)

    def list_style(self, obj):
        list_fields = obj.list_fields
        if not list_fields:
            return "-"
        if len(list_fields) >= 30:
            return list_fields[:31] + "..."
        return list_fields

    def search_style(self, obj):
        search_fields = obj.search_fields
        if not search_fields:
            return "-"
        if len(search_fields) >= 30:
            return search_fields[:31] + "..."
        return search_fields

    def alter_fields_style(self, obj):
        alter_fields = obj.alter_fields
        if not alter_fields:
            return "-"
        if len(alter_fields) >= 30:
            return alter_fields[:31] + "..."
        return alter_fields

    list_style.short_description = "展示字段(一行一个，不填使用全部字段)"
    search_style.short_description = "查询字段(一行一个)"
    alter_fields_style.short_description = "可修改字段(一行一个)"
    _fields = [
        "db_source",
        "table_name",
        "list_fields",
        "search_fields",
        # "view_sql",
        "alter_fields",
        "verbose_name",
        "can_delete",
    ]
    fieldsets = (
        ("填写项", {"fields": tuple(_fields)}),
        ("基础信息(不可修改项)", {"fields": tuple(readonly_fields)}),
    )



@admin.register(InspectDbRecord)
class InspectDbRecordAdmin(admin.ModelAdmin):

    __module__ = InspectDbRecord
    list_display = [
        "id",
        "db_source",
        "model_name",
        # "inspectdb_records",
        "inspectdb_records_format",
    ]
    readonly_fields = [
        "is_changed",
    ]
    search_fields = ["db_source", "model_name"]
    actions = ["delete_all"]
    show_full_result_count = False
    paginator = LargeTablePaginator

    def inspectdb_records_format(self, obj):
        if obj.inspectdb_records:
            return format_html("<pre>" + obj.inspectdb_records + "</pre>")

    def save_model(self, request, obj, form, change):
        if request.method.upper() in ["POST", "PUT"]:
            obj.is_changed = "Y"
        super(InspectDbRecordAdmin, self).save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super(InspectDbRecordAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            if "delete_all" in actions:
                del actions["delete_all"]
        return actions

    def delete_all(self, request, queryset):
        if request.user.is_superuser:
            qs = InspectDbRecord.objects.all().delete()
        else:
            self.message_user(request, "只有系统管理员可以删除全部数据")

    delete_all.short_description = "删除全部数据"
    inspectdb_records_format.short_description = "迁移记录"


@admin.register(DbSourcePermission)
class DbSourcePermissionAdmin(admin.ModelAdmin):

    __module__ = DbSourcePermission
    list_display = ["db_source", "user"]

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False
