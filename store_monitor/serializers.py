from rest_framework import serializers
from .models import store_status, business_hours, store_timezone

class StoreStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = store_status
        fields = '__all__'

class BusinessHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = business_hours
        fields = '__all__'

class StoreTimezoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = store_timezone
        fields = '__all__'