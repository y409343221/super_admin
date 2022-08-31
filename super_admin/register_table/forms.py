import keyword
import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.constants import LOOKUP_SEP
from django.utils.connection import ConnectionDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db import connections
from django.conf import settings

from super_admin.register_table.models import AdminCustomRecord, InspectDbRecord, DbSourcePermission


class RegisterTableAddForm(forms.ModelForm):

    list_fields = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': '在页面上的展示字段(一行填写一个,不填展示全部)'}), label=_('展示字段'))
    search_fields = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': '搜索框查询的字段(一行填写一个)'}), label=_('查询字段'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.request.user.is_superuser:
            db_source = DbSourcePermission.objects.filter(user=self.request.user).values_list("db_source", flat=True)
            db_source_choices = [k for k in settings.DB_SOURCE_MAP if k[0] in db_source]
            db_source_choices.insert(0, ("--------------------", "-------------------"))
            if "db_source" in self.fields.keys():
                self.fields['db_source'].choices = db_source_choices

    def normalize_col_name(self, col_name):
        """
        Modify the column name to make it Python-compatible as a field name
        """
        new_name = col_name.lower()

        new_name, num_repl = re.subn(r'\W', '_', new_name)

        if new_name.find(LOOKUP_SEP) >= 0:
            while new_name.find(LOOKUP_SEP) >= 0:
                new_name = new_name.replace(LOOKUP_SEP, '_')

        if new_name.startswith('_'):
            new_name = 'field%s' % new_name

        if new_name.endswith('_'):
            new_name = '%sfield' % new_name

        if keyword.iskeyword(new_name):
            new_name += '_field'

        if new_name[0].isdigit():
            new_name = 'number_%s' % new_name

        return new_name

    def get_connection(self, _db_source):
        try:
            if hasattr(self, _db_source):
                return getattr(self, _db_source)
            connection = connections[_db_source]
        except ConnectionDoesNotExist:
            raise ValidationError(f"无法连接到{_db_source}数据源")
        else:
            setattr(self, _db_source, connection)
            return connection

    def get_fields(self, _db_source, _table_name):
        connection = self.get_connection(_db_source)
        types = {'t'}
        with connection.cursor() as cursor:
            if _table_name not in [info.name for info in connection.introspection.get_table_list(cursor) if info.type in types]:
                raise ValidationError(f"没有查询到表{_table_name}")
            table_description = connection.introspection.get_table_description(cursor, _table_name)
            fields = [row.name for row in table_description]
            setattr(self, f"{_db_source}_{_table_name}", fields)
            return fields

    def get_relation_fields(self, _db_source, _table_name):
        connection = self.get_connection(_db_source)
        types = {'t'}
        with connection.cursor() as cursor:
            if _table_name not in [info.name for info in connection.introspection.get_table_list(cursor) if info.type in types]:
                raise ValidationError(f"没有查询到表{_table_name}")
            relations = connection.introspection.get_relations(cursor, _table_name)
            setattr(self, f"{_db_source}_{_table_name}_relations", relations)
            return relations

    def clean_list_fields(self):
        _list_fields = self.cleaned_data.get("list_fields", "")
        _table_name = self.cleaned_data.get("table_name", "")
        _db_source = self.cleaned_data.get("db_source", "")

        if _list_fields and _table_name and _db_source:
            l_fields = _list_fields.splitlines(keepends=False)

            if len(set(l_fields)) != len(l_fields):
                raise ValidationError("含有重复字段， 请修改")
            db_fields = getattr(self, f"{_db_source}_{_table_name}", "") or self.get_fields(_db_source, _table_name)
            if not db_fields:
                raise ValidationError("未查询到该数据源表字段")
            error_fields = [x for x in l_fields if x not in db_fields]
            if len(error_fields):
                raise ValidationError(f"字段{error_fields}不在数据源中, 可选字段{db_fields}")
            # 修改user填写的字段为 model对应 orm 字段
            self.cleaned_data["list_fields"] = "\n".join([self.normalize_col_name(y) for y in l_fields])
        return self.cleaned_data.get("list_fields")

    def clean_search_fields(self):
        _search_fields = self.cleaned_data.get("search_fields", "")
        _table_name = self.cleaned_data.get("table_name", "")
        _db_source = self.cleaned_data.get("db_source", "")

        if _search_fields and _table_name and _db_source:
            l_fields = _search_fields.splitlines(keepends=False)

            if len(set(l_fields)) != len(l_fields):
                raise ValidationError("含有重复字段， 请修改")
            db_fields = getattr(self, f"{_db_source}_{_table_name}", "") or self.get_fields(_db_source, _table_name)
            if not db_fields:
                raise ValidationError("未查询到该数据源表字段")
            error_fields = [x for x in l_fields if x not in db_fields]
            if len(error_fields):
                raise ValidationError(f"字段{error_fields}不在数据源中")
            # 对于外键字段修改成__id格式
            # TODO 需要后续观察是否有其他问题。
            relations = getattr(self, f"{_db_source}_{_table_name}_relations", "") or self.get_relation_fields(_db_source, _table_name)
            # if not relations:
            #     return self.cleaned_data.get("search_fields")
            new_search_fields = []
            for field in l_fields:
                if field in relations:
                    if field.endswith("_id"):
                        field = field.removesuffix("_id")
                        field += "__id"
                else:
                    field = self.normalize_col_name(field)
                new_search_fields.append(field)

            self.cleaned_data["search_fields"] = "\n".join(new_search_fields)

        return self.cleaned_data.get("search_fields")

    def clean_table_name(self):
        _table_name = self.cleaned_data.get("table_name", "")
        _db_source = self.cleaned_data.get("db_source", "")

        if _db_source and _table_name:
            connection = self.get_connection(_db_source)
            types = {'t'}
            with connection.cursor() as cursor:
                if _table_name not in [info.name for info in connection.introspection.get_table_list(cursor) if
                                       info.type in types]:
                    raise ValidationError(f"没有查询到表{_table_name}")
        return self.cleaned_data.get("table_name")

    def clean_db_source(self):
        db_source = self.cleaned_data.get("db_source", "")
        if not db_source or db_source.startswith("-------"):
            raise ValidationError(f"没有数据库来源，请找管理员申请需要的数据库")
        return self.cleaned_data.get("db_source")

    class Meta:
        model = AdminCustomRecord
        fields = ["db_source", "table_name", "list_fields", "search_fields", "verbose_name"]
