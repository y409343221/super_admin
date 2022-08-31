readonly_admin = """
from django.conf import settings
from django.contrib import admin
from ..models import *
from super_admin.utils.approx_count import LargeTablePaginator


class {0}(admin.ModelAdmin):
    record_id = {4}
    readonly_fields = []
    _list_display = {1}
    search_fields = {2}
    list_per_page = 50
    show_full_result_count = False
    paginator = LargeTablePaginator
    allow_delete = {6}
    alter_fields = {7}

    def has_module_permission(self, request):

        if request.user.is_anonymous:
            return False
        if request.user.is_superuser:
            return True
        else:
            perm = ".".join(["{5}", "view_"+"{0}"])
            if request.user.has_perm(perm):
                return True
            return False

    def get_readonly_fields(self, request, obj=None):
        all_fields = list(
            self.readonly_fields
            + [field.name for field in obj._meta.fields]
            + [field.name for field in obj._meta.many_to_many]
        )
        if not self.alter_fields:
            return all_fields
        else:
            if request.user.has_perm(".".join(["{5}", "change_"+"{0}"])):
                return [x for x in all_fields if x not in self.alter_fields]
            return all_fields

    def get_list_display(self, request):
        if self._list_display:
            return list(self._list_display)
        return [field.name for field in self.model._meta.concrete_fields]

    def get_search_fields(self, request):
        if self.search_fields:
            return list(self.search_fields)
        return None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.allow_delete:
            return False
        delete_perm = ".".join(["{5}", "delete_"+"{0}"])
        if request.user.has_perm(delete_perm):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm(".".join(["{5}", "change_"+"{0}"])):
            return True
        return False

    def has_view_permission(self, request, obj=None):
        return True


admin.site.register({3}, {0})
"""

duplicate_model_admin = """
from django.conf import settings
from django.contrib import admin
from ..models import *
from super_admin.utils.approx_count import LargeTablePaginator


class {0}({1}):
    record_id = {7}

    class Meta:
        verbose_name = verbose_name_plural = '{2}'
        proxy = True
        db_table = '{3}'


class {4}(admin.ModelAdmin):
    readonly_fields = []
    _list_display = {5}
    search_fields = {6}
    list_per_page = 50
    show_full_result_count = False
    paginator = LargeTablePaginator
    allow_delete = {9}
    alter_fields = {10}

    def has_module_permission(self, request):
        if request.user.is_anonymous:
            return False
        if request.user.is_superuser:
            return True
        else:
            perm = ".".join(["{8}", "view_"+ "{4}"])
            if request.user.has_perm(perm):
                return True
            return False

    def get_readonly_fields(self, request, obj=None):
        all_fields = list(
            self.readonly_fields
            + [field.name for field in obj._meta.fields]
            + [field.name for field in obj._meta.many_to_many]
        )
        if not self.alter_fields:
            return all_fields
        else:
            if request.user.has_perm(".".join(["{8}", "change_"+"{4}"])):
                return [x for x in all_fields if x not in self.alter_fields]
            return all_fields

    def get_list_display(self, request):
        if self._list_display:
            return list(self._list_display)
        return [field.name for field in self.model._meta.concrete_fields]

    def get_search_fields(self, request):
        if self.search_fields:
            return list(self.search_fields)
        return None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.allow_delete:
            return False
        delete_perm = ".".join(["{8}", "delete_"+ "{4}"])
        if request.user.has_perm(delete_perm):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.has_perm(".".join(["{8}", "change_"+"{4}"])):
            return True
        return False

    def has_view_permission(self, request, obj=None):
        return True


admin.site.register({0}, {4})
"""


def common_admin_template(
    model_name,
    admin_name,
    list_fields,
    search_fields,
    record_id,
    app_name,
    alter_fields,
    allow_delete=False,
):

    return readonly_admin.format(
        model_name,
        admin_name,
        list_fields,
        search_fields,
        record_id,
        app_name,
        allow_delete,
        alter_fields
    )


def duplicate_model_admin_template(
    new_classname,
    inherit_classname,
    verbose_name,
    db_table,
    admin_classname,
    list_fields,
    search_fields,
    record_id,
    app_name,
    alter_fields,
    allow_delete=False
):
    """
    相同的model注册admin时， 需要继承原model再注册

    :param new_classname: 新model class名称
    :param inherit_classname: 继承的class
    :param verbose_name: admin展示名称
    :param db_table: 表名
    :param admin_classname: 生成的admin class名称
    :param list_fields: 展示字段
    :param search_fields: 查询字段
    :param record_id: 生成使用的record id, 用于控制删除权限
    :param app_name: 当前app名称
    :param alter_fields: 可修改字段
    :param allow_delete: 是否允许删除数据
    :
    :return: str
    """
    return duplicate_model_admin.format(
        new_classname,
        inherit_classname,
        verbose_name,
        db_table,
        admin_classname,
        list_fields,
        search_fields,
        record_id,
        app_name,
        allow_delete,
        alter_fields
    )
