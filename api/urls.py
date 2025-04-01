from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseListCreate, RoutineViewSet, RoutinePlanViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'routines', RoutineViewSet, basename='routine')
router.register(r'routine-plans', RoutinePlanViewSet, basename='routineplan')

# The API URLs are now determined automatically by the router.
# Additionally, we include the existing exercise URL pattern.
urlpatterns = [
    path('exercises/', ExerciseListCreate.as_view(), name='exercise-list-create'),
    path('', include(router.urls)), # Include the router's URLs
    # Add other API endpoints for the 'api' app here if needed
]
