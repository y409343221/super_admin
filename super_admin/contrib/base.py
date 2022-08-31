from django.db import models
from django.conf import settings


ACTIVE_FLAG_Y = "Y"
ACTIVE_FLAG_N = "N"

ACTIVE_FLAG_CHOICES = (("Y", ACTIVE_FLAG_Y), ("N", ACTIVE_FLAG_N))


class BaseModel(models.Model):
    # user_model = get_user_model()

    active_flag = models.CharField(
        max_length=1, choices=ACTIVE_FLAG_CHOICES, default=ACTIVE_FLAG_Y
    )
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_created_by",
        db_column="created_by",
        blank=True,
        null=True,
        db_constraint=False,
    )
    last_updated_date = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="%(class)s_last_updated_by",
        db_column="last_updated_by",
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True
