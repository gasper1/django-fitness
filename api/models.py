from django.db import models
from django.conf import settings

class Exercise(models.Model):
    """Represents a single exercise."""

    ACTIVITY_CHOICES = [
        ('Strength', 'Strength Training'),
        ('Cardio', 'Cardiovascular'),
        ('Flexibility', 'Flexibility'),
        ('Balance', 'Balance'),
        # Add more activities as needed
    ]

    TYPE_CHOICES = [
        ('Barbell', 'Barbell'),
        ('Dumbbell', 'Dumbbell'),
        ('Machine', 'Machine'),
        ('Bodyweight', 'Bodyweight'),
        ('Kettlebell', 'Kettlebell'),
        ('Resistance Band', 'Resistance Band'),
        ('Run', 'Running'),
        ('Other', 'Other'),
        # Add more types as needed
    ]

    MUSCLE_GROUP_CHOICES = [
        ('Chest', 'Chest'),
        ('Back', 'Back'),
        ('Shoulders', 'Shoulders'),
        ('Arms', 'Arms'),
        ('Legs', 'Legs'),
        ('Abs', 'Abdominals'),
        ('Full Body', 'Full Body'),
        # Add more muscle groups as needed
    ]

    SUB_GROUP_CHOICES = [
        ('Upper Chest', 'Upper Chest'),
        ('Lower Chest', 'Lower Chest'),
        ('Lats', 'Latissimus Dorsi'),
        ('Traps', 'Trapezius'),
        ('Quads', 'Quadriceps'),
        ('Hamstrings', 'Hamstrings'),
        ('Calves', 'Calves'),
        ('Glutes', 'Glutes'),
        ('Biceps', 'Biceps'),
        ('Triceps', 'Triceps'),
        # Add more sub-groups as needed
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Name of the exercise")
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, help_text="Primary activity category")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, help_text="Type of equipment or method used")
    muscle_group = models.CharField(max_length=50, choices=MUSCLE_GROUP_CHOICES, help_text="Main muscle group targeted")
    sub_group = models.CharField(max_length=50, choices=SUB_GROUP_CHOICES, blank=True, null=True, help_text="Specific sub-muscle group targeted (optional)")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Exercise"
        verbose_name_plural = "Exercises"


class Routine(models.Model):
    """Represents a workout routine, which is a collection of exercises."""
    name = models.CharField(max_length=100, unique=True, help_text="Name of the routine")
    exercises = models.ManyToManyField(Exercise, related_name='routines', help_text="Exercises included in this routine")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Routine"
        verbose_name_plural = "Routines"


class RoutinePlan(models.Model):
    """Model definition for RoutinePlan."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        # Ensure a user can only plan one routine per day
        unique_together = ('user', 'date')
        ordering = ['date']
        verbose_name = "Routine Plan"
        verbose_name_plural = "Routine Plans"

    def __str__(self):
        return f"{self.user.username}'s plan for {self.date}: {self.routine.name}"
