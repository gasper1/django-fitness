from rest_framework import generics
from .models import Exercise
from .serializers import ExerciseSerializer

class ExerciseListCreate(generics.ListCreateAPIView):
    """
    API view to retrieve list of exercises or create a new exercise.
    * Requires token authentication.
    * All users can access this view.
    """
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    # Add permission classes if needed, e.g.:
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Create your views here. - This comment can be removed or kept
