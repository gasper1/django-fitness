from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from .models import Exercise, Routine, RoutinePlan
from .serializers import ExerciseSerializer, RoutineSerializer, RoutinePlanSerializer

class ExerciseListCreate(generics.ListCreateAPIView):
    """
    API view to retrieve list of exercises or create a new exercise.
    * Requires token authentication.
    * All users can access this view.
    """
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    # Add permission classes if needed, e.g.:
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


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
