"""
1.先创建auto_admin文件
2.创建xxx_xxx_1_admin.py文件， 命名方式， db_source + table_name + user_id + admin.py,
3.根据record 生成admin class.
4.在主admin中导入admin class.
"""
import keyword
import re
import os
import pathlib
import subprocess
import datetime
import time

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models.constants import LOOKUP_SEP
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import create_contenttypes

from super_admin.register_table.models import AdminCustomRecord
from super_admin.utils.auto_admin_template import (
    common_admin_template,
    duplicate_model_admin_template,
)


class Command(BaseCommand):
    help = "Auto create django admin.py by records"
    # requires_system_checks = []
    # stealth_options = ('table_name_filter',)
    db_module = "django.db"

    def add_arguments(self, parser):
        parser.add_argument(
            "table",
            nargs="*",
            type=str,
            help="Selects what tables or views should be created.",
        )

    def handle(self, **options):
        def table2model(_table_name):
            return re.sub(r"[^a-zA-Z0-9]", "", _table_name.title())

        table_name = options["table"]

        custom_records = AdminCustomRecord.objects.all().order_by("id").values()
        app_db_mapping = settings.EXTRA_DB_APPS_MAPPING
        app_names_mapping = dict(
            zip(app_db_mapping.values(), app_db_mapping.keys())
        )  # db_name: app_name
        for record in custom_records:
            if table_name and record["table_name"] != table_name[0]:
                continue
            app_name = app_names_mapping[record["db_source"]]
            print("*" * 35)
            print(
                f"当前执行的id: {record['id']}, app_name: {app_name}, 数据库: {record['db_source']}, 表名: {record['table_name']}, 创建人id: {record['created_by_id']}"
            )
            # check app is installed
            if ("super_admin." + app_name) not in settings.INSTALLED_APPS:
                raise CommandError(f"{app_name} is not in INSTALLED_APPS")
            app_path = settings.ROOT_DIR / "super_admin" / app_name
            # check app is created
            if not app_path.exists():
                raise CommandError(f"{app_name} is not exist")
            auto_admin_path = app_path / "auto_admin"
            if not auto_admin_path.exists():
                os.makedirs(auto_admin_path, exist_ok=True)
                init_file = auto_admin_path / "__init__.py"
                with open(init_file, "w"):
                    pass
            print("校验准备完毕， 正在查询Model名称···")
            # 查询Model
            connection = connections[record["db_source"]]
            model_name = None
            with connection.cursor() as cursor:
                types = {"t"}
                table_info = connection.introspection.get_table_list(cursor)
                for class_name in sorted(
                    info.name for info in table_info if info.type in types
                ):
                    if class_name == record["table_name"]:
                        model_name = table2model(class_name)
            if not model_name:
                raise CommandError("未查询到model名称， 生成model名称失败。")

            print("开始生成admin文件")
            # 命名方式， db_source + table_name + user_id + admin.py,
            current_datetime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            import_name = f"{record['db_source']}_{record['table_name']}_{record['created_by_id']}_{record['id']}_{current_datetime}_admin"
            # check if admin is already created

            if len(
                list(
                    auto_admin_path.glob(
                        f"{record['db_source']}_{record['table_name']}_{record['created_by_id']}_{record['id']}*.py"
                    )
                )
            ):
                print(
                    f"{record['db_source']}_{record['table_name']}_{record['created_by_id']}_{record['id']}已经存在，本次将跳过。"
                )
                continue

            admin_filename = import_name + ".py"
            admin_file = auto_admin_path / admin_filename
            search_fields, list_fields, alter_fields = (
                record["search_fields"].splitlines(keepends=False) or [],
                record["list_fields"].splitlines(keepends=False) or [],
                record["alter_fields"].splitlines(keepends=False) or [],
            )
            admin_model_name = f"{table2model(record['db_source'])}{table2model(record['table_name'])}{record['created_by_id']}{table2model(current_datetime)}Admin"

            if len(
                list(
                    auto_admin_path.glob(
                        f"{record['db_source']}_{record['table_name']}*.py"
                    )
                )
            ):
                # 已经生成过该表的admin， 需要额外处理， 生成继承model， 再注册到admin
                kwargs = {
                    "new_classname": f"{model_name}{current_datetime.replace('_', '')}",
                    "inherit_classname": model_name,
                    "verbose_name": record["verbose_name"]
                    if record["verbose_name"]
                    else f"{record['table_name']}{current_datetime}",
                    "db_table": record["table_name"],
                    "admin_classname": admin_model_name,
                    "list_fields": list_fields,
                    "search_fields": search_fields,
                    "record_id": record["id"],
                    "app_name": app_name,
                    "alter_fields": alter_fields,
                    "allow_delete": record["can_delete"]
                }
                admin_content = duplicate_model_admin_template(**kwargs)

            else:
                admin_content = common_admin_template(
                    admin_model_name,
                    list_fields,
                    search_fields,
                    model_name,
                    record["id"],
                    app_name,
                    alter_fields,
                    record["can_delete"],
                )
            # 写入auto_admin 下
            with open(auto_admin_path / admin_file, "w", encoding="utf-8") as f:
                f.write(admin_content)

            with open(app_path / "admin.py", "a+") as f1:
                read_text = f1.read()
                if f"auto_admin.{import_name}" not in read_text:
                    f1.write(f"from .auto_admin.{import_name} import *")
                    f1.write("\n")
            acr = AdminCustomRecord.objects.get(pk=record["id"])
            acr.admin_name = admin_model_name
            acr.save()
            _model_name = record["table_name"].replace("_", "").replace("-", "")
            try:
                ct = ContentType.objects.get(
                    app_label=app_name, model=_model_name
                )
                print(app_name, _model_name)
            except ContentType.DoesNotExist:
                app_config = apps.get_app_config(app_label=app_name)
                create_contenttypes(app_config)
                ct = ContentType.objects.get(
                    app_label=app_name, model=_model_name
                )
            if ct:
                permission_names = [
                    f"Can view {admin_model_name}",
                    f"Can add {admin_model_name}",
                    f"Can delete {admin_model_name}",
                    f"Can change {admin_model_name}",
                ]
                for permission_name in permission_names:
                    _permission_name = "_".join(permission_name.split(" ")[1:])
                    perm, _ = Permission.objects.get_or_create(
                        name=permission_name,
                        content_type=ct,
                        codename=_permission_name,
                    )
                    if permission_name.startswith("Can view"):
                        user = get_user_model().objects.filter(pk=record['created_by_id']).first()
                        if user:
                            user.user_permissions.add(perm)
            else:
                print("权限加载失败， 检查是否进行了migrate或者手动添加。")

            print(f"生成完毕， admin文件名: {admin_filename}, AdminClass名称: {admin_model_name}")

            time.sleep(0.5)
            print()
