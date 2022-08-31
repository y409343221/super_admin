from django.conf import settings
from django.contrib import admin


class ReadOnlyAdmin(admin.ModelAdmin):

    readonly_fields = []
    search_fields = []
    _list_display = []
    # def __init__(self, model, admin_site):
    #     super(ReadOnlyAdmin, self).__init__(model, admin_site)

    # def get_queryset(self, request):
    #     qs = super(ReadOnlyAdmin, self).get_queryset(request)
    #     return qs.filter(created_by=request.user.id)

    def has_module_permission(self, request):
        from super_admin.register_table.models import AdminCustomRecord

        if request.user.is_anonymous:
            return False
        if request.user.is_superuser:
            return True
        records = AdminCustomRecord.objects.filter(created_by=request.user).values()
        db_name = settings.DATABASE_APPS_MAPPING.get(
            self.model._meta.__dict__["app_label"], "default"
        )
        for record in records:
            if (
                record["table_name"]
                == self.model._meta.__dict__["original_attrs"]["db_table"]
                and db_name == record["db_source"]
            ):
                return True
        return False

    def get_readonly_fields(self, request, obj=None):
        return list(
            self.readonly_fields
            + [field.name for field in obj._meta.fields]
            + [field.name for field in obj._meta.many_to_many]
        )

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
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True


# class ListAdminMixin(object):
#
#     def __init__(self, model, admin_site):
