import os

from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
# django.setup()

from django.apps import AppConfig, apps
from django.contrib import admin
from super_admin.admin_permissions import ReadOnlyAdmin


class RegisterTableConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "super_admin.register_table"

    # def ready(self):
    #     from super_admin.register_table.models import AdminCustomRecord
    #
    #     app_labels = settings.LOCAL_APPS
    #
    #     custom_records = AdminCustomRecord.objects.all().values()
    #
    #     exclude_labels = [
    #         "register_table"
    #     ]
    #
    #     for label in app_labels:
    #         label = label.split(".")[-1]
    #         if label in exclude_labels:
    #             continue
    #         models = apps.get_app_config(label).get_models()
    #         db_name = settings.DATABASE_APPS_MAPPING.get(label, "default")
    #         if db_name == "default":
    #             continue
    #         for model in models:
    #             for record in custom_records:
    #                 if model._meta.model_name == record["table_name"].replace("_", "").replace("-", "") and db_name == record["db_source"]:
    #                 # if model._meta.__dict__["original_attrs"].get("db_table", "") == record["table_name"] and db_name == record["db_source"]:
    #                     if record["verbose_name"]:
    #                         model._meta.__dict__["verbose_name"] = record["verbose_name"]
    #                         model._meta.__dict__["verbose_name_plural"] = record["verbose_name"]
    #                     admin_class = type(
    #                         "AdminClass", (ReadOnlyAdmin,), {}
    #                     )
    #                     if record["search_fields"]:
    #                         admin_class.search_fields = record["search_fields"].splitlines(keepends=False) or []
    #                     if record["list_fields"]:
    #                         admin_class._list_display = record["list_fields"].splitlines(keepends=False) or []
    #                     try:
    #                         admin.site.register(model, admin_class)
    #                     except admin.sites.AlreadyRegistered:
    #                         pass
    #                     break

"""
old version
"""
# @staticmethod
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

# def ready(self):
#
#     # models = apps.get_app_config("super_admin.register_table").get_models()
#     # TODO 无法 makemigrations, 需要注释 ready才可以
#     # models = self.create_models()
#     for model, search_fields in models:
#         ReadOnlyAdmin.search_fields = search_fields
#         admin_class = type(
#             "AdminClass", (ReadOnlyAdmin,), {"search_fields": search_fields}
#         )
#         try:
#             admin.site.register(model, admin_class)
#         except admin.sites.AlreadyRegistered:
#             pass


# class UniversalManagerApp(AppConfig):
#     """
#     应用配置在所有应用的Admin都加载后执行
#
#     """
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'super_admin.register_table'
#
#     def ready(self):
#
#         models = apps.get_app_config("super_admin.register_table").get_models()
#
#         for model in models:
#             admin_class = type("AdminClass", (ReadOnlyAdmin,), {"search_fields": []})
#             try:
#                 print(model)
#                 admin.site.register(model, admin_class)
#             except admin.sites.AlreadyRegistered:
#                 pass
