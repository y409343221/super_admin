from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from super_admin.contrib.base import BaseModel, ACTIVE_FLAG_Y
# from super_admin.utils.autocreate_model import new_stock
# from tinymce.models import HTMLField


DB_SOURCE_MAP = settings.DB_SOURCE_MAP


class AdminCustomRecordManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(active_flag=ACTIVE_FLAG_Y).prefetch_related("created_by")


class AdminCustomRecord(BaseModel):

    db_source = models.CharField(max_length=200, choices=DB_SOURCE_MAP, null=False, blank=False, verbose_name=_("数据来源"))
    table_name = models.CharField(max_length=60, null=True, blank=True, verbose_name=_("表(视图)名"))
    list_fields = models.TextField(blank=True, null=True, verbose_name=_("展示字段(一行一个，默认全部字段)"))
    search_fields = models.TextField(blank=True, null=True, verbose_name=_("查询字段(一行一个)"))
    # view_sql = models.TextField(null=True, blank=True, verbose_name=_("定制视图sql"))
    verbose_name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("展示名称"))
    admin_name = models.CharField(max_length=500, null=True, blank=True, verbose_name=_("生成的admin名称"))
    alter_fields = models.TextField(null=True, blank=True, verbose_name=_("修改字段(一行一个)"), help_text=_("填写后需要向系统管理员申请修改权限"))
    can_delete = models.BooleanField(default=False, verbose_name=_("是否允许删除数据"), help_text=_("勾选后需要向系统管理员申请删除权限"))

    objects = AdminCustomRecordManager()

    class Meta:
        verbose_name = verbose_name_plural = _("后台定制记录")
        db_table = "ad_custom_record"
        ordering = ["-id"]

    def __str__(self):
        return self.table_name if self.table_name else self.db_source


class InspectDbRecord(models.Model):
    db_source = models.CharField(max_length=200, choices=DB_SOURCE_MAP, null=False, blank=False, verbose_name=_("数据来源"))
    model_name = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("model名称"))
    inspectdb_records = models.TextField(null=True, blank=True, verbose_name=_('迁移记录'))

    changed_map = (
        ("Y", "是"),
        ("N", "否")
    )
    is_changed = models.CharField(max_length=3, default="N", verbose_name=_("是否修改过"))

    class Meta:
        verbose_name = verbose_name_plural = _("迁移记录")
        db_table = "ad_inspectdb_records"
        ordering = ["-id"]

    def __str__(self):
        return self.model_name if self.model_name else self.db_source


class DbSourcePermission(models.Model):

    db_source = models.CharField(max_length=200, choices=DB_SOURCE_MAP, null=False, blank=False, verbose_name=_("数据来源"))
    user = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = verbose_name_plural = _("数据库权限表")
        db_table = "ad_dbsource_permission"
        ordering = ["-id"]

    def __str__(self):
        return str(self.db_source) + "---" + str(self.user.username)


















