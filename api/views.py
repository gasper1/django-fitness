from rest_framework import generics, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Exercise, Routine, RoutinePlan, ExerciseLog, TopDownWeeklyTarget
from .serializers import ExerciseSerializer, RoutineSerializer, RoutinePlanSerializer, ExerciseLogSerializer, TopDownWeeklyTargetSerializer
from datetime import date, timedelta

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
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def historical_stats(self, request):
        weeks_back = int(request.query_params.get('weeks_back', 6))
        user = request.user

        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())

        result = []
        for i in range(weeks_back - 1, -1, -1):
            week_start = current_week_start - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            iso = week_start.isocalendar()
            year, week_num = iso[0], iso[1]

            try:
                target_obj = TopDownWeeklyTarget.objects.get(user=user, year=year, week=week_num)
                weekly_target = target_obj.target_points
            except TopDownWeeklyTarget.DoesNotExist:
                weekly_target = 0

            plans = RoutinePlan.objects.filter(
                user=user, date__range=[week_start, week_end]
            ).prefetch_related('routine__exercises')
            planned_points = sum(
                ex.training_points
                for plan in plans
                for ex in plan.routine.exercises.all()
            )

            logs = ExerciseLog.objects.filter(
                user=user, date__range=[week_start, week_end], completed=True
            ).select_related('exercise')
            completed_points = sum(log.exercise.training_points for log in logs)

            achievement = round(completed_points / weekly_target * 100, 1) if weekly_target > 0 else 0

            result.append({
                'week': f"W{week_num:02d} {year}",
                'planned': planned_points,
                'completed': completed_points,
                'weeklyTarget': weekly_target,
                'achievementPercentage': achievement,
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def kpi_summary(self, request):
        user = request.user
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({'error': 'start_date and end_date are required'}, status=status.HTTP_400_BAD_REQUEST)

        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        iso = start_date.isocalendar()
        year, week_num = iso[0], iso[1]

        try:
            target_obj = TopDownWeeklyTarget.objects.get(user=user, year=year, week=week_num)
            weekly_target = target_obj.target_points
        except TopDownWeeklyTarget.DoesNotExist:
            weekly_target = 0

        plans = RoutinePlan.objects.filter(
            user=user, date__range=[start_date, end_date]
        ).prefetch_related('routine__exercises')
        logs = ExerciseLog.objects.filter(
            user=user, date__range=[start_date, end_date]
        ).select_related('exercise')

        daily_metrics = {}
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            day_planned = sum(
                ex.training_points
                for p in plans if p.date == current
                for ex in p.routine.exercises.all()
            )
            day_completed = sum(
                l.exercise.training_points for l in logs
                if l.date == current and l.completed
            )
            day_achievement = round(day_completed / day_planned * 100, 1) if day_planned > 0 else 0
            daily_metrics[date_str] = {
                'planned_points': day_planned,
                'completed_points': day_completed,
                'achievement_percentage': day_achievement,
            }
            current += timedelta(days=1)

        total_planned = sum(m['planned_points'] for m in daily_metrics.values())
        total_completed = sum(m['completed_points'] for m in daily_metrics.values())
        planning_achievement = round(total_planned / weekly_target * 100, 1) if weekly_target > 0 else 0
        training_achievement = round(total_completed / total_planned * 100, 1) if total_planned > 0 else 0

        return Response({
            'weekly_target': weekly_target,
            'planned_points': total_planned,
            'completed_points': total_completed,
            'planning_achievement': planning_achievement,
            'training_achievement': training_achievement,
            'daily_metrics': daily_metrics,
        })
