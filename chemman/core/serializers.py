from rest_framework import serializers

from .models.chems import Chemical
from .models.storage import (
    Storage, StoragePlace, StoredChemical, StoredPackage
)


class StorageSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Storage
        fields = ['id', 'name', 'department', 'type', 'lockable']


class StoragePlaceSerializer(serializers.ModelSerializer):
    storage = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StoragePlace
        fields = ['id', 'name', 'lockable', 'storage']


# Only to have this information in the Package
class SimpleChemicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chemical
        fields = ['id', 'display_name', 'formula', 'molar_mass']


class StoredChemicalSerializer(serializers.ModelSerializer):
    chemical = SimpleChemicalSerializer(read_only=True)

    class Meta:
        model = StoredChemical
        fields = ['id', 'chemical', 'name_extra', 'quality']


class StoredPackageSerializer(serializers.ModelSerializer):
    place = StoragePlaceSerializer(read_only=True)
    stored_chemical = StoredChemicalSerializer(read_only=True)

    class Meta:
        model = StoredPackage
        fields = [
            'id', 'place', 'package_id', 'content', 'unit', 'stored_chemical'
        ]
