from rest_framework import serializers

class PaymentChargeUserSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    course_code = serializers.CharField(max_length=200)
    studentID = serializers.IntegerField()

    class Meta:
        extra_kwargs = {'token': {'write_only': True},}


class PaymentManualChargeSerializer(serializers.Serializer):
	currency = serializers.CharField(max_length=3)
	localCurrencyChargedAmount = serializers.DecimalField(max_digits=15, decimal_places=6)
	buyerID = serializers.IntegerField()
	studentID = serializers.IntegerField()
	course_code = serializers.CharField(max_length=255)
	source = serializers.CharField(max_length=10)

	# will be collected by request
	# user=None, 

	remarks = serializers.CharField(max_length=None, min_length=None, allow_blank=True,)



class PaymentManualRefundSerializer(serializers.Serializer):

	localCurrencyChargedAmount = serializers.DecimalField(max_digits=15, decimal_places=6)
	order_id = serializers.CharField(max_length=255)
	source = serializers.CharField(max_length=10)

	# user=None
	remarks = serializers.CharField(max_length=None, min_length=None, allow_blank=True,)
