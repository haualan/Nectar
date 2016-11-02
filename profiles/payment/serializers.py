from rest_framework import serializers



class GetOrgMonthEndSummarySerializer(serializers.Serializer):
    org_id = serializers.IntegerField()
    dt = serializers.DateTimeField(required = False)
    s = serializers.CharField(required = False)
