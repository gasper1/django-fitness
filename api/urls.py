from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import ExerciseViewSet instead of ExerciseListCreate
from .views import ExerciseViewSet, RoutineViewSet, RoutinePlanViewSet, ExerciseLogViewSet, TopDownWeeklyTargetViewSet, WeeklyStatsViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
# Register ExerciseViewSet
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'routines', RoutineViewSet, basename='routine')
router.register(r'routine-plans', RoutinePlanViewSet, basename='routineplan')
router.register(r'exercise-logs', ExerciseLogViewSet, basename='exerciselog')
router.register(r'weekly-targets', TopDownWeeklyTargetViewSet, basename='weeklytarget')
router.register(r'weekly-stats', WeeklyStatsViewSet, basename='weeklystats')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    # Remove the old path for ExerciseListCreate
    path('', include(router.urls)), # Include the router's URLs
    # Add other API endpoints for the 'api' app here if needed
]
