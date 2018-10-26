from rest_framework import serializers

class BitcoinTransactionSerializer(serializers.Serializer):
    datetime = serializers.DateTimeField()
    service_str = serializers.CharField()

    from_address = serializers.CharField()
    inputs = serializers.CharField()
    outputs = serializers.CharField()
    mining_fee = serializers.IntegerField()
    tx = serializers.CharField()

    block_height = serializers.IntegerField()
    status = serializers.IntegerField()
    spoolverb = serializers.CharField()
