import requests
import logging
from django.conf import settings
from django.contrib.admin import AdminSite as _AdminSite
from django.contrib.admin import site
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

logger = logging.getLogger("super_admin")


class AdminSite(_AdminSite):
    site_title = gettext_lazy("SuperAdmin")
    site_header = gettext_lazy("Do. Or do not. There is no try.")
    index_title = gettext_lazy("SuperAdmin")

    def __init__(self, *args, **kwargs):
        super(AdminSite, self).__init__(*args, **kwargs)
        self._registry.update(site._registry)  # PART 2

    @method_decorator(never_cache)
    def login(self, request, extra_context=None):
        """
        Displays the login form for the given HttpRequest.
        """

        if request.method == "GET" and self.has_permission(request):
            # Already logged-in, redirect to admin index
            index_path = reverse("admin:index", current_app=self.name)

            return HttpResponseRedirect(index_path)
        url = request.GET.get("next")
        if "sid" in url:
            sid = urlparse.parse_qs(urlparse.urlparse(url).query)["sid"][0]
            rst = requests.get(
                settings.ADMIN_LOGIN_DATA_URL.format(
                    **{"sid": sid, "host": request.get_host()}
                )
            )
            rst = rst.json()
            # user = authenticate(
            #     username=rst["user"], password=None, user_info=rst, auto_create=True
            # )
            user = authenticate(
                username=rst.get("mail", rst["user"] + "@unknown.com"),
                password=None,
                email=rst.get("mail", rst["user"] + "@unknown.com"),
                name=rst.get("display", ""),
                member_of=rst.get("memberOf", ""),
                auto_create=True,
                check_password=False,
            )
            # user = authenticate(username='ysj',
            #                     password="ysj12271", user_info=rst)
            if user:
                login(request, user)
                # if not self.has_permission(request.user):
                index_path = reverse("admin:index", current_app=self.name)
                return HttpResponseRedirect(index_path)
            else:
                return HttpResponseForbidden(
                    content="403: Not found User: " + "sso user"
                )

        else:
            # settings.ADMIN_LOGIN_URL = settings.ADMIN_LOGIN_URL.format(
            #     **{'host': request.META['HTTP_HOST']})

            return HttpResponseRedirect(
                settings.ADMIN_LOGIN_URL.format(host=request.get_host())
            )


site = AdminSite()
