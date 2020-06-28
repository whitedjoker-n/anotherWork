# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class KLine(models.Model):
    time_key = models.DateTimeField(blank=True, null=True)
    code = models.CharField(max_length=255)
    open = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    pe_ratio = models.FloatField(blank=True, null=True)
    turnover_rate = models.FloatField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    turnover = models.FloatField(blank=True, null=True)
    change_rate = models.FloatField(blank=True, null=True)
    last_close = models.FloatField(blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'k_line'
        unique_together = (('time_key', 'code', 'type'),)


class KLineTushare(models.Model):
    date = models.DateTimeField(blank=True, null=True)
    code = models.CharField(max_length=255)
    open = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    pre_close = models.FloatField(blank=True, null=True)
    change = models.FloatField(blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    pct_chg = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    type = models.CharField(max_length=255)

    class Meta:
        db_table = 'k_line_tushare'
        unique_together = (('date', 'code', 'type'),)


class KlineRecord(models.Model):
    code = models.CharField(max_length=255)
    kline_type = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    finish = models.IntegerField()

    class Meta:
        db_table = 'kline_record'
        unique_together = (('code', 'kline_type'),)
