# Super Admin

本项目可以通过配置多个数据库, 生成对应的models和admin。


## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

#### 系统管理员
-  创建系统管理员命令

        $ python manage.py createsuperuser
        
-  只有系统管理员可以查看和修改inspectdb的数据。

### 系统初始化

数据库迁移

    $ python manage.py migrate

### 操作流程

-  在config.settings.base.py中配置新数据源（三个配置）

    
    DATABASES = {
        "akso_test": env.db("AKSO_DATABASE_URL"),
    }
    
    EXTRA_DB_APPS_MAPPING = {
        "akso_test": "akso_test",
    }
    
    DB_SOURCE_MAP = (
    ("akso_test", "手机端报销测试库"),
)
    
-  创建app
    
    
    $ python manage.py auto_createapp --database=xxx

-  生成models

    ##### 指定生成某个db的models， 不指定则全部生成（不建议）。
    
    $ python manage.py auto_inspectdb --databases=xxx
    
-  在[admin管理后台](http://127.0.0.1:8000/admin)中填写需要查询的数据源，字段等。
   
   
-  生成admin文件


    $ python manage.py auto_createadmin 'table_name'
    $ python manage.py makemigrations
    $ python manage.py migrate

