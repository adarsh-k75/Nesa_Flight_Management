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

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()

        # 1. Prevent self loops
        if self.left == self:
            raise ValidationError("An airport's left child cannot be itself.")
        if self.right == self:
            raise ValidationError("An airport's right child cannot be itself.")
        if self.parent == self:
            raise ValidationError("An airport cannot be its own parent.")

        # 2. Prevent pointing to parent as left/right child
        if self.parent:
            if self.left == self.parent:
                raise ValidationError("An airport's left child cannot be its parent.")
            if self.right == self.parent:
                raise ValidationError("An airport's right child cannot be its parent.")

        # 3. Prevent cycles: left/right child cannot be the airport itself or any of its ancestors
        ancestors = set()
        if self.code:
            ancestors.add(self.code)
        curr = self.parent
        while curr:
            if curr.code:
                ancestors.add(curr.code)
            curr = curr.parent

        if self.left and self.left.code in ancestors:
            raise ValidationError("Left child cannot be the airport itself or one of its ancestors.")
        if self.right and self.right.code in ancestors:
            raise ValidationError("Right child cannot be the airport itself or one of its ancestors.")

        # 4. Check for cycles through parent pointers
        if self.parent:
            visited = set()
            if self.code:
                visited.add(self.code)
            curr = self.parent
            while curr:
                if curr.code in visited:
                    raise ValidationError("Circular reference detected in the airport tree hierarchy.")
                if curr.code:
                    visited.add(curr.code)
                curr = curr.parent

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


    