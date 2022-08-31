from rest_framework import routers

from super_admin.register_table.views import *

router = routers.DefaultRouter()
router.register(r"model_names", InspectDbRecordViewSet, basename="model_names")

urlpatterns = router.urls
