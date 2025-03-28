from django.db import models

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

# Create your models here.
