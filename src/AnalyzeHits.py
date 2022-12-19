#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import itertools
import numpy as np
import math
import boto3
from io import StringIO
import datetime
from urllib.parse import urlparse
from urllib.parse import parse_qs
pd.set_option('display.max_columns', 15)

class HitAnalysis:
    def __init__(self, bucket, hitFileName, outFileName):
        self.hitFileName = hitFileName
        self.outFileName = outFileName
        self.bucket = bucket

    def loadFile(self):
        s3 = boto3.resource('s3') 
        bucket = s3.Bucket(self.bucket)
        obj = bucket.Object(key='in/' + self.hitFileName) 
        self.dfHits = pd.read_csv(obj.get()['Body'],delimiter="\t")        
        #self.dfHits = pd.read_csv("C:\Raghu\Learning\Adobe\data[57][88][30][97].tsv",delimiter="\t")

    def writeFile(self):
        filename = 'out/' + datetime.date.today().strftime('%Y-%m-%d') + "_" + self.outFileName
        s3 = boto3.resource('s3') 
        object = s3.Object(self.bucket, filename)
        csv_buffer = StringIO()
        self.dfFinal.to_csv(csv_buffer,sep ='\t',index=None)
        object.put(Body=csv_buffer.getvalue())
        #self.dfHits = pd.read_csv("C:\Raghu\Learning\Adobe\data[57][88][30][97].tsv",delimiter="\t")
        
    def getRevenue(self, event_list, product_list):
        revenue = 0
        if event_list != 1:
            return revenue
        if not product_list:
            revenue += 0
        products = product_list.split(',')
        for p in products:
            prd_attrs = p.split(';')
            if not prd_attrs[3]:
                revenue += 0
            else:
                revenue += int(prd_attrs[3])
        return revenue
    
    def getEngineAndKeyword(self, ip, hitdate, min_hit_time):
        dfReferrer = self.dfHits[((self.dfHits["ip"] == ip) & (self.dfHits["hitdate"] == hitdate) & (self.dfHits["hit_time_gmt"] == min_hit_time))]
        referrer = dfReferrer["referrer"].values[0]
        engine,query_string = referrer.split('?')
        engine = engine.replace("/search","")
        url_dict  = dict(param.split('=') for param in query_string.split('&'))
        key_word = None
        if 'q' in url_dict and ("google" in referrer or "bing" in referrer):
            key_word = url_dict['q']
        if 'p' in url_dict and ("yahoo" in referrer):
            key_word = url_dict['p']
        return engine,key_word
        
    def analyze(self):
        self.dfHits["timestamp"] = pd.to_datetime(self.dfHits['date_time'])
        self.dfHits["hitdate"] = self.dfHits['timestamp'].dt.date
        self.dfHits['event_list'] = self.dfHits['event_list'].fillna(0)
        self.dfHits["Revenue"] = self.dfHits.apply(lambda x: self.getRevenue(x['event_list'], x['product_list']), axis=1)
        self.dfHits["min_hit_time"] = self.dfHits.groupby(['ip','hitdate']).hit_time_gmt.transform('min')
        #print(self.dfHits.head(25))
        self.dfHits[["Search Engine Domain","Search Keyword"]] = self.dfHits.apply(lambda x: self.getEngineAndKeyword(x['ip'], x['hitdate'], x['min_hit_time']), axis=1, result_type ='expand')
        self.dfFinal = self.dfHits[(self.dfHits["event_list"] == 1.0)][["Search Engine Domain", "Search Keyword", "Revenue"]]
        self.dfFinal = self.dfFinal.sort_values(['Revenue'], ascending=False)
        self.writeFile()
        #print(self.dfFinal.head(25))

hitAnalysis = HitAnalysis("esshopzilla-demo", "data[57][88][30][97].tsv", "SearchKeywordPerformance.tab")
hitAnalysis.loadFile()
hitAnalysis.analyze()
