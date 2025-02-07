from django.db import models

# Create your models here.

class Branch(models.Model):
    name = models.CharField(max_length=100)
    extra_data = models.JSONField(default=dict)

    def __str__(self):
        return f"BRANCH #{self.id} {self.name}"

    def get_brand(self):
        try:
            brand = self.extra_data["brand"]
            return brand
        except:
            return 0


class Role(models.Model):

    name = models.CharField(default="", max_length=50)

    max_hours_per_day = models.IntegerField(default=0)
    max_services_per_week = models.IntegerField(default=0)
    max_hours_per_week = models.IntegerField(default=0)
    max_hours_per_month = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, default="F")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, default=1)
    extra_data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Schedule(models.Model):

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    employees = models.JSONField(default=dict)
    start_date = models.CharField(default="", max_length=100)
    end_date = models.CharField(default="", max_length=100)
    shift_data = models.JSONField(default=dict)
    closing_days = models.JSONField(default=dict)
    free_days = models.JSONField(default=dict)

    schedule_data = models.JSONField(default=dict)

    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"SCHEDULE #{self.id}"


class Import(models.Model):

    import_date = models.CharField(default="", max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    import_type = models.CharField(max_length=100, default="")
    data = models.JSONField(default=dict)

    def __str__(self):
        return f"IMPORT #{self.id}"