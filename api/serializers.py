from django.contrib.auth.models import User # Import the User model
from rest_framework import serializers
from .models import Exercise, Routine, RoutinePlan, ExerciseLog, TopDownWeeklyTarget

class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for the Exercise model."""
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'activity', 'type', 'muscle_group', 'sub_group', 'training_points'] # Include all relevant fields
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


class ExerciseLogSerializer(serializers.ModelSerializer):
    """Serializer for the ExerciseLog model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = ExerciseLog
        fields = ['id', 'user', 'exercise', 'exercise_name', 'date', 'completed']
        read_only_fields = ['id', 'user', 'exercise_name']

    def create(self, validated_data):
        # Automatically set the user to the request user
        validated_data['user'] = self.context['request'].user
        # Use get_or_create to handle the unique_together constraint gracefully
        # This allows for updating the 'completed' status if an entry already exists
        instance, created = ExerciseLog.objects.get_or_create(
            user=validated_data['user'],
            exercise=validated_data['exercise'],
            date=validated_data['date'],
            defaults={'completed': validated_data.get('completed', False)}
        )
        # If the instance was not created (it already existed), update 'completed' status
        if not created:
            instance.completed = validated_data.get('completed', instance.completed)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        # Standard update logic, but user, exercise, and date shouldn't change
        # Only 'completed' status should be updatable via PUT/PATCH
        instance.completed = validated_data.get('completed', instance.completed)
        instance.save()
        return instance


class TopDownWeeklyTargetSerializer(serializers.ModelSerializer):
    """Serializer for the TopDownWeeklyTarget model."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TopDownWeeklyTarget
        fields = ['id', 'user', 'year', 'week', 'target_points']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        # Automatically set the user to the request user
        validated_data['user'] = self.context['request'].user
        # Use update_or_create to handle the unique_together constraint gracefully
        # This allows creating or updating the target for a given user, year, and week
        instance, created = TopDownWeeklyTarget.objects.update_or_create(
            user=validated_data['user'],
            year=validated_data['year'],
            week=validated_data['week'],
            defaults={'target_points': validated_data.get('target_points', 50)} # Use default if not provided
        )
        return instance

    def update(self, instance, validated_data):
        # Only 'target_points' should be updatable via PUT/PATCH
        instance.target_points = validated_data.get('target_points', instance.target_points)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model, used for registration."""
    password = serializers.CharField(write_only=True) # Password should not be read

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name') # Include fields you want for registration
        extra_kwargs = {'password': {'write_only': True}} # Ensure password is write-only

    def create(self, validated_data):
        # Create the user instance using the create_user method to handle password hashing
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''), # Optional email
            first_name=validated_data.get('first_name', ''), # Optional first name
            last_name=validated_data.get('last_name', '') # Optional last name
        )
        return user
