import boto3
import datetime
import pandas as pd
from src.AnalyzeHits import HitAnalysis


RESULT_FILE = "SearchKeywordPerformance.tab"
S3_BUCKET_NAME = "esshopzilla-demo"

def initialize_test():
    return

def test_analysis():
    #initialize_test()
    s3 = boto3.resource('s3') 
    bucket = s3.Bucket(S3_BUCKET_NAME)
    filename = 'out/' + datetime.date.today().strftime('%Y-%m-%d') + "_" + RESULT_FILE
    obj = bucket.Object(key=filename) 
    dfResults = pd.read_csv(obj.get()['Body'],delimiter="\t")        
    topKeyword = dfResults[(dfResults["Revenue"]==290)]["Search Keyword"].values[0]
    assert topKeyword == "Ipod"