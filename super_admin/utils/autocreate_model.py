import datetime
from django.db import models
from super_admin.utils.db2model import Db2Model


def create_model(name, fields=None, app_label="", module="", options=None):
    class Meta:
        pass

    if app_label:
        setattr(Meta, "app_label", app_label)
    if options is not None:
        for key, value in options.items():
            setattr(Meta, key, value)
    attrs = {"__module__": module, "Meta": Meta}
    if fields:
        attrs.update(fields)
    # 继承models.Model
    return type(name, (models.Model,), attrs)


def new_stock(tab_name, fields, database="default", verbose_name=None):
    """
    动态创建数据模型
    :param str tab_name: 表名
    :param str database: 连接的数据库, 默认default
    :param list fields: 展示的字段名
    :param str verbose_name: 展示名称
    :return: 返回模型类
    """
    args = {
        "verbosity": 1,
        "settings": None,
        "pythonpath": None,
        "traceback": False,
        "no_color": False,
        "force_color": False,
        "table": [tab_name],
        "database": database,
        "include_partitions": False,
        "include_views": False,
    }
    try:
        db2model = Db2Model()
        fields = fields if fields else []
        target_fields = db2model.get_fields_dict(args, fields=fields)
    except Exception as e:
        print("error in connect db", str(e))
        return
    verbose_name = verbose_name if verbose_name else tab_name + "_%s" % datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    options = {
        # "ordering": ["-id"],
        "db_table": tab_name,
        "managed": False,
        "verbose_name": verbose_name,
        "verbose_name_plural": verbose_name
    }
    custom_model = create_model(
        tab_name,
        target_fields,
        options=options,
        # app_label="%s" % tab_name,
        module="super_admin.register_table.models",
    )

    return custom_model
