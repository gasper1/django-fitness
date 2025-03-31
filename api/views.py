from rest_framework import generics, viewsets, permissions
from .models import Exercise, Routine
from .serializers import ExerciseSerializer, RoutineSerializer

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


# Create your views here. - This comment can be removed or kept
