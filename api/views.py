import anthropic
import json
import os
from datetime import date, datetime, timedelta

from django.db.models import F, Max
from rest_framework import generics, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Exercise, Routine, RoutinePlan, ExerciseLog, ExerciseSet, TopDownWeeklyTarget, WeeklyAnalysis
from .serializers import ExerciseSerializer, RoutineSerializer, RoutinePlanSerializer, ExerciseLogSerializer, ExerciseSetSerializer, TopDownWeeklyTargetSerializer

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    serializer_class = RoutineSerializer

    def get_queryset(self):
        return Routine.objects.prefetch_related('exercises')


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
        queryset = RoutinePlan.objects.filter(user=user).select_related('routine').prefetch_related('routine__exercises')

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
        queryset = ExerciseLog.objects.filter(user=user).select_related('exercise').prefetch_related('sets')

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


class ExerciseSetViewSet(viewsets.ModelViewSet):
    """CRUD for individual sets within an ExerciseLog. set_number is backend-assigned."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExerciseSetSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return ExerciseSet.objects.filter(exercise_log__user=self.request.user).order_by('set_number')

    def perform_create(self, serializer):
        exercise_log = serializer.validated_data['exercise_log']
        if exercise_log.user != self.request.user:
            raise PermissionDenied()
        max_num = ExerciseSet.objects.filter(exercise_log=exercise_log).aggregate(
            m=Max('set_number')
        )['m'] or 0
        serializer.save(set_number=max_num + 1)

    def perform_destroy(self, instance):
        exercise_log = instance.exercise_log
        deleted_num = instance.set_number
        instance.delete()
        ExerciseSet.objects.filter(
            exercise_log=exercise_log,
            set_number__gt=deleted_num
        ).update(set_number=F('set_number') - 1)


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
        offset = int(request.query_params.get('offset', 0))
        user = request.user

        today = date.today()
        current_week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        earliest_week_start = current_week_start - timedelta(weeks=weeks_back - 1)
        range_end = current_week_start + timedelta(days=6)

        # 3 bulk queries for the entire date range instead of 3×weeks_back sequential queries
        all_targets = {
            (t.year, t.week): t.target_points
            for t in TopDownWeeklyTarget.objects.filter(user=user)
        }
        all_plans = list(
            RoutinePlan.objects.filter(
                user=user, date__range=[earliest_week_start, range_end]
            ).prefetch_related('routine__exercises')
        )
        all_logs = list(
            ExerciseLog.objects.filter(
                user=user, date__range=[earliest_week_start, range_end], completed=True
            ).select_related('exercise')
        )

        result = []
        for i in range(weeks_back - 1, -1, -1):
            week_start = current_week_start - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            iso = week_start.isocalendar()
            year, week_num = iso[0], iso[1]

            weekly_target = all_targets.get((year, week_num), 0)

            week_plans = [p for p in all_plans if week_start <= p.date <= week_end]
            planned_points = sum(
                ex.training_points
                for plan in week_plans
                for ex in plan.routine.exercises.all()
            )

            week_logs = [l for l in all_logs if week_start <= l.date <= week_end]
            completed_points = sum(log.exercise.training_points for log in week_logs)

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

    @action(detail=False, methods=['get', 'post'])
    def analysis(self, request):
        user = request.user
        today = date.today()
        iso = today.isocalendar()
        year = int(request.query_params.get('year', iso[0]))
        week = int(request.query_params.get('week', iso[1]))

        if request.method == 'GET':
            try:
                cached = WeeklyAnalysis.objects.get(user=user, year=year, week=week)
                return Response({
                    'content': cached.content,
                    'generated_at': cached.generated_at.isoformat(),
                    'cached': True,
                })
            except WeeklyAnalysis.DoesNotExist:
                return Response({'content': None, 'cached': False})

        # POST: generate (or regenerate)
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return Response(
                {'error': 'ANTHROPIC_API_KEY not configured on server'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        week_data = _build_week_data(user, year, week)
        prompt = _build_analysis_prompt(week_data)

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                messages=[{'role': 'user', 'content': prompt}],
            )
            raw = message.content[0].text.strip()
            if raw.startswith('```'):
                raw = raw.split('```')[1]
                if raw.startswith('json'):
                    raw = raw[4:]
            content = json.loads(raw.strip())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        obj, _ = WeeklyAnalysis.objects.update_or_create(
            user=user, year=year, week=week,
            defaults={'content': content},
        )

        return Response({
            'content': content,
            'generated_at': obj.generated_at.isoformat(),
            'cached': False,
        })


def _build_week_data(user, year, week):
    week_start = datetime.fromisocalendar(year, week, 1).date()
    week_end = week_start + timedelta(days=6)

    try:
        target_obj = TopDownWeeklyTarget.objects.get(user=user, year=year, week=week)
        weekly_target = target_obj.target_points
    except TopDownWeeklyTarget.DoesNotExist:
        weekly_target = 0

    plans = RoutinePlan.objects.filter(
        user=user, date__range=[week_start, week_end]
    ).prefetch_related('routine__exercises').order_by('date')

    logs = ExerciseLog.objects.filter(
        user=user, date__range=[week_start, week_end]
    ).select_related('exercise').order_by('date')

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_plans = [p for p in plans if p.date == day]
        day_logs = [l for l in logs if l.date == day]

        exercises = []
        if day_plans:
            for p in day_plans:
                for ex in p.routine.exercises.all():
                    exercises.append({
                        'name': ex.name,
                        'type': ex.type,
                        'muscle_group': ex.muscle_group,
                        'training_points': ex.training_points,
                    })

        day_planned = sum(e['training_points'] for e in exercises)
        day_completed = sum(l.exercise.training_points for l in day_logs if l.completed)

        days.append({
            'day': day_names[i],
            'date': day.strftime('%a %b %d'),
            'routine': day_plans[0].routine.name if day_plans else None,
            'planned_points': day_planned,
            'completed_points': day_completed,
            'exercises': exercises,
        })

    history = []
    for offset in range(4, 0, -1):
        h_start = week_start - timedelta(weeks=offset)
        h_end = h_start + timedelta(days=6)
        h_iso = h_start.isocalendar()
        h_year, h_week = h_iso[0], h_iso[1]
        try:
            h_target = TopDownWeeklyTarget.objects.get(user=user, year=h_year, week=h_week)
            h_target_pts = h_target.target_points
        except TopDownWeeklyTarget.DoesNotExist:
            h_target_pts = 0
        h_logs = ExerciseLog.objects.filter(
            user=user, date__range=[h_start, h_end], completed=True
        ).select_related('exercise')
        h_completed = sum(l.exercise.training_points for l in h_logs)
        history.append({
            'week': f"W{h_week:02d} {h_year}",
            'completed': h_completed,
            'target': h_target_pts,
            'pct': round(h_completed / h_target_pts * 100, 1) if h_target_pts > 0 else 0,
        })

    total_planned = sum(d['planned_points'] for d in days)
    total_completed = sum(d['completed_points'] for d in days)

    return {
        'week_label': f"W{week:02d} {year}",
        'week_range': f"{week_start.strftime('%a %b %d')} – {week_end.strftime('%a %b %d %Y')}",
        'weekly_target': weekly_target,
        'total_planned': total_planned,
        'total_completed': total_completed,
        'planning_pct': round(total_planned / weekly_target * 100, 1) if weekly_target > 0 else 0,
        'achievement_pct': round(total_completed / weekly_target * 100, 1) if weekly_target > 0 else 0,
        'days': days,
        'history': history,
    }


def _build_analysis_prompt(data):
    day_lines = []
    for d in data['days']:
        if d['routine']:
            exs = ', '.join(
                f"{e['name']} ({e['muscle_group']}, {e['training_points']}pts)"
                for e in d['exercises']
            )
            day_lines.append(
                f"  {d['day']} {d['date']}: {d['routine']} — planned {d['planned_points']}pts, "
                f"completed {d['completed_points']}pts\n    Exercises: {exs}"
            )
        else:
            day_lines.append(f"  {d['day']} {d['date']}: — (rest/unplanned)")

    history_lines = [
        f"  {h['week']}: {h['completed']}/{h['target']} pts ({h['pct']}% of target)"
        for h in data['history']
    ]

    return f"""You are a personal fitness coach. Analyze this weekly training data and provide structured feedback.

WEEK: {data['week_label']} ({data['week_range']})
TARGET: {data['weekly_target']} training points
PLANNED: {data['total_planned']} pts ({data['planning_pct']}% of target)
COMPLETED: {data['total_completed']} pts ({data['achievement_pct']}% of target)

DAILY BREAKDOWN:
{chr(10).join(day_lines)}

RECENT HISTORY (last 4 weeks):
{chr(10).join(history_lines)}

Return ONLY a valid JSON object — no markdown, no code blocks, just raw JSON:
{{
  "summary": "1-2 sentence overview of the week",
  "observations": ["specific data-driven observation", "another observation", "a third observation"],
  "suggestions": ["actionable suggestion", "another suggestion"]
}}

Be specific: reference exercise names, point counts, recovery gaps, muscle group balance, and historical trends."""
