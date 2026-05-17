from django.contrib import admin
from .models import Exercise, Routine, RoutinePlan, ExerciseLog, TopDownWeeklyTarget, WeeklyAnalysis


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'activity', 'type', 'muscle_group', 'sub_group', 'training_points')
    list_filter = ('activity', 'type', 'muscle_group')
    search_fields = ('name',)


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('exercises',)


@admin.register(RoutinePlan)
class RoutinePlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'routine', 'date')
    list_filter = ('user', 'date')
    date_hierarchy = 'date'


@admin.register(ExerciseLog)
class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'date', 'completed')
    list_filter = ('user', 'completed', 'date')
    date_hierarchy = 'date'


@admin.register(TopDownWeeklyTarget)
class TopDownWeeklyTargetAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'week', 'target_points')
    list_filter = ('user', 'year')


@admin.register(WeeklyAnalysis)
class WeeklyAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'week', 'generated_at')
    list_filter = ('user', 'year')
    readonly_fields = ('generated_at',)
