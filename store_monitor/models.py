from django.db import models
from django.utils import timezone

# Create your models here.

class store_status(models.Model):
    store_id = models.IntegerField()
    status = models.CharField(max_length=200)
    timestamp_utc = models.DateTimeField(default=timezone.now)

class business_hours(models.Model):
    store_id = models.IntegerField()
    day_of_week = models.IntegerField()
    start_time_local = models.DateTimeField()
    end_time_local = models.DateTimeField()

class store_timezone(models.Model):
    store_id = models.IntegerField()
    timezone_str = models.CharField(max_length=100)

