from django.db import models

# routes/models.py



class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True)
    
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )

    left = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="left_parent"
    )

    right = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="right_parent"
    )

    left_duration = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    right_duration = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.code