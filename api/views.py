from rest_framework import generics, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils.timezone import now
from datetime import datetime, timedelta
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


class WeeklyStatsViewSet(viewsets.ViewSet):
    """ViewSet for providing aggregated fitness statistics."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def kpi_summary(self, request):
        """Return KPI summary for a specified week range."""
        # Get parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate metrics
        user = request.user

        # Get weekly target
        try:
            date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            iso_year = date_obj.isocalendar()[0]
            iso_week = date_obj.isocalendar()[1]

            weekly_target = TopDownWeeklyTarget.objects.get(
                user=user,
                year=iso_year,
                week=iso_week
            )
            target_points = weekly_target.target_points
        except TopDownWeeklyTarget.DoesNotExist:
            target_points = 50  # Default

        # Get planned routines
        routine_plans = RoutinePlan.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).select_related('routine')

        # Calculate planned points
        planned_points = 0
        for plan in routine_plans:
            exercises = plan.routine.exercises.all()
            planned_points += sum(e.training_points for e in exercises)

        # Get completed exercises
        completed_logs = ExerciseLog.objects.filter(
            user=user,
            date__range=[start_date, end_date],
            completed=True
        ).select_related('exercise')

        # Calculate completed points
        completed_points = sum(log.exercise.training_points for log in completed_logs)

        # Calculate daily metrics
        daily_metrics = {}
        current_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')

            # Get routine for this day
            try:
                routine_plan = RoutinePlan.objects.get(user=user, date=date_str)
                routine = routine_plan.routine
                day_planned_points = sum(e.training_points for e in routine.exercises.all())
            except RoutinePlan.DoesNotExist:
                routine = None
                day_planned_points = 0

            # Get completed exercises for this day
            day_logs = [log for log in completed_logs if log.date.strftime('%Y-%m-%d') == date_str]
            day_completed_points = sum(log.exercise.training_points for log in day_logs)

            daily_metrics[date_str] = {
                'planned_points': day_planned_points,
                'completed_points': day_completed_points,
                'achievement_percentage': round((day_completed_points / day_planned_points * 100) if day_planned_points > 0 else 0)
            }

            current_date += timedelta(days=1)

        # Calculate overall achievements
        planning_achievement = round((planned_points / target_points * 100) if target_points > 0 else 0)
        training_achievement = round((completed_points / target_points * 100) if target_points > 0 else 0)

        return Response({
            'weekly_target': target_points,
            'planned_points': planned_points,
            'completed_points': completed_points,
            'planning_achievement': planning_achievement,
            'training_achievement': training_achievement,
            'daily_metrics': daily_metrics
        })

    @action(detail=False, methods=['get'])
    def historical_stats(self, request):
        """Return historical weekly stats for dashboard visualization."""
        # Get parameters for how many weeks to look back
        weeks_back = int(request.query_params.get('weeks_back', 6))

        user = request.user
        current_date = now().date()

        # Calculate stats for each week going back
        weekly_stats = []

        for i in range(weeks_back):
            # Calculate the start and end dates for this week
            week_end = current_date - timedelta(days=current_date.weekday() + 7*i)
            week_start = week_end - timedelta(days=6)

            # ISO week data for target lookup
            iso_year = week_start.isocalendar()[0]
            iso_week = week_start.isocalendar()[1]

            # Get weekly target
            try:
                weekly_target = TopDownWeeklyTarget.objects.get(
                    user=user,
                    year=iso_year,
                    week=iso_week
                )
                target_points = weekly_target.target_points
            except TopDownWeeklyTarget.DoesNotExist:
                target_points = 50  # Default

            # Get planned points for this week
            routine_plans = RoutinePlan.objects.filter(
                user=user,
                date__range=[week_start, week_end]
            ).select_related('routine')

            planned_points = 0
            for plan in routine_plans:
                exercises = plan.routine.exercises.all()
                planned_points += sum(e.training_points for e in exercises)

            # Get completed points for this week
            completed_logs = ExerciseLog.objects.filter(
                user=user,
                date__range=[week_start, week_end],
                completed=True
            ).select_related('exercise')

            completed_points = sum(log.exercise.training_points for log in completed_logs)

            # Calculate achievement percentage
            achievement_percentage = round((completed_points / target_points * 100) if target_points > 0 else 0)

            week_label = f"Week {iso_week}"
            weekly_stats.append({
                'week': week_label,
                'planned': planned_points,
                'completed': completed_points,
                'weeklyTarget': target_points,
                'achievementPercentage': achievement_percentage
            })

        # Reverse to show oldest to newest
        weekly_stats.reverse()

        return Response(weekly_stats)
