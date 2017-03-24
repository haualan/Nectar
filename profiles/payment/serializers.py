from rest_framework import serializers
from .models import *
from django.conf import settings
from profiles.serializers import UserSimpleSerializer

def get_model_concrete_fields(MyModel):
    return [
        f.name
        for f in MyModel._meta.get_fields()
        if f.concrete and (
            not f.is_relation
            or f.one_to_one
            or (f.many_to_one and f.related_model)
        )
    ]

class CouponValidationSerializer(serializers.Serializer):
    addlDiscount = serializers.IntegerField(required=False, default=0)
    coupon_code = serializers.CharField(max_length=200, required=True, allow_blank=False)
    course_code = serializers.CharField(max_length=200, required=True, allow_blank=False)
    price_code = serializers.CharField(max_length=200, required=True, allow_blank=False)

class ReferralValidationSerializer(serializers.Serializer):
    refCode = serializers.CharField(max_length=200, required=True, allow_blank=False)
    subdomain = serializers.CharField(max_length=200, required=True, allow_blank=False)




class PaymentChargeUserSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    course_code = serializers.CharField(max_length=200)
    price_code = serializers.CharField(max_length=200)
    coupon_code = serializers.CharField(max_length=200, required=False)
    studentID = serializers.IntegerField()

    class Meta:
        extra_kwargs = {'token': {'write_only': True},}


class PaymentManualChargeSerializer(serializers.Serializer):
    currency = serializers.CharField(max_length=3)
    localCurrencyChargedAmount = serializers.DecimalField(max_digits=15, decimal_places=6, )
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


class ReferralCreditSerializer(serializers.HyperlinkedModelSerializer):
    discountAmount = serializers.SerializerMethodField(method_name = '_get_discountAmount')
    referToUser = UserSimpleSerializer()

    def _get_discountAmount(self, obj):
        """
        returns the discount amount of the referral code, 
        - requires the subdomain query param when this is requested, otherwise returns 0
        """
        subdomain = self.context.get("request").query_params.get('subdomain', None)

        return obj.get_discountAmount(subdomain = subdomain)


    class Meta:
        model = ReferralCredit
        # fields = '__all__' 
        fields = get_model_concrete_fields(model) + ['url', 'discountAmount']

class LedgerSerializer(serializers.HyperlinkedModelSerializer):
    localCurrencyChargedAmount = serializers.DecimalField(max_digits=15, decimal_places=6, coerce_to_string=False)

    class Meta:
        model = Ledger
        # fields = '__all__' 
        fields = get_model_concrete_fields(model) + ['url']
