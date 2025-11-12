"""
Amazon Kinesis Producer for SEC Filings
Streams SEC filings as they are published for near real-time updates
"""

import json
import boto3
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
kinesis_client = boto3.client('kinesis')
s3_client = boto3.client('s3')

# Configuration
KINESIS_STREAM_NAME = 'sec-filings-stream'
SEC_API_ENDPOINT = 'https://www.sec.gov/cgi-bin/browse-edgar'
USER_AGENT = 'ABSolution/1.0 (contact@example.com)'


class SECFilingsProducer:
    """Produces real-time SEC filings to Kinesis stream"""

    def __init__(self, stream_name: str):
        self.stream_name = stream_name
        self.kinesis = kinesis_client
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

    def fetch_recent_filings(self, form_types: List[str] = None,
                            lookback_hours: int = 1) -> List[Dict]:
        """
        Fetch recent SEC filings from SEC EDGAR

        Args:
            form_types: List of form types to fetch (e.g., ['ABS-EE', '10-D'])
            lookback_hours: How many hours back to look for filings

        Returns:
            List of filing dictionaries
        """
        if form_types is None:
            form_types = ['ABS-EE', '10-D', '10-K', '8-K']

        filings = []
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)

        logger.info(f"Fetching filings from last {lookback_hours} hours")
        logger.info(f"Form types: {form_types}")

        for form_type in form_types:
            try:
                # SEC EDGAR API call
                params = {
                    'action': 'getcompany',
                    'type': form_type,
                    'dateb': datetime.utcnow().strftime('%Y%m%d'),
                    'owner': 'exclude',
                    'count': 100,
                    'output': 'atom'
                }

                response = self.session.get(SEC_API_ENDPOINT, params=params)
                response.raise_for_status()

                # Parse filings (simplified - would need actual parsing)
                # In production, use proper SEC EDGAR API or RSS feeds
                logger.info(f"Fetched {form_type} filings")

                # Simulate filing data for demonstration
                # DISABLED: Do not generate mock filings
                # sample_filing = self._generate_sample_filing(form_type)
                # filings.append(sample_filing)

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching {form_type} filings: {str(e)}")
                continue

        logger.info(f"Total filings fetched: {len(filings)}")
        return filings

    def _generate_sample_filing(self, form_type: str) -> Dict:
        """
        Generate sample filing data for demonstration
        In production, this would parse actual SEC data
        """
        import random
        import uuid

        asset_classes = ['AUTO_LOAN', 'CREDIT_CARD', 'STUDENT_LOAN', 'MORTGAGE']
        asset_class = random.choice(asset_classes)

        filing = {
            'accessionNo': f"0001234567-{datetime.utcnow().strftime('%y-%m%d')}-{random.randint(1000, 9999)}",
            'cik': f"{random.randint(1000000, 9999999):07d}",
            'companyName': f"Example Issuer {random.randint(1, 100)} LLC",
            'formType': form_type,
            'filedAt': datetime.utcnow().isoformat(),
            'fiscalYear': datetime.utcnow().year,
            'fiscalPeriod': f"Q{(datetime.utcnow().month-1)//3 + 1}",

            'deal': {
                'name': f"{asset_class.replace('_', ' ')} Trust {datetime.utcnow().year}-{random.randint(1, 5)}"
            },

            'issuer': {
                'name': f"Example Issuer {random.randint(1, 100)} LLC"
            },

            'poolStats': {
                'originalBalance': random.uniform(500000000, 2000000000),
                'currentBalance': random.uniform(300000000, 1500000000),
                'principalReceived': random.uniform(100000000, 500000000)
            },

            'performance': {
                'delinquency30': random.uniform(0.01, 0.05),
                'delinquency60': random.uniform(0.005, 0.03),
                'delinquency90Plus': random.uniform(0.002, 0.02),
                'cumulativeDefaultRate': random.uniform(0.01, 0.08),
                'cumulativeLossRate': random.uniform(0.005, 0.05)
            },

            'creditMetrics': {
                'avgFICO': random.randint(620, 760),
                'avgLTV': random.uniform(0.60, 0.85),
                'avgDTI': random.uniform(0.25, 0.45)
            },

            'description': f"{asset_class.replace('_', ' ')} backed securities"
        }

        return filing

    def put_record_to_kinesis(self, filing: Dict) -> Dict:
        """
        Put a single record to Kinesis stream

        Args:
            filing: Filing data dictionary

        Returns:
            Response from Kinesis
        """
        try:
            # Use accession number as partition key for even distribution
            partition_key = filing.get('accessionNo', 'default')

            # Convert to JSON and put to Kinesis
            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(filing, default=str),
                PartitionKey=partition_key
            )

            logger.debug(f"Put record to Kinesis: {filing['accessionNo']}, "
                        f"Shard: {response['ShardId']}, "
                        f"Sequence: {response['SequenceNumber']}")

            return response

        except Exception as e:
            logger.error(f"Error putting record to Kinesis: {str(e)}")
            raise

    def put_records_batch(self, filings: List[Dict]) -> Dict:
        """
        Put multiple records to Kinesis in batch (up to 500 records)

        Args:
            filings: List of filing dictionaries

        Returns:
            Summary of batch operation
        """
        if not filings:
            return {'success_count': 0, 'failed_count': 0}

        records = []
        for filing in filings[:500]:  # Kinesis batch limit
            records.append({
                'Data': json.dumps(filing, default=str),
                'PartitionKey': filing.get('accessionNo', 'default')
            })

        try:
            response = self.kinesis.put_records(
                StreamName=self.stream_name,
                Records=records
            )

            success_count = len(records) - response['FailedRecordCount']
            failed_count = response['FailedRecordCount']

            logger.info(f"Batch put: {success_count} succeeded, {failed_count} failed")

            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'response': response
            }

        except Exception as e:
            logger.error(f"Error in batch put: {str(e)}")
            raise

    def stream_filings_continuously(self, poll_interval_seconds: int = 300):
        """
        Continuously poll for new filings and stream to Kinesis

        Args:
            poll_interval_seconds: How often to poll for new filings
        """
        logger.info(f"Starting continuous streaming (poll interval: {poll_interval_seconds}s)")

        while True:
            try:
                # Fetch recent filings
                filings = self.fetch_recent_filings(lookback_hours=1)

                if filings:
                    # Stream to Kinesis
                    result = self.put_records_batch(filings)
                    logger.info(f"Streamed {result['success_count']} filings to Kinesis")
                else:
                    logger.info("No new filings found")

                # Wait before next poll
                time.sleep(poll_interval_seconds)

            except KeyboardInterrupt:
                logger.info("Stopping continuous streaming")
                break
            except Exception as e:
                logger.error(f"Error in continuous streaming: {str(e)}")
                time.sleep(60)  # Wait before retrying


class KinesisConsumer:
    """Consumes records from Kinesis stream for testing"""

    def __init__(self, stream_name: str):
        self.stream_name = stream_name
        self.kinesis = kinesis_client

    def get_shard_iterator(self, shard_id: str, iterator_type: str = 'LATEST') -> str:
        """Get shard iterator for reading from stream"""
        response = self.kinesis.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType=iterator_type
        )
        return response['ShardIterator']

    def consume_records(self, shard_id: str, limit: int = 10):
        """
        Consume records from a shard

        Args:
            shard_id: Shard ID to consume from
            limit: Maximum number of records to consume
        """
        shard_iterator = self.get_shard_iterator(shard_id)
        records_consumed = 0

        while records_consumed < limit:
            try:
                response = self.kinesis.get_records(
                    ShardIterator=shard_iterator,
                    Limit=min(limit - records_consumed, 100)
                )

                records = response['Records']
                if records:
                    for record in records:
                        data = json.loads(record['Data'])
                        logger.info(f"Consumed: {data.get('accessionNo')} - {data.get('companyName')}")
                        records_consumed += 1

                shard_iterator = response['NextShardIterator']

                if not records:
                    logger.info("No more records available")
                    break

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error consuming records: {str(e)}")
                break


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='SEC Filings Kinesis Producer')
    parser.add_argument('--mode', choices=['produce', 'consume', 'continuous'],
                       default='produce', help='Operation mode')
    parser.add_argument('--stream', default=KINESIS_STREAM_NAME,
                       help='Kinesis stream name')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of filings to produce')
    parser.add_argument('--interval', type=int, default=300,
                       help='Poll interval for continuous mode (seconds)')

    args = parser.parse_args()

    if args.mode == 'produce':
        producer = SECFilingsProducer(args.stream)
        logger.info(f"Producing {args.count} sample filings...")

        # Generate sample filings
        # DISABLED: Do not generate mock filings
        # filings = [producer._generate_sample_filing('ABS-EE')
        #           for _ in range(args.count)]

        # Skip sending mock filings to Kinesis
        logger.warning("Mock filing generation is disabled")
        # result = producer.put_records_batch(filings)
        # logger.info(f"Produced {result['success_count']} filings")

    elif args.mode == 'continuous':
        producer = SECFilingsProducer(args.stream)
        producer.stream_filings_continuously(args.interval)

    elif args.mode == 'consume':
        consumer = KinesisConsumer(args.stream)

        # List shards
        response = kinesis_client.describe_stream(StreamName=args.stream)
        shards = response['StreamDescription']['Shards']

        logger.info(f"Consuming from {len(shards)} shards...")
        for shard in shards:
            consumer.consume_records(shard['ShardId'], limit=args.count)


if __name__ == '__main__':
    main()
