#!/usr/bin/env python3
"""
Upload SEC Filings to S3
Upload existing downloaded SEC filings to AWS S3 bucket
"""

import os
import sys
import boto3
import logging
from pathlib import Path
from typing import Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class S3Uploader:
    """Upload SEC filings to S3"""

    def __init__(self, bucket_name: str, prefix: str = 'raw-filings'):
        """
        Initialize S3 uploader

        Args:
            bucket_name: S3 bucket name
            prefix: S3 key prefix (folder path)
        """
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3_client = boto3.client('s3')

        logger.info(f"Initialized S3 uploader")
        logger.info(f"  Bucket: {bucket_name}")
        logger.info(f"  Prefix: {prefix}")

    def check_bucket_exists(self) -> bool:
        """Check if S3 bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✓ Bucket '{self.bucket_name}' exists and is accessible")
            return True
        except Exception as e:
            logger.error(f"✗ Cannot access bucket '{self.bucket_name}': {str(e)}")
            return False

    def upload_directory(self, local_dir: str, dry_run: bool = False) -> dict:
        """
        Upload entire directory to S3

        Args:
            local_dir: Local directory path
            dry_run: If True, only show what would be uploaded

        Returns:
            Dictionary with upload statistics
        """
        local_path = Path(local_dir)
        if not local_path.exists():
            logger.error(f"Directory does not exist: {local_dir}")
            return {'uploaded': 0, 'failed': 0, 'skipped': 0}

        stats = {'uploaded': 0, 'failed': 0, 'skipped': 0, 'total_bytes': 0}

        # Find all files
        files = list(local_path.rglob('*'))
        file_count = sum(1 for f in files if f.is_file())

        logger.info(f"Found {file_count} files to upload")
        logger.info("=" * 80)

        for file_path in files:
            if file_path.is_file():
                # Skip summary JSONs if they're in the root
                if file_path.name.endswith('_summary.json') and file_path.parent == local_path:
                    logger.debug(f"Skipping summary file: {file_path.name}")
                    stats['skipped'] += 1
                    continue

                # Create S3 key preserving directory structure
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{self.prefix}/{relative_path}".replace('\\', '/')

                if dry_run:
                    file_size = file_path.stat().st_size
                    logger.info(f"[DRY RUN] Would upload: {file_path.name} "
                              f"({file_size:,} bytes) -> s3://{self.bucket_name}/{s3_key}")
                    stats['uploaded'] += 1
                    stats['total_bytes'] += file_size
                else:
                    try:
                        # Upload file
                        file_size = file_path.stat().st_size
                        self.s3_client.upload_file(
                            str(file_path),
                            self.bucket_name,
                            s3_key
                        )

                        stats['uploaded'] += 1
                        stats['total_bytes'] += file_size

                        logger.info(f"✓ Uploaded: {relative_path} ({file_size:,} bytes)")

                    except Exception as e:
                        stats['failed'] += 1
                        logger.error(f"✗ Failed to upload {file_path.name}: {str(e)}")

        return stats

    def upload_file(self, local_file: str, s3_key: Optional[str] = None) -> bool:
        """
        Upload a single file to S3

        Args:
            local_file: Local file path
            s3_key: S3 key (if None, uses filename)

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(local_file)
        if not file_path.exists():
            logger.error(f"File does not exist: {local_file}")
            return False

        if s3_key is None:
            s3_key = f"{self.prefix}/{file_path.name}"

        try:
            file_size = file_path.stat().st_size
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key
            )
            logger.info(f"✓ Uploaded: {file_path.name} ({file_size:,} bytes) "
                       f"-> s3://{self.bucket_name}/{s3_key}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to upload {file_path.name}: {str(e)}")
            return False

    def list_uploaded_files(self, max_keys: int = 100) -> list:
        """
        List files that have been uploaded to S3

        Args:
            max_keys: Maximum number of keys to return

        Returns:
            List of S3 object summaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix,
                MaxKeys=max_keys
            )

            if 'Contents' not in response:
                logger.info("No files found in S3")
                return []

            objects = response['Contents']
            logger.info(f"\nFiles in s3://{self.bucket_name}/{self.prefix}/")
            logger.info("=" * 80)

            total_size = 0
            for obj in objects:
                size_mb = obj['Size'] / (1024 * 1024)
                total_size += obj['Size']
                logger.info(f"  {obj['Key']} ({size_mb:.2f} MB) - {obj['LastModified']}")

            total_mb = total_size / (1024 * 1024)
            logger.info(f"\nTotal: {len(objects)} files, {total_mb:.2f} MB")

            return objects

        except Exception as e:
            logger.error(f"Error listing S3 objects: {str(e)}")
            return []

    def print_summary(self, stats: dict):
        """Print upload summary"""
        logger.info("\n" + "=" * 80)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 80)
        logger.info(f"  Uploaded:  {stats['uploaded']:,} files")
        logger.info(f"  Failed:    {stats['failed']:,} files")
        logger.info(f"  Skipped:   {stats['skipped']:,} files")
        total_mb = stats['total_bytes'] / (1024 * 1024)
        logger.info(f"  Total size: {total_mb:.2f} MB")
        logger.info("=" * 80)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Upload SEC filings to AWS S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all downloaded filings
  python scripts/upload_to_s3.py \\
    --bucket absolution-sec-filings \\
    --directory data/sec_filings

  # Dry run to see what would be uploaded
  python scripts/upload_to_s3.py \\
    --bucket absolution-sec-filings \\
    --directory data/sec_filings \\
    --dry-run

  # Upload and then list files
  python scripts/upload_to_s3.py \\
    --bucket absolution-sec-filings \\
    --directory data/sec_filings \\
    --list

  # Just list existing files in S3
  python scripts/upload_to_s3.py \\
    --bucket absolution-sec-filings \\
    --list-only
        """
    )

    parser.add_argument(
        '--bucket',
        required=True,
        help='S3 bucket name'
    )
    parser.add_argument(
        '--directory',
        default='data/sec_filings',
        help='Local directory to upload (default: data/sec_filings)'
    )
    parser.add_argument(
        '--prefix',
        default='raw-filings',
        help='S3 prefix/folder (default: raw-filings)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List uploaded files after upload'
    )
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list files in S3, do not upload'
    )

    args = parser.parse_args()

    # Initialize uploader
    uploader = S3Uploader(args.bucket, args.prefix)

    # Check bucket exists
    if not uploader.check_bucket_exists():
        logger.error("Cannot proceed - bucket not accessible")
        sys.exit(1)

    # List only mode
    if args.list_only:
        uploader.list_uploaded_files(max_keys=1000)
        return

    # Upload files
    if args.dry_run:
        logger.info("\n🔍 DRY RUN MODE - No files will actually be uploaded\n")

    stats = uploader.upload_directory(args.directory, dry_run=args.dry_run)
    uploader.print_summary(stats)

    # List files if requested
    if args.list and not args.dry_run:
        logger.info("\n")
        uploader.list_uploaded_files(max_keys=100)

    if stats['uploaded'] > 0 and not args.dry_run:
        logger.info(f"\n✅ Upload complete! Files are now in s3://{args.bucket}/{args.prefix}/")


if __name__ == '__main__':
    main()
