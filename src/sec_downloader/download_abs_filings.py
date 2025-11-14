"""
SEC Filings Downloader for ABS Issuers
Downloads SEC filings for Ford Credit, GM Financial, and Santander Consumer

This script uses the SEC EDGAR API to download ABS-related filings
and optionally uploads them to S3 for processing by AWS Glue.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import boto3
from sec_edgar_downloader import Downloader
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SEC API Configuration
SEC_API_BASE = "https://data.sec.gov"
USER_AGENT = "ABSolution ABS Analytics Platform (contact@example.com)"
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}


@dataclass
class ABSIssuer:
    """Represents an ABS issuer with their SEC information"""
    name: str
    cik: str
    tickers: List[str]
    description: str


# Major ABS Issuers Configuration
ABS_ISSUERS = {
    'ford_credit': ABSIssuer(
        name='Ford Credit',
        cik='38777',  # Ford Motor Credit Company LLC
        tickers=['F'],
        description='Ford Motor Credit Company - Auto Loans and Leases'
    ),
    'gm_financial': ABSIssuer(
        name='GM Financial',
        cik='1576940',  # GM Financial Company Inc.
        tickers=['GM'],
        description='General Motors Financial Company - Auto Loans and Leases'
    ),
    'santander_consumer': ABSIssuer(
        name='Santander Consumer',
        cik='1548429',  # Santander Consumer USA Holdings Inc.
        tickers=['SC'],
        description='Santander Consumer USA - Auto Loans and Consumer Finance'
    ),
}


class ABSFilingsDownloader:
    """
    Downloads SEC filings for ABS issuers
    Focuses on ABS-EE, 10-D, 10-K, and 8-K forms
    """

    # ABS-related form types
    ABS_FORM_TYPES = [
        'ABS-EE',    # ABS Informational and Computational Material
        '10-D',      # Asset-Backed Issuer Distribution Report
        '10-K',      # Annual Report
        '8-K',       # Current Report
        'ABS-15G',   # Asset-Backed Securities Report
    ]

    def __init__(self, download_dir: str = './data/sec_filings',
                 s3_bucket: Optional[str] = None,
                 s3_prefix: str = 'raw-filings'):
        """
        Initialize the downloader

        Args:
            download_dir: Local directory to save filings
            s3_bucket: Optional S3 bucket to upload filings
            s3_prefix: S3 prefix for uploaded filings
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.s3_client = boto3.client('s3') if s3_bucket else None

        # Initialize SEC Edgar downloader
        self.downloader = Downloader(
            company_name="ABSolution",
            email_address="contact@example.com",
            download_folder=str(self.download_dir)
        )

        logger.info(f"Initialized downloader - Local dir: {self.download_dir}")
        if s3_bucket:
            logger.info(f"S3 upload enabled - Bucket: {s3_bucket}, Prefix: {s3_prefix}")

    def get_company_facts(self, cik: str) -> Dict:
        """
        Get company facts from SEC API

        Args:
            cik: Company CIK number

        Returns:
            Dictionary of company facts
        """
        # Pad CIK to 10 digits
        cik_padded = cik.zfill(10)
        url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

        try:
            response = requests.get(url, headers=REQUEST_HEADERS)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching company facts for CIK {cik}: {str(e)}")
            return {}

    def get_recent_filings(self, cik: str, form_types: List[str] = None,
                          after_date: str = None) -> List[Dict]:
        """
        Get recent filings for a company

        Args:
            cik: Company CIK number
            form_types: List of form types to filter
            after_date: Only get filings after this date (YYYY-MM-DD)

        Returns:
            List of filing dictionaries
        """
        if form_types is None:
            form_types = self.ABS_FORM_TYPES

        company_data = self.get_company_facts(cik)
        if not company_data:
            return []

        filings = company_data.get('filings', {}).get('recent', {})
        if not filings:
            return []

        # Parse filings into list of dicts
        num_filings = len(filings.get('accessionNumber', []))
        filing_list = []

        for i in range(num_filings):
            filing = {
                'accessionNumber': filings['accessionNumber'][i],
                'filingDate': filings['filingDate'][i],
                'reportDate': filings.get('reportDate', [''] * num_filings)[i],
                'acceptanceDateTime': filings.get('acceptanceDateTime', [''] * num_filings)[i],
                'form': filings['form'][i],
                'fileNumber': filings.get('fileNumber', [''] * num_filings)[i],
                'items': filings.get('items', [''] * num_filings)[i],
                'size': filings.get('size', [0] * num_filings)[i],
                'primaryDocument': filings.get('primaryDocument', [''] * num_filings)[i],
                'primaryDocDescription': filings.get('primaryDocDescription', [''] * num_filings)[i],
            }

            # Filter by form type
            if form_types and filing['form'] not in form_types:
                continue

            # Filter by date
            if after_date and filing['filingDate'] < after_date:
                continue

            filing_list.append(filing)

        logger.info(f"Found {len(filing_list)} recent filings for CIK {cik}")
        return filing_list

    def download_filings_for_issuer(self, issuer: ABSIssuer,
                                    after_date: Optional[str] = None,
                                    limit: Optional[int] = None) -> Dict:
        """
        Download all ABS-related filings for an issuer

        Args:
            issuer: ABSIssuer object
            after_date: Only download filings after this date (YYYY-MM-DD)
            limit: Maximum number of filings per form type

        Returns:
            Summary dictionary
        """
        logger.info(f"=" * 80)
        logger.info(f"Downloading filings for: {issuer.name} (CIK: {issuer.cik})")
        logger.info(f"Description: {issuer.description}")
        logger.info(f"=" * 80)

        summary = {
            'issuer': issuer.name,
            'cik': issuer.cik,
            'forms_downloaded': {},
            'total_downloads': 0,
            'errors': []
        }

        # Get recent filings metadata first
        recent_filings = self.get_recent_filings(
            issuer.cik,
            form_types=self.ABS_FORM_TYPES,
            after_date=after_date
        )

        logger.info(f"Found {len(recent_filings)} total filings")

        # Download each form type
        for form_type in self.ABS_FORM_TYPES:
            try:
                logger.info(f"\nDownloading {form_type} forms...")

                # Download using sec-edgar-downloader
                num_downloaded = self.downloader.get(
                    form=form_type,
                    ticker_or_cik=issuer.cik,
                    after=after_date,
                    limit=limit
                )

                summary['forms_downloaded'][form_type] = num_downloaded
                summary['total_downloads'] += num_downloaded

                logger.info(f"Downloaded {num_downloaded} {form_type} filings")

            except Exception as e:
                error_msg = f"Error downloading {form_type}: {str(e)}"
                logger.error(error_msg)
                summary['errors'].append(error_msg)
                summary['forms_downloaded'][form_type] = 0

        # Upload to S3 if configured
        if self.s3_bucket:
            self._upload_to_s3(issuer)

        return summary

    def download_all_issuers(self, after_date: Optional[str] = None,
                            limit: Optional[int] = None) -> List[Dict]:
        """
        Download filings for all configured ABS issuers

        Args:
            after_date: Only download filings after this date (YYYY-MM-DD)
            limit: Maximum number of filings per form type per issuer

        Returns:
            List of summary dictionaries
        """
        logger.info("=" * 80)
        logger.info("DOWNLOADING SEC FILINGS FOR ALL ABS ISSUERS")
        logger.info("=" * 80)

        summaries = []

        for issuer_key, issuer in ABS_ISSUERS.items():
            summary = self.download_filings_for_issuer(
                issuer,
                after_date=after_date,
                limit=limit
            )
            summaries.append(summary)

            # Save summary to JSON
            self._save_summary(issuer, summary)

        # Print overall summary
        self._print_overall_summary(summaries)

        return summaries

    def _upload_to_s3(self, issuer: ABSIssuer):
        """Upload downloaded filings to S3"""
        if not self.s3_client:
            return

        logger.info(f"Uploading filings to S3: s3://{self.s3_bucket}/{self.s3_prefix}/")

        # Find all downloaded files for this issuer
        issuer_dir = self.download_dir / 'sec-edgar-filings' / issuer.cik
        if not issuer_dir.exists():
            logger.warning(f"No filings found for {issuer.name}")
            return

        uploaded_count = 0
        for file_path in issuer_dir.rglob('*'):
            if file_path.is_file():
                # Create S3 key preserving directory structure
                relative_path = file_path.relative_to(self.download_dir)
                s3_key = f"{self.s3_prefix}/{relative_path}"

                try:
                    self.s3_client.upload_file(
                        str(file_path),
                        self.s3_bucket,
                        s3_key
                    )
                    uploaded_count += 1
                except Exception as e:
                    logger.error(f"Error uploading {file_path}: {str(e)}")

        logger.info(f"Uploaded {uploaded_count} files to S3")

    def _save_summary(self, issuer: ABSIssuer, summary: Dict):
        """Save download summary to JSON file"""
        summary_file = self.download_dir / f"{issuer.name.replace(' ', '_')}_summary.json"

        with open(summary_file, 'w') as f:
            json.dump({
                **summary,
                'download_date': datetime.utcnow().isoformat(),
            }, f, indent=2)

        logger.info(f"Summary saved to: {summary_file}")

    def _print_overall_summary(self, summaries: List[Dict]):
        """Print overall download summary"""
        logger.info("\n" + "=" * 80)
        logger.info("OVERALL DOWNLOAD SUMMARY")
        logger.info("=" * 80)

        total_downloads = 0
        total_errors = 0

        for summary in summaries:
            logger.info(f"\n{summary['issuer']} (CIK: {summary['cik']})")
            logger.info(f"  Total filings: {summary['total_downloads']}")

            for form_type, count in summary['forms_downloaded'].items():
                if count > 0:
                    logger.info(f"    {form_type}: {count}")

            if summary['errors']:
                logger.info(f"  Errors: {len(summary['errors'])}")
                total_errors += len(summary['errors'])

            total_downloads += summary['total_downloads']

        logger.info(f"\nGRAND TOTAL: {total_downloads} filings downloaded")
        if total_errors > 0:
            logger.info(f"Total errors: {total_errors}")
        logger.info("=" * 80)


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Download SEC filings for ABS issuers'
    )
    parser.add_argument(
        '--issuer',
        choices=['ford_credit', 'gm_financial', 'santander_consumer', 'all'],
        default='all',
        help='Which issuer to download filings for'
    )
    parser.add_argument(
        '--after-date',
        type=str,
        help='Only download filings after this date (YYYY-MM-DD). Default: 1 year ago'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of filings per form type (default: no limit)'
    )
    parser.add_argument(
        '--download-dir',
        type=str,
        default='./data/sec_filings',
        help='Local directory to save filings'
    )
    parser.add_argument(
        '--s3-bucket',
        type=str,
        help='S3 bucket to upload filings (optional)'
    )
    parser.add_argument(
        '--s3-prefix',
        type=str,
        default='raw-filings',
        help='S3 prefix for uploaded filings'
    )

    args = parser.parse_args()

    # Default to 1 year ago if no date specified
    if not args.after_date:
        one_year_ago = datetime.now() - timedelta(days=365)
        args.after_date = one_year_ago.strftime('%Y-%m-%d')

    logger.info(f"Download parameters:")
    logger.info(f"  Issuer: {args.issuer}")
    logger.info(f"  After date: {args.after_date}")
    logger.info(f"  Limit per form: {args.limit or 'No limit'}")
    logger.info(f"  Download directory: {args.download_dir}")

    # Initialize downloader
    downloader = ABSFilingsDownloader(
        download_dir=args.download_dir,
        s3_bucket=args.s3_bucket,
        s3_prefix=args.s3_prefix
    )

    # Download filings
    if args.issuer == 'all':
        downloader.download_all_issuers(
            after_date=args.after_date,
            limit=args.limit
        )
    else:
        issuer = ABS_ISSUERS[args.issuer]
        downloader.download_filings_for_issuer(
            issuer,
            after_date=args.after_date,
            limit=args.limit
        )

    logger.info("\n✅ Download complete!")


if __name__ == '__main__':
    main()
