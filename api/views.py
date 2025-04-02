from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from .models import Exercise, Routine, RoutinePlan, ExerciseLog, TopDownWeeklyTarget
from .serializers import ExerciseSerializer, RoutineSerializer, RoutinePlanSerializer, ExerciseLogSerializer, TopDownWeeklyTargetSerializer

# Replaced ExerciseListCreate with ExerciseViewSet
class ExerciseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows exercises to be viewed or edited.
    Provides list, create, retrieve, update, partial_update, destroy actions.
    """
    queryset = Exercise.objects.all().order_by('name') # Keep ordering consistent
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Keep same permissions


class RoutineViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows routines to be viewed or edited.
    Provides list, create, retrieve, update, partial_update, destroy actions.
    """
    # queryset = Routine.objects.all().prefetch_related('exercises') # Optimize query by prefetching exercises
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    # Add permission classes as needed, e.g., permissions.IsAuthenticated
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class RoutinePlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows routine plans to be viewed or edited.
    Filters plans based on the logged-in user.
    """
    serializer_class = RoutinePlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the routine plans
        for the currently authenticated user, optionally filtered by date range.
        """
        user = self.request.user
        queryset = RoutinePlan.objects.filter(user=user).select_related('routine')

        # Get date range parameters from the request query string
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        # Apply date range filtering if both parameters are provided
        if start_date and end_date:
            # Add validation here if needed (e.g., check date format)
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset.order_by('date')

    def perform_create(self, serializer):
        # Ensure the plan is created for the logged-in user.
        # The serializer already handles setting the user from context.
        serializer.save()

    # Optional: Add custom logic for update/delete if needed,
    # e.g., ensuring users can only modify their own plans (though get_queryset handles this for retrieve/list).
    # The default ModelViewSet behavior combined with get_queryset and IsAuthenticated
    # generally provides sufficient protection for standard CRUD.


class ExerciseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows exercise logs to be viewed or edited.
    Filters logs based on the logged-in user and optionally by date range.
    Handles creation and updates, ensuring logs are tied to the correct user.
    """
    serializer_class = ExerciseLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return a list of exercise logs for the currently authenticated user,
        optionally filtered by date range.
        """
        user = self.request.user
        queryset = ExerciseLog.objects.filter(user=user).select_related('exercise')

        # Get date range parameters from the request query string
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        # Apply date range filtering if both parameters are provided
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        elif start_date: # Filter by a single date if only start_date is provided
             queryset = queryset.filter(date=start_date)


        return queryset.order_by('date', 'exercise__name')

    def perform_create(self, serializer):
        # The serializer's create method handles setting the user and get_or_create logic.
        # We pass the request context to the serializer.
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure users can only update their own logs.
        # The get_queryset method already filters by user, so direct updates are safe.
        serializer.save()

    # We might want a specific endpoint or action to handle bulk updates or creation
    # based on a date and completed status, especially for the checkbox interaction.
    # For now, the standard ModelViewSet POST/PUT/PATCH should work for individual logs.
    # The serializer's create method uses get_or_create, so POST can function as an upsert.


class TopDownWeeklyTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows top-down weekly targets to be viewed or edited.
    Filters targets based on the logged-in user.
    """
    serializer_class = TopDownWeeklyTargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the top-down weekly targets
        for the currently authenticated user, optionally filtered by year and week.
        """
        user = self.request.user
        queryset = TopDownWeeklyTarget.objects.filter(user=user)

        # Get year and week parameters from the request query string
        year = self.request.query_params.get('year', None)
        week = self.request.query_params.get('week', None)

        # Apply filtering if parameters are provided
        if year:
            queryset = queryset.filter(year=year)
        if week:
            queryset = queryset.filter(week=week)

        return queryset.order_by('year', 'week')

    def perform_create(self, serializer):
        # The serializer's create method handles setting the user and update_or_create logic.
        # We pass the request context to the serializer.
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure users can only update their own targets.
        # The get_queryset method already filters by user, so direct updates are safe.
        serializer.save()
