from rest_framework import serializers

class PaymentChargeUserSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    course_code = serializers.CharField(max_length=200)
    studentID = serializers.IntegerField()

    class Meta:
        extra_kwargs = {'token': {'write_only': True},}