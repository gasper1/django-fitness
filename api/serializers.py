from rest_framework import serializers
from .models import Exercise

class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for the Exercise model."""
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'activity', 'type', 'muscle_group', 'sub_group'] # Include all relevant fields
        read_only_fields = ['id'] # ID is typically read-only
