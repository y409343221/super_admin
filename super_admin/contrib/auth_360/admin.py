from django.contrib import admin

from super_admin.contrib.auth_360.sites import AdminSite

site = AdminSite()
admin.site = site
