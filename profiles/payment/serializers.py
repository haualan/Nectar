from rest_framework import serializers
from .models import *
from django.conf import settings
from profiles.serializers import UserSimpleSerializer

class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    
    def to_internal_value(self, data):
        # print 'JSONSerializerField data', type(data), data
        if type(data) != dict and type(data) != list:
            raise ParseError('expecting a dict or list instead of :{}'.format(data))
        return data
    def to_representation(self, value):
        # print 'JSONSerializerField value', type(value),value
        if type(value) != dict:
            return json.loads(value)

        # print 'to rep', value, self.default, value == {}
        if value == {} or value == []:
            # adhere to default representation if empty set or list is passed (because we don't know if user wants to save a list or dict) 
            # print 'returning self default'
            print 'self.default', self.default
            if self.default is not empty:
                return self.default
            return value

        return value

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
    refCode = serializers.CharField(max_length=200, required=False)
    refCreditList = JSONSerializerField(required=False)

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

    remarks = serializers.CharField(max_length=None, min_length=None, allow_blank=True, required=False)



class PaymentManualRefundSerializer(serializers.Serializer):

    localCurrencyChargedAmount = serializers.DecimalField(max_digits=15, decimal_places=6)
    order_id = serializers.CharField(max_length=255)
    source = serializers.CharField(max_length=10)

    # user=None
    remarks = serializers.CharField(max_length=None, min_length=None, allow_blank=True, required=False)


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
