"""
AWS Glue ETL Script for SEC Filings Ingestion
Automates ingestion and transformation of SEC filings into a normalized schema
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import boto3
import json
from datetime import datetime

# Initialize Glue context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_INPUT_PATH', 'S3_OUTPUT_PATH', 'DATABASE_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
S3_INPUT_PATH = args['S3_INPUT_PATH']
S3_OUTPUT_PATH = args['S3_OUTPUT_PATH']
DATABASE_NAME = args['DATABASE_NAME']

class SECFilingsETL:
    """ETL processor for SEC ABS filings"""

    def __init__(self, glue_context, spark_session):
        self.glue_context = glue_context
        self.spark = spark_session
        self.s3_client = boto3.client('s3')
        self.textract_client = boto3.client('textract')
        self.comprehend_client = boto3.client('comprehend')

    def read_raw_filings(self, input_path):
        """Read raw SEC filings from S3"""
        print(f"Reading raw filings from {input_path}")

        # Read various filing types
        dynamic_frame = self.glue_context.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={
                "paths": [input_path],
                "recurse": True
            },
            format="json",
            format_options={
                "multiline": True
            }
        )

        return dynamic_frame

    def extract_filing_metadata(self, df):
        """Extract metadata from SEC filings"""
        print("Extracting filing metadata")

        # Extract key fields from filings
        df = df.withColumn("filing_date", to_date(col("filedAt"))) \
               .withColumn("accession_number", col("accessionNo")) \
               .withColumn("cik", col("cik")) \
               .withColumn("company_name", col("companyName")) \
               .withColumn("form_type", col("formType")) \
               .withColumn("filing_year", year(col("filing_date"))) \
               .withColumn("filing_quarter", quarter(col("filing_date"))) \
               .withColumn("processed_at", current_timestamp())

        return df

    def normalize_abs_data(self, df):
        """Normalize ABS-specific fields"""
        print("Normalizing ABS data fields")

        # Define normalized schema for ABS data
        df = df.withColumn("issuer_name", col("company_name")) \
               .withColumn("asset_class",
                   when(col("description").like("%auto%"), "Auto Loan")
                   .when(col("description").like("%credit card%"), "Credit Card")
                   .when(col("description").like("%student%"), "Student Loan")
                   .when(col("description").like("%mortgage%"), "Mortgage")
                   .otherwise("Other")) \
               .withColumn("deal_name", col("exhibitList.deal_name")) \
               .withColumn("original_balance", col("exhibitList.original_balance").cast("decimal(18,2)")) \
               .withColumn("current_balance", col("exhibitList.current_balance").cast("decimal(18,2)")) \
               .withColumn("delinquency_rate", col("exhibitList.delinquency_rate").cast("decimal(5,4)")) \
               .withColumn("average_fico", col("exhibitList.average_fico").cast("integer"))

        return df

    def extract_pdf_data_with_textract(self, s3_uri):
        """
        Extract structured data from PDFs using Amazon Textract
        This would be called for each PDF document in the filing
        """
        print(f"Extracting PDF data from {s3_uri}")

        bucket, key = s3_uri.replace("s3://", "").split("/", 1)

        try:
            # Start Textract job for document analysis
            response = self.textract_client.start_document_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )

            job_id = response['JobId']
            print(f"Textract job started: {job_id}")

            return job_id

        except Exception as e:
            print(f"Error extracting PDF data: {str(e)}")
            return None

    def analyze_sentiment_with_comprehend(self, text):
        """
        Apply NLP to detect trends, anomalies and sentiment
        in issuer commentary sections using Amazon Comprehend
        """
        if not text or len(text) < 10:
            return None

        try:
            # Detect sentiment
            sentiment_response = self.comprehend_client.detect_sentiment(
                Text=text[:5000],  # Comprehend has a 5000 byte limit
                LanguageCode='en'
            )

            # Detect key phrases
            key_phrases_response = self.comprehend_client.detect_key_phrases(
                Text=text[:5000],
                LanguageCode='en'
            )

            # Detect entities
            entities_response = self.comprehend_client.detect_entities(
                Text=text[:5000],
                LanguageCode='en'
            )

            return {
                'sentiment': sentiment_response['Sentiment'],
                'sentiment_scores': sentiment_response['SentimentScore'],
                'key_phrases': [p['Text'] for p in key_phrases_response['KeyPhrases'][:10]],
                'entities': [e['Text'] for e in entities_response['Entities'][:10]]
            }

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return None

    def apply_data_quality_rules(self, df):
        """Apply data quality rules and filtering"""
        print("Applying data quality rules")

        # Filter out invalid records
        df = df.filter(
            (col("accession_number").isNotNull()) &
            (col("filing_date").isNotNull()) &
            (col("form_type").isin(['ABS-EE', '10-D', '10-K', '8-K']))
        )

        # Add data quality flags
        df = df.withColumn("quality_score",
            when((col("average_fico").isNotNull()) &
                 (col("delinquency_rate").isNotNull()) &
                 (col("current_balance").isNotNull()), 1.0)
            .when((col("average_fico").isNotNull()) |
                  (col("delinquency_rate").isNotNull()), 0.7)
            .otherwise(0.3)
        )

        return df

    def write_to_catalog(self, dynamic_frame, output_path, table_name):
        """Write processed data to Glue Data Catalog"""
        print(f"Writing data to {output_path}")

        # Write as Parquet with partitioning
        self.glue_context.write_dynamic_frame.from_options(
            frame=dynamic_frame,
            connection_type="s3",
            connection_options={
                "path": output_path,
                "partitionKeys": ["filing_year", "filing_quarter", "asset_class"]
            },
            format="parquet",
            format_options={
                "compression": "snappy"
            }
        )

        print(f"Data written successfully to {output_path}")

# Main ETL execution
def main():
    etl = SECFilingsETL(glueContext, spark)

    # Step 1: Read raw filings
    raw_filings = etl.read_raw_filings(S3_INPUT_PATH)

    # Convert to Spark DataFrame for transformations
    df = raw_filings.toDF()

    # Step 2: Extract metadata
    df = etl.extract_filing_metadata(df)

    # Step 3: Normalize ABS data
    df = etl.normalize_abs_data(df)

    # Step 4: Apply data quality rules
    df = etl.apply_data_quality_rules(df)

    # Step 5: Convert back to DynamicFrame
    normalized_frame = DynamicFrame.fromDF(df, glueContext, "normalized_frame")

    # Step 6: Write to output
    etl.write_to_catalog(
        normalized_frame,
        S3_OUTPUT_PATH,
        "normalized_sec_filings"
    )

    print("ETL job completed successfully")

if __name__ == "__main__":
    main()
    job.commit()
