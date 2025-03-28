from django.urls import path
from .views import ExerciseListCreate

urlpatterns = [
    path('exercises/', ExerciseListCreate.as_view(), name='exercise-list-create'),
    # Add other API endpoints for the 'api' app here if needed
]
