from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from super_admin.register_table.models import InspectDbRecord
from super_admin.register_table.serializers import InspectDbRecordSerializer


class InspectDbRecordFilter(filters.FilterSet):

    db_source = filters.CharFilter(
        field_name="db_source", lookup_expr="exact"
    )

    class Meta:
        model = InspectDbRecord
        fields = ["db_source"]


class InspectDbRecordViewSet(ModelViewSet):
    queryset = InspectDbRecord.objects.all()
    serializer_class = InspectDbRecordSerializer
    filterset_class = InspectDbRecordFilter
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def records(self, request, pk=None):

        db_source = request.GET.get('db_source', '')
        if not db_source:
            return Response(data={})
        result = InspectDbRecord.objects.filter(db_source=db_source).values()
        return Response(data={"model_names": result})


