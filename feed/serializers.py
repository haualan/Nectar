from rest_framework import serializers


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        # print 'JSONSerializerField data', type(data), data
        if type(data) != dict and type(data) != list:
            raise ParseError('expecting a dict or list instead of :{}'.format(data))
        return data
    def to_representation(self, value):
        # print 'JSONSerializerField value', type(value),value
        # if type(value) != dict:
        #     return json.loads(value)
        return value


class FeedSerializer(serializers.Serializer):
    item = JSONSerializerField()
