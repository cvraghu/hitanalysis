This repository contains code, unit tests and cloud formation templates to deploy a python script as AWS Python Shell Glue job.

AWS services used for the CI/CD portion in the solution:

AWS CodeCommit
AWS CodeBuild
AWS CloudFormation
Amazon Elastic Container Registry
EC2 Instance
AWS Glue

Components details

deploy/template.yml - AWS Cloudformation template for deployment of AWS Glue job and related resources.

src/AnalyzeHits.py - Python code for a sample AWS Glue job to process data in csv files in S3 bucket.

src/AnalyzeHitsSpark.py - PySpark code for a sample AWS Glue job to process data in csv files in S3 bucket.

src/requirements.txt - Simple text file containing AWS Glue job's dependencies for use by Python package manager Pip.

tests/test_hitanalysys.py - A simple PyTest code to execute test cases for the AWS Glue job src/AnalyzeHits.py.

pipeline.yml - AWS Cloudformation template for deploying pipeline to build, test and deploy the AWS Glue job in src folder.

The pipeline performs the following operations:

Pipeline uses the Code Commit repo as the source and transfers the most recent code from the master branch to the CodeBuild project for subsequent steps.
In the next next stage build and test,the most recent code from the previous phase is unit tested and the test report is published to CodeBuild report groups.
Unit testing is done on an EC2 instance created using an image in ECR public registry that is meant for Spark jobs.
If the tests are successful, then the next CodeBuild project is launched to publish the code to an Amazon Simple Storage Service (Amazon S3) bucket.
Following the successful completion of the publish phase, the final step is to deploy the AWS Glue task using the CloudFormation template in the deploy folder.

Pre-requisites

1. Ceate a S3 bucket with name "esshopzilla-demo"
2. Create a folder called "in" under the "esshopzilla-demo" bucket
3. Upload the data[57][88][30][97].tsv to the in folder. This will be used in pytest test case
4. Create a code commit repository with name "AdobeHitAnalysis" 
5. If you use different names for S3 bucket, code commit repo and job name, please make sure to change the references in pipeline.yml, template.yml, src/* and test/*

Steps 

1. Download the repo from this github
2. Clone the AdobeHitAnalysis AWS code commit repo
3. Copy the donwloaded code to this cloned repo
4. Add, Commit and Push all files to AdobeHitAnalysis code commit repo.
5. Open AWS Console
    a. Open Cloud Formation page
    b. Upload pipeline.yml and click through and submit. Choose Full rollback in case of errors
    c. This should deploy the Code Build pipeline that will unit test and deploy the code to Glue
6. Once Pipeline is deployed, pipeline will automatically run. If everything is good Glue job (samplejob) will be created.
7. If you want to rerun the pipeline, make changes to code commit repo (real or dummy change to Readme.md is enough)

Performance for large files

1. Try removing unwanted columns at source to reduce file size 
2. Process the file in chunks. ex data = pd.read_csv("data.csv", chunksize=100000)
3. Use third party libraries like dask that can parallely process the data
4. If the python script does not perform well for large files, convert to PySpark code and deploy as Spark Glue Job which will run in Spark clusters, thereby taking advantage of Spark partitions and parallel processing, etc. We can store the input/output files as parquet and run Spark-sql for adhoc analysis. We can use Athena or quicksight to do analysis on top the input/output data.
Refer to src/AnalyzeHitsSpark.py