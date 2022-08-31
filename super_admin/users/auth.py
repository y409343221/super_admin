from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from rest_auth.models import TokenModel
from rest_framework import HTTP_HEADER_ENCODING, exceptions, serializers
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import (
    SessionAuthentication as _SessionAuthentication,
)
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed


class SSOAuthBackend(ModelBackend):
    def authenticate(
        self,
        request=None,
        username=None,
        email=None,
        password=None,
        name=None,
        member_of=None,
        auto_create=False,
        check_password=True,
        **kwargs
    ):

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if not auto_create:
                return
            is_superuser = False
            if username in [admin[0].lower() for admin in settings.ADMINS]:
                is_superuser = True
            user = User(
                username=username,
                password="asdfghjkl1",
                is_staff=True,
                is_superuser=is_superuser,
                email=email,
                name=name,
                member_of=member_of,
            )
            user.save()
        # user.get_or_create_token()
        if not user.is_superuser:
            try:
                group = Group.objects.get(name="base_permission")
            except Group.DoesNotExist:
                group = Group.objects.create(name="base_permission")
                group.save()
                register_base_permissions = [
                    "add_admincustomrecord",
                    "change_admincustomrecord",
                    "delete_admincustomrecord",
                    "view_admincustomrecord",
                ]
                permissions = Permission.objects.filter(codename__in=register_base_permissions)
                for permission in permissions:
                    group.permissions.add(permission)
            if not user.groups.filter(name="base_permission").exists():
                user.groups.add(group.id)

        if check_password:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        else:
            return user
