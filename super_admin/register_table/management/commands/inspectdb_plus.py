import keyword
import re
import os
import pathlib
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models.constants import LOOKUP_SEP

from django.conf import settings
from super_admin.register_table.models import InspectDbRecord


class Command(BaseCommand):
    help = "Introspects the database tables in the given database and outputs a Django model module."
    requires_system_checks = []
    stealth_options = ('table_name_filter',)
    db_module = 'django.db'

    def add_arguments(self, parser):
        parser.add_argument(
            'table', nargs='*', type=str,
            help='Selects what tables or views should be introspected.',
        )
        parser.add_argument(
            '--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a database to introspect. Defaults to using the "default" database.',
        )
        parser.add_argument(
            '--include-partitions', action='store_true', help='Also output models for partition tables.',
        )
        parser.add_argument(
            '--include-views', action='store_true', help='Also output models for database views.',
        )
        parser.add_argument(
            '--clear_model', type=bool, default=False, help='clear old model file'
        )

    def save_record(self, **kwargs):
        InspectDbRecord.objects.filter(
            db_source=kwargs["database"],
            model_name=kwargs["table"],
            is_changed="N"
        ).delete()
        instance = InspectDbRecord(
            db_source=kwargs["database"],
            model_name=kwargs["table"],
            inspectdb_records=kwargs["inspectdb_records"]
        )
        instance.save()

    # def compare_old_version(self, options):
    #     if options["table"] == "":
    #         pass
    #     else:
    #         exclude_labels = ["register_table", "users"]
    #         labels = [x.split(".")[-1] for x in settings.LOCAL_APPS if x.split(".")[-1] not in exclude_labels]
    #         for label in labels:
    #             models = list(apps.get_app_config(label).get_models())
    #             if not len(models):
    #                 raise CommandError("Must inspectdb first")
    #             for model in models:
    #                 options["table"] = [model._meta.original_attrs["db_table"]]
    #                 save_inspectdb_records = ""
    #                 for line in self.handle_inspection(options):
    #                     self.stdout.write(line)
    #                     if line.endswith("\n"):
    #                         save_inspectdb_records = save_inspectdb_records + "\n" + line
    #                 self.save_record(
    #                     database=options["database"],
    #                     table=model._meta.original_attrs["db_table"],
    #                     inspectdb_records=save_inspectdb_records
    #                     )

    def handle(self, **options):
        """
        :param options:
                    options = {
                            "verbosity": 1,
                            "settings": None,
                            "pythonpath": None,
                            "traceback": False,
                            "no_color": False,
                            "force_color": False,
                            "table": ["users_user"],
                            "database": "default",
                            "include_partitions": False,
                            "include_views": False,
                        }
        :return:
        """
        try:
            if options["clear_model"]:
                exclude_labels = ["users", "register_table"]
                app_name = [k for k, v in settings.DATABASE_APPS_MAPPING.items() if v == options["database"]]
                if not len(app_name):
                    raise CommandError("Can not find app with db[%s]" % options["database"])
                app_name = app_name[0]
                if app_name in exclude_labels:
                    raise CommandError("Can not clear app model in %s" % exclude_labels)

                model_path = settings.ROOT_DIR / "super_admin" / app_name / "models.py"
                try:
                    with open(model_path, "w") as f:
                        f.write("")
                except FileNotFoundError as e:
                    raise CommandError(str(e))
                    # raise CommandError("No such file %s" % model_path)
            else:
                for line in self.handle_inspection(options):
                    self.stdout.write(line)
                # print(line)

        except NotImplementedError:
            raise CommandError("Database inspection isn't supported for the currently selected database backend.")

    def handle_inspection(self, options):
        connection = connections[options['database']]
        # 'table_name_filter' is a stealth option
        table_name_filter = options.get('table_name_filter')

        def table2model(table_name):
            return re.sub(r'[^a-zA-Z0-9]', '', table_name.title())

        with connection.cursor() as cursor:
            yield 'from %s import models' % self.db_module
            known_models = []
            table_info = connection.introspection.get_table_list(cursor)

            # Determine types of tables and/or views to be introspected.
            types = {'t'}
            if options['include_partitions']:
                types.add('p')
            if options['include_views']:
                types.add('v')
            exclude_records = InspectDbRecord.objects.filter(
                db_source=options["database"],
                is_changed="Y",
            ).values("model_name", "inspectdb_records")
            exclude_table_names = [_record["model_name"] for _record in exclude_records]
            for table_name in (options['table'] or sorted(info.name for info in table_info if info.type in types)):
                if table_name in exclude_table_names:
                    for record in exclude_records:
                        if record["model_name"] == table_name:
                            yield ''
                            yield ''
                            yield record["inspectdb_records"]
                            break
                    continue
                if table_name_filter is not None and callable(table_name_filter):
                    if not table_name_filter(table_name):
                        continue
                try:
                    try:
                        relations = connection.introspection.get_relations(cursor, table_name)
                    except NotImplementedError:
                        relations = {}
                    try:
                        constraints = connection.introspection.get_constraints(cursor, table_name)
                    except NotImplementedError:
                        constraints = {}
                    primary_key_column = connection.introspection.get_primary_key_column(cursor, table_name)
                    unique_columns = [
                        c['columns'][0] for c in constraints.values()
                        if c['unique'] and len(c['columns']) == 1
                    ]
                    table_description = connection.introspection.get_table_description(cursor, table_name)
                except Exception as e:
                    yield "# Unable to inspect table '%s'" % table_name
                    yield "# The error was: %s" % e
                    continue

                orm_model = ""
                yield ''
                yield ''
                yield 'class %s(models.Model):\n' % table2model(table_name)
                orm_model += "%s" % 'class %s(models.Model):\n' % table2model(table_name)
                known_models.append(table2model(table_name))
                used_column_names = []  # Holds column names used in the table so far
                column_to_field_name = {}  # Maps column names to names of model fields
                for row in table_description:
                    comment_notes = []  # Holds Field notes, to be displayed in a Python comment.
                    extra_params = {}  # Holds Field parameters such as 'db_column'.
                    column_name = row.name
                    is_relation = column_name in relations

                    att_name, params, notes = self.normalize_col_name(
                        column_name, used_column_names, is_relation)
                    extra_params.update(params)
                    comment_notes.extend(notes)

                    used_column_names.append(att_name)
                    column_to_field_name[column_name] = att_name

                    # Add primary_key and unique, if necessary.
                    if column_name == primary_key_column:
                        extra_params['primary_key'] = True
                    elif column_name in unique_columns:
                        extra_params['unique'] = True

                    if is_relation:
                        if extra_params.pop('unique', False) or extra_params.get('primary_key'):
                            rel_type = 'OneToOneField'
                        else:
                            rel_type = 'ForeignKey'
                        rel_to = (
                            "self" if relations[column_name][1] == table_name
                            else table2model(relations[column_name][1])
                        )
                        if rel_to in known_models:
                            field_type = '%s(%s' % (rel_type, rel_to)
                        else:
                            field_type = "%s('%s'" % (rel_type, rel_to)
                    else:
                        # Calling `get_field_type` to get the field type string and any
                        # additional parameters and notes.
                        field_type, field_params, field_notes = self.get_field_type(connection, table_name, row)
                        extra_params.update(field_params)
                        comment_notes.extend(field_notes)

                        field_type += '('

                    # Don't output 'id = meta.AutoField(primary_key=True)', because
                    # that's assumed if it doesn't exist.
                    if att_name == 'id' and extra_params == {'primary_key': True}:
                        if field_type == 'AutoField(':
                            continue
                        elif field_type == connection.features.introspected_field_types['AutoField'] + '(':
                            comment_notes.append('AutoField?')

                    # Add 'null' and 'blank', if the 'null_ok' flag was present in the
                    # table description.
                    if row.null_ok:  # If it's NULL...
                        extra_params['blank'] = True
                        extra_params['null'] = True

                    field_desc = '%s = %s%s' % (
                        att_name,
                        # Custom fields will have a dotted path
                        '' if '.' in field_type else 'models.',
                        field_type,
                    )
                    if field_type.startswith(('ForeignKey(', 'OneToOneField(')):
                        field_desc += ', models.DO_NOTHING'

                    if extra_params:
                        if not field_desc.endswith('('):
                            field_desc += ', '
                        field_desc += ', '.join('%s=%r' % (k, v) for k, v in extra_params.items())
                    field_desc += ')'
                    if comment_notes:
                        field_desc += '  # ' + ' '.join(comment_notes)
                    yield '    %s\n' % field_desc
                    orm_model += '    %s\n' % field_desc
                is_view = any(info.name == table_name and info.type == 'v' for info in table_info)
                is_partition = any(info.name == table_name and info.type == 'p' for info in table_info)
                yield from self.get_meta(table_name, constraints, column_to_field_name, is_view, is_partition)
                for x in self.get_meta(table_name, constraints, column_to_field_name, is_view, is_partition):
                    orm_model += "%s" % x
                self.save_record(database=options["database"], table=table_name, inspectdb_records=orm_model)

    def normalize_col_name(self, col_name, used_column_names, is_relation):
        """
        Modify the column name to make it Python-compatible as a field name
        """
        field_params = {}
        field_notes = []

        new_name = col_name.lower()
        if new_name != col_name:
            field_notes.append('Field name made lowercase.')

        if is_relation:
            if new_name.endswith('_id'):
                new_name = new_name[:-3]
            else:
                field_params['db_column'] = col_name

        new_name, num_repl = re.subn(r'\W', '_', new_name)
        if num_repl > 0:
            field_notes.append('Field renamed to remove unsuitable characters.')

        if new_name.find(LOOKUP_SEP) >= 0:
            while new_name.find(LOOKUP_SEP) >= 0:
                new_name = new_name.replace(LOOKUP_SEP, '_')
            if col_name.lower().find(LOOKUP_SEP) >= 0:
                # Only add the comment if the double underscore was in the original name
                field_notes.append("Field renamed because it contained more than one '_' in a row.")

        if new_name.startswith('_'):
            new_name = 'field%s' % new_name
            field_notes.append("Field renamed because it started with '_'.")

        if new_name.endswith('_'):
            new_name = '%sfield' % new_name
            field_notes.append("Field renamed because it ended with '_'.")

        if keyword.iskeyword(new_name):
            new_name += '_field'
            field_notes.append('Field renamed because it was a Python reserved word.')

        if new_name[0].isdigit():
            new_name = 'number_%s' % new_name
            field_notes.append("Field renamed because it wasn't a valid Python identifier.")

        if new_name in used_column_names:
            num = 0
            while '%s_%d' % (new_name, num) in used_column_names:
                num += 1
            new_name = '%s_%d' % (new_name, num)
            field_notes.append('Field renamed because of name conflict.')

        if col_name != new_name and field_notes:
            field_params['db_column'] = col_name

        return new_name, field_params, field_notes

    def get_field_type(self, connection, table_name, row):
        """
        Given the database connection, the table name, and the cursor row
        description, this routine will return the given field type name, as
        well as any additional keyword parameters and notes for the field.
        """
        field_params = {}
        field_notes = []

        try:
            field_type = connection.introspection.get_field_type(row.type_code, row)
        except KeyError:
            field_type = 'TextField'
            field_notes.append('This field type is a guess.')

        # Add max_length for all CharFields.
        if field_type == 'CharField' and row.internal_size:
            field_params['max_length'] = int(row.internal_size)

        if field_type in {'CharField', 'TextField'} and row.collation:
            field_params['db_collation'] = row.collation

        if field_type == 'DecimalField':
            if row.precision is None or row.scale is None:
                field_notes.append(
                    'max_digits and decimal_places have been guessed, as this '
                    'database handles decimal fields as float')
                field_params['max_digits'] = row.precision if row.precision is not None else 10
                field_params['decimal_places'] = row.scale if row.scale is not None else 5
            else:
                field_params['max_digits'] = row.precision
                field_params['decimal_places'] = row.scale

        return field_type, field_params, field_notes

    def get_meta(self, table_name, constraints, column_to_field_name, is_view, is_partition):
        """
        Return a sequence comprising the lines of code necessary
        to construct the inner Meta class for the model corresponding
        to the given database table name.
        """
        unique_together = []
        has_unsupported_constraint = False
        for params in constraints.values():
            if params['unique']:
                columns = params['columns']
                if None in columns:
                    has_unsupported_constraint = True
                columns = [x for x in columns if x is not None]
                if len(columns) > 1:
                    unique_together.append(str(tuple(column_to_field_name[c] for c in columns)))
        if is_view:
            managed_comment = "  # Created from a view. Don't remove."
        elif is_partition:
            managed_comment = "  # Created from a partition. Don't remove."
        else:
            managed_comment = ''
        meta = ['']
        if has_unsupported_constraint:
            meta.append('    # A unique constraint could not be introspected.')
        meta += [
            '    class Meta:\n',
            '        managed = False%s\n' % managed_comment,
            '        db_table = %r\n' % table_name
        ]
        if unique_together:
            tup = '(' + ', '.join(unique_together) + ',)'
            meta += ["        unique_together = %s\n" % tup]
        return meta