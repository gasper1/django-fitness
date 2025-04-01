from rest_framework import serializers
from .models import Exercise, Routine, RoutinePlan

class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for the Exercise model."""
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'activity', 'type', 'muscle_group', 'sub_group'] # Include all relevant fields
        read_only_fields = ['id'] # ID is typically read-only


class RoutineSerializer(serializers.ModelSerializer):
    """Serializer for the Routine model."""
    # Use PrimaryKeyRelatedField for writing, allowing updates with exercise IDs
    exercises = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        many=True,
    #     write_only=False # Keep write_only=False to allow reading the IDs as well if needed, or set to True if only writing IDs
    )
    # # Optionally, include a nested serializer for read operations if you want detailed exercise info
    exercises_details = ExerciseSerializer(many=True, read_only=True, source='exercises')


    class Meta:
        model = Routine
        # Adjust fields based on whether you include exercises_details
        # fields = ['id', 'name', 'exercises', 'exercises_details']
        fields = ['id', 'name', 'exercises', 'exercises_details']
        # read_only_fields = ['id', 'exercises_details'] # exercises_details is read-only

    # If you want to return the full exercise details upon creation/update,
    # you might override create/update or use a different serializer for read vs write.
    # For simplicity, this setup uses IDs for writing and includes details for reading via exercises_details.


class RoutinePlanSerializer(serializers.ModelSerializer):
    """Serializer for the RoutinePlan model."""
    # Display routine name for readability
    routine_name = serializers.CharField(source='routine.name', read_only=True)
    # Use ID for writing AND include it in reading
    routine = serializers.PrimaryKeyRelatedField(queryset=Routine.objects.all()) # Removed write_only=True
    # User is set automatically based on the request user, so it's read-only here
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RoutinePlan
        fields = ['id', 'user', 'routine', 'routine_name', 'date']
        read_only_fields = ['id', 'user', 'routine_name']

    def create(self, validated_data):
        # Automatically set the user to the request user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
