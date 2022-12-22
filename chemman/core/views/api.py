from rest_framework import permissions, viewsets

from ..models.storage import (
    Storage, StoragePlace, StoredPackage
)
from ..serializers import (
    StorageSerializer, StoragePlaceSerializer, StoredPackageSerializer
)


class StorageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer
    permission_classes = [permissions.IsAuthenticated]


class StoragePlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StoragePlace.objects.all()
    serializer_class = StoragePlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = super().get_queryset()
        storage = self.request.GET.get('storage', '')
        if storage:
            query = query.filter(storage__id=int(storage))
        return query


class StoredPackageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StoredPackage.objects.all()
    serializer_class = StoredPackageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = super().get_queryset()
        place = self.request.GET.get('place', '')
        if place:
            query = query.filter(place__id=int(place))
        return query
