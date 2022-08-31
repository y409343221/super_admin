from rest_framework import serializers

from super_admin.register_table.models import InspectDbRecord


class InspectDbRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectDbRecord
        fields = "__all__"
