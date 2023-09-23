import csv
import os
import uuid
from datetime import timezone, timedelta

from django.http import HttpResponse
from requests import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, Q, F

from .models import store_status, business_hours, store_timezone
from background_task import background
from django.core.cache import cache
from .serializers import StoreStatusSerializer, BusinessHoursSerializer, StoreTimezoneSerializer
from django.utils import timezone
import pytz
from datetime import datetime, timedelta

business_hours_data = business_hours.objects.all()
store_timezone_data = store_timezone.objects.all()
default_timezone_str = 'America/Chicago'

def convert_utc_to_local(store_id, utc_timestamp):

    try:
        # Retrieve the store's time zone based on store_id
        store_timezone_obj = store_timezone.objects.get(store_id=store_id)
        timezone_str = store_timezone_obj.timezone_str
    except store_timezone.DoesNotExist:
        # If store's time zone is missing
        timezone_str = default_timezone_str
    # Convert UTC timestamp to datetime object
    utc_datetime = datetime.strptime(utc_timestamp, '%Y-%m-%d %H:%M:%S.%f UTC')

    current_datetime = timezone.now()

    utc_timezone = pytz.timezone('UTC')
    local_timezone = pytz.timezone(timezone_str)
    # Convert the current_datetime to the store's local timezone
    local_datetime = current_datetime.astimezone(local_timezone)
    # Convert local datetime to desired format
    local_timestamp = local_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return local_timestamp

from datetime import datetime, timedelta

class TriggerReportView(APIView):

    def generate_report3(self, report_id):
        # Define the time intervals for the report (last hour, last day, last week)
        current_timestamp = datetime.utcnow()
        last_hour_start = current_timestamp - timedelta(hours=1)
        last_day_start = current_timestamp - timedelta(days=1)
        last_day_end = current_timestamp
        last_week_start = current_timestamp - timedelta(weeks=1)
        last_week_end = current_timestamp

        business_hours_data = business_hours.objects.all()
        store_status_data = store_status.objects.all()
        store_timezone_data = store_timezone.objects.all()

        # Filter store status data for the specific store and time intervals
        status_data_last_hour = store_status_data.filter(
            timestamp_utc__range=(last_hour_start, current_timestamp)
        )

        status_data_last_day = store_status_data.filter(
            timestamp_utc__range=(last_day_start, last_day_end)
        )

        status_data_last_week = store_status_data.filter(
            timestamp_utc__range=(last_week_start, last_week_end)
        )

        report_data = []
        status_data_within_hours = []
        status_data_within_minutes = []

        for hour_entry in status_data_last_hour:
            timestamp = hour_entry.timestamp_utc
            store_id = hour_entry.store_id

            local_timestamp = convert_utc_to_local(store_id, timestamp)
            # Get the day of the week (0-6) for the timestamp
            day_of_week = datetime.strptime(local_timestamp, "%Y-%m-%d %H:%M:%S").weekday()
            # Retrieve the business hours minute_entry for the store and day of the week
            business_hours_entry = business_hours.objects.get(store_id=store_id, day_of_week=day_of_week)
            # Check if the timestamp falls within the business hours for that day
            if business_hours_entry.start_time_local <= local_timestamp <= business_hours_entry.end_time_local:
                status_data_within_minutes.append(hour_entry)
            # Calculate uptime and downtime for the last hour within business hours
            uptime_last_hour = sum(1 for hour_entry in status_data_within_minutes if hour_entry.status == 'active')
            downtime_last_hour = sum(1 for hour_entry in status_data_within_minutes if hour_entry.status == 'inactive')

            status_data_within_minutes.clear()

        for day_entry in status_data_last_day:
            timestamp = day_entry.timestamp_utc
            store_id = day_entry.store_id

            local_timestamp = convert_utc_to_local(store_id, timestamp)

            day_of_week = datetime.strptime(local_timestamp, "%Y-%m-%d %H:%M:%S").weekday()
            # Retrieve the business hours minute_entry for the store and day of the week
            business_hours_entry = business_hours.objects.get(store_id=store_id, day_of_week=day_of_week)
            # Check if the timestamp falls within the business hours for that day
            if business_hours_entry.start_time_local <= local_timestamp <= business_hours_entry.end_time_local:
                status_data_within_hours.append(day_entry)
            # Calculate uptime and downtime for the last day within business hours
            uptime_last_day = sum(1 for day_entry in status_data_within_hours if day_entry.status == 'active')
            downtime_last_day = sum(1 for day_entry in status_data_within_hours if day_entry.status == 'inactive')

            status_data_within_hours.clear()

        for week_entry in status_data_last_week:
            timestamp = week_entry.timestamp_utc
            store_id = week_entry.store_id

            local_timestamp = convert_utc_to_local(store_id, timestamp)

            day_of_week = datetime.strptime(local_timestamp, "%Y-%m-%d %H:%M:%S").weekday()
            # Retrieve the business hours minute_entry for the store and day of the week
            business_hours_entry = business_hours.objects.get(store_id=store_id, day_of_week=day_of_week)
            # Check if the timestamp falls within the business hours for that day
            if business_hours_entry.start_time_local <= local_timestamp <= business_hours_entry.end_time_local:
                status_data_within_hours.append(week_entry)
            # Calculate uptime and downtime for the last week within business hours
            uptime_last_week = sum(1 for week_entry in status_data_within_hours if week_entry.status == 'active')
            downtime_last_week = sum(1 for week_entry in status_data_within_hours if week_entry.status == 'inactive')

            status_data_within_hours.clear()
            # Append the store's report data to the report_data list
            report_data.append({
                'store_id': store_id,
                'uptime_last_hour': uptime_last_hour * 10,
                'uptime_last_day': uptime_last_day * 60,
                'uptime_last_week': uptime_last_week * 60,
                'downtime_last_hour': downtime_last_hour * 10,
                'downtime_last_day': downtime_last_day * 60,
                'downtime_last_week': downtime_last_week * 60,
            })

            print(report_data)

            csv_filename = f"report_{report_id}.csv"
            csv_path = os.path.join("reports", csv_filename)

            with open(csv_path, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)

                writer.writerow(['store_id', 'uptime_last_hour(in minutes)', 'uptime_last_day(in hours)',
                                 'uptime_last_week(in hours)', 'downtime_last_hour(in minutes)',
                                 'downtime_last_day(in hours)', 'downtime_last_week(in hours)'])

                for data in report_data:
                    writer.writerow([

                        data['uptime_last_hour'],
                        data['uptime_last_day'],
                        data['uptime_last_week'],
                        data['downtime_last_hour'],
                        data['downtime_last_day'],
                        data['downtime_last_week']
                    ])

            return csv_path

            cache.set(report_id, csv_path)

        return report_data

    def post(self, request):
        report_id = str(uuid.uuid4())
        csv_path = self.generate_report3(report_id)
        return Response({'report_id': report_id})

class GetReportView(APIView):
    def get(self, request):
        report_id = request.query_params.get('report_id')
        csv_path = cache.get(report_id)

        if csv_path:

            if os.path.exists(csv_path):
                with open(csv_path, 'rb') as csv_file:
                    response = HttpResponse(csv_file.read(), content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(csv_path)}"'
            return response
        else:
            return Response({'status': 'Running'})