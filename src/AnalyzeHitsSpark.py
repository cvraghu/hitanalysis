import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import HiveContext, SQLContext, Row
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from pyspark.sql import DataFrame
from datetime import datetime
import pandas as pd
import itertools
import numpy as np
import math
import boto3
from io import StringIO

hitSchema = StructType([
            StructField("hit_time_gmt",LongType(),False),
            StructField("date_time",TimestampType(), False),
            StructField("user_agent",StringType(),True),
            StructField("ip",StringType(),True),
            StructField("event_list",IntegerType(),True),
            StructField("geo_city",StringType(),True),
            StructField("geo_region",StringType(),True),
            StructField("geo_country",StringType(),True),
            StructField("pagename",StringType(),True),
            StructField("page_url",StringType(),True),
            StructField("product_list",StringType(),True),
            StructField("referrer",StringType(),True)
  ])
  
  
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

def getRevenue(event_list, product_list):
    revenue = 0
    if event_list != 1:
        return revenue
    if product_list == "":
        revenue += 0
    products = product_list.split(',')
    for p in products:
        prd_attrs = p.split(';')
        if not prd_attrs[3]:
            revenue += 0
        else:
            revenue += int(prd_attrs[3])
    return revenue

getRevenueUDF = udf(lambda event_list,product_list: getRevenue(event_list, product_list),IntegerType())

def getKeyword(engine, query_string):
    url_dict  = dict(param.split('=') for param in query_string.split('&'))
    key_word = None
    if 'q' in url_dict and ("google" in engine or "bing" in engine):
        key_word = url_dict['q']
    if 'p' in url_dict and ("yahoo" in engine):
        key_word = url_dict['p']
    return key_word

getKeywordUDF = udf(lambda engine, query_string: getKeyword(engine, query_string),StringType())

df_hits = spark.read.format("csv").option("header", "true").option("delimiter", "\t").schema(hitSchema).load('s3://esshopzilla-demo1/in/TestData.tsv')

w = Window.partitionBy('ip', 'hit_date').orderBy('hit_time_gmt')

df_hits = df_hits.na.fill({'event_list': 0, 'product_list': ''})
df_hits_new = df_hits.withColumn("time_stamp", (col("hit_time_gmt")).cast("timestamp")).withColumn("hit_date", col("time_stamp").cast("date")).withColumn("Revenue", getRevenueUDF(col("event_list"), col("product_list"))).withColumn("min_hit_time", first('hit_time_gmt').over(w).alias("min_hit_time")).withColumn("first_referrer", first('referrer').over(w).alias("first_referrer")).withColumn("Search Engine Domain",regexp_replace(split(col("first_referrer"),'\\?').getItem(0),"com/search","com")).withColumn("Search Keyword",getKeywordUDF(col("Search Engine Domain"),split(col("first_referrer"),'\\?').getItem(1)))

df_hits_final = df_hits_new[col('event_list') == 1]["Search Engine Domain", "Search Keyword", "Revenue"].sort(col("Revenue").desc())

currentdate = datetime.now().strftime("%Y-%m-%d") 
filename = 'out/' + currentdate + "_SearchKeywordPerformance.tab"
s3 = boto3.resource('s3') 
object = s3.Object('esshopzilla-demo1', filename)
csv_buffer = StringIO()
pd_df = df_hits_final.toPandas()
pd_df.to_csv(csv_buffer,sep ='\t',index=None)
object.put(Body=csv_buffer.getvalue())