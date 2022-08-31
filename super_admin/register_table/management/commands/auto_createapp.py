import keyword
import re
import os
import pathlib
import subprocess
import shutil
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.core.management.templates import TemplateCommand
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models.constants import LOOKUP_SEP

from django.conf import settings


class Command(TemplateCommand):
    help = "Auto create django app and mv to super_admin."
    requires_system_checks = []
    stealth_options = ("table_name_filter",)
    db_module = "django.db"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="*",
            help="Nominates a database to create. Defaults to create all databases.",
        )

    def remove_file(self, old_path, new_path):
        if not os.path.exists(new_path):
            os.makedirs(new_path, exist_ok=True)
        filelist = os.listdir(old_path)  # 列出该目录下的所有文件,listdir返回的文件列表是不包含路径的。
        for file in filelist:
            src = os.path.join(old_path, file)
            dst = os.path.join(new_path, file)
            shutil.move(src, dst)
        os.rmdir(old_path)

    def record_apps(self, app_name):
        # with open(settings.ROOT_DIR / "config" / "register_apps", "a") as f:
        #     f.write(app_name + "\n")
        pass

    def handle(self, **options):
        # {'verbosity': 1, 'settings': None, 'pythonpath': None, 'traceback': False, 'no_color': False,
        #  'force_color': False, 'name': 'test', 'directory': None, 'template':None, 'extensions': ['py'], 'files': []}
        options = {
            "verbosity": 1,
            "settings": None,
            "pythonpath": None,
            "traceback": False,
            "no_color": False,
            "force_color": False,
            "template": None,
            "extensions": ["py"],
            "files": [],
            "database": options["database"]
        }
        exclude_app_names = settings.DATABASE_APPS_BASE.keys()
        if options["database"] == "*":
            created_apps = []
            for app_name, db_name in settings.EXTRA_DB_APPS_MAPPING.items():
                if app_name in exclude_app_names:
                    print("Can not execute %s, about to execute next one" % app_name)
                    continue
                app_path = settings.ROOT_DIR / "super_admin" / app_name
                if app_path.exists():
                    continue
                super().handle("app", app_name, target=None, **options)
                created_apps.append(app_name)

            for app in created_apps:
                if os.path.exists(settings.ROOT_DIR / app):
                    self.remove_file(settings.ROOT_DIR / app, settings.ROOT_DIR / "super_admin" / app)
                    self.record_apps(app)
                    print("app %s created success." % app)
        else:
            db_name = options["database"]
            exclude_dbs = ["default"]
            conf_db_names = settings.DATABASE_APPS_MAPPING.values()
            if db_name not in conf_db_names or db_name in exclude_dbs:
                raise CommandError("Can not execute %s db source." % db_name)
            app_names = [k for k, v in settings.DATABASE_APPS_MAPPING.items() if v == db_name]
            if len(app_names):
                app_name = app_names[0]
                app_path = settings.ROOT_DIR / "super_admin" / app_name
                if app_path.exists():
                    raise CommandError("%s already exists" % app_name)
                super().handle("app", app_name, target=None, **options)
                if os.path.exists(settings.ROOT_DIR / app_name):
                    self.remove_file(settings.ROOT_DIR / app_name, settings.ROOT_DIR / "super_admin" / app_name)
                    self.record_apps(app_name)
                    print("app %s created success." % app_name)




