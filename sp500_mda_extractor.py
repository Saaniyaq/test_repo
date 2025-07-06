#!/usr/bin/env python3
"""
S&P 500 MD&A Data Extractor for FinBERT Analysis

This script extracts Management Discussion and Analysis (MD&A) sections 
from SEC filings (10-K and 10-Q) for all S&P 500 companies and creates 
a structured dataset suitable for FinBERT sentiment analysis.

Author: AI Assistant
Date: 2024
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Tuple
import time
import json
from pathlib import Path
import argparse

# Import edgar tools
try:
    from edgar import *
    from edgar.core import get_filings
except ImportError:
    print("Error: edgartools not installed. Please run: pip install edgartools")
    sys.exit(1)

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sp500_mda_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SP500MDAExtractor:
    """Main class for extracting MD&A data from S&P 500 companies"""
    
    def __init__(self, output_dir: str = "output", user_email: str = None):
        """
        Initialize the extractor
        
        Args:
            output_dir: Directory to save output files
            user_email: Email address for SEC compliance (required)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not user_email:
            raise ValueError("User email is required for SEC compliance")
            
        # Set Edgar identity
        set_identity(user_email)
        
        self.sp500_companies = None
        self.mda_data = []
        
    def get_sp500_companies(self) -> pd.DataFrame:
        """
        Get S&P 500 companies list with CIK codes from Wikipedia
        
        Returns:
            DataFrame with company information including CIKs
        """
        logger.info("Fetching S&P 500 companies list...")
        
        try:
            # Get S&P 500 list from Wikipedia
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_df = tables[0]  # First table contains the companies
            
            # Clean and standardize column names
            sp500_df.columns = sp500_df.columns.str.strip()
            
            # Rename columns for consistency
            column_mapping = {
                'Symbol': 'ticker',
                'Security': 'company_name', 
                'GICS Sector': 'sector',
                'GICS Sub-Industry': 'sub_industry',
                'Headquarters Location': 'headquarters',
                'Date added': 'date_added',
                'CIK': 'cik',
                'Founded': 'founded'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in sp500_df.columns:
                    sp500_df = sp500_df.rename(columns={old_col: new_col})
            
            # Clean CIK column - remove leading zeros and convert to int
            if 'cik' in sp500_df.columns:
                sp500_df['cik'] = sp500_df['cik'].astype(str).str.zfill(10)
            
            # Save the company list
            sp500_df.to_csv(self.output_dir / "sp500_companies.csv", index=False)
            logger.info(f"Retrieved {len(sp500_df)} S&P 500 companies")
            
            self.sp500_companies = sp500_df
            return sp500_df
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 companies: {e}")
            raise
    
    def get_company_filings(self, ticker: str, cik: str, start_date: str, end_date: str, 
                           forms: List[str] = ['10-K', '10-Q']) -> List:
        """
        Get filings for a specific company
        
        Args:
            ticker: Company ticker symbol
            cik: Company CIK
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) 
            forms: List of form types to retrieve
            
        Returns:
            List of filing objects
        """
        try:
            # Get company object
            company = Company(ticker)
            
            # Get filings within date range
            filings = company.get_filings(
                forms=forms,
                filing_date=f'{start_date}:{end_date}'
            )
            
            logger.info(f"Found {len(filings)} filings for {ticker} ({len(forms)} form types)")
            return filings
            
        except Exception as e:
            logger.warning(f"Error getting filings for {ticker}: {e}")
            return []
    
    def extract_mda_from_filing(self, filing) -> Optional[Dict]:
        """
        Extract MD&A section from a specific filing
        
        Args:
            filing: Edgar filing object
            
        Returns:
            Dictionary with MD&A content and metadata
        """
        try:
            # Get the filing document
            doc = filing.document
            
            if not doc:
                return None
                
            # Extract MD&A section (Item 7 for 10-K, Part II Item 7 for 10-Q)
            mda_text = None
            
            if filing.form == '10-K':
                # Try to get Item 7 MD&A section
                try:
                    mda_text = doc.get_section('7')  # Item 7 - MD&A
                except:
                    # Fallback: try to extract using text patterns
                    full_text = doc.text
                    mda_text = self._extract_mda_by_pattern(full_text, '10-K')
            
            elif filing.form == '10-Q':
                # Try to get Part II Item 7 for 10-Q
                try:
                    mda_text = doc.get_section('part2item7')  # Part II Item 7 - MD&A
                except:
                    # Fallback: try to extract using text patterns  
                    full_text = doc.text
                    mda_text = self._extract_mda_by_pattern(full_text, '10-Q')
            
            if mda_text and len(mda_text.strip()) > 100:  # Minimum length check
                # Clean the text
                clean_text = self._clean_mda_text(mda_text)
                
                return {
                    'ticker': filing.company.ticker if hasattr(filing.company, 'ticker') else 'N/A',
                    'company_name': filing.company.name if hasattr(filing.company, 'name') else 'N/A',
                    'cik': filing.company.cik if hasattr(filing.company, 'cik') else 'N/A',
                    'form_type': filing.form,
                    'filing_date': filing.filing_date.strftime('%Y-%m-%d') if filing.filing_date else 'N/A',
                    'period_end': filing.period_of_report.strftime('%Y-%m-%d') if hasattr(filing, 'period_of_report') and filing.period_of_report else 'N/A',
                    'accession_number': filing.accession_number,
                    'url': filing.url,
                    'mda_text': clean_text,
                    'mda_length': len(clean_text),
                    'word_count': len(clean_text.split())
                }
                
        except Exception as e:
            logger.warning(f"Error extracting MD&A from filing {filing.accession_number}: {e}")
            
        return None
    
    def _extract_mda_by_pattern(self, text: str, form_type: str) -> Optional[str]:
        """
        Extract MD&A section using text patterns when section extraction fails
        
        Args:
            text: Full filing text
            form_type: Type of form (10-K or 10-Q)
            
        Returns:
            MD&A text if found
        """
        try:
            # Common MD&A section patterns
            if form_type == '10-K':
                patterns = [
                    r'ITEM\s*7\.?\s*MANAGEMENT[\'']?S\s+DISCUSSION\s+AND\s+ANALYSIS.*?(?=ITEM\s*7A|ITEM\s*8|\nITEM\s|\n\n\s*ITEM)',
                    r'Item\s*7\.?\s*Management[\'']?s\s+Discussion\s+and\s+Analysis.*?(?=Item\s*7A|Item\s*8|\nItem\s|\n\n\s*Item)',
                    r'7\.?\s*MANAGEMENT[\'']?S\s+DISCUSSION\s+AND\s+ANALYSIS.*?(?=7A|8\.|\n7A|\n8\.)'
                ]
            else:  # 10-Q
                patterns = [
                    r'PART\s*II.*?ITEM\s*7\.?\s*MANAGEMENT[\'']?S\s+DISCUSSION\s+AND\s+ANALYSIS.*?(?=ITEM\s*8|\nITEM\s|\n\n\s*ITEM)',
                    r'Part\s*II.*?Item\s*7\.?\s*Management[\'']?s\s+Discussion\s+and\s+Analysis.*?(?=Item\s*8|\nItem\s|\n\n\s*Item)'
                ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(0)
                    
        except Exception as e:
            logger.warning(f"Error in pattern-based MD&A extraction: {e}")
            
        return None
    
    def _clean_mda_text(self, text: str) -> str:
        """
        Clean MD&A text for analysis
        
        Args:
            text: Raw MD&A text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove HTML tags if present
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common filing artifacts
        artifacts = [
            r'Table of Contents',
            r'\d+',  # Remove standalone numbers
            r'Page \d+',
            r'Form \d+-[A-Z]',
        ]
        
        for artifact in artifacts:
            text = re.sub(artifact, '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_all_mda(self, start_date: str = "2005-01-01", 
                       end_date: str = "2024-12-31", 
                       max_companies: Optional[int] = None) -> pd.DataFrame:
        """
        Extract MD&A data for all S&P 500 companies
        
        Args:
            start_date: Start date for filing search
            end_date: End date for filing search  
            max_companies: Limit number of companies (for testing)
            
        Returns:
            DataFrame with all extracted MD&A data
        """
        if self.sp500_companies is None:
            self.get_sp500_companies()
        
        companies_to_process = self.sp500_companies.copy()
        if max_companies:
            companies_to_process = companies_to_process.head(max_companies)
        
        logger.info(f"Starting MD&A extraction for {len(companies_to_process)} companies")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Process each company
        for idx, row in tqdm(companies_to_process.iterrows(), 
                           total=len(companies_to_process),
                           desc="Processing companies"):
            
            ticker = row['ticker']
            cik = row.get('cik', '')
            company_name = row.get('company_name', '')
            
            logger.info(f"Processing {ticker} - {company_name}")
            
            try:
                # Get filings for this company
                filings = self.get_company_filings(ticker, cik, start_date, end_date)
                
                # Extract MD&A from each filing
                for filing in filings:
                    mda_data = self.extract_mda_from_filing(filing)
                    if mda_data:
                        self.mda_data.append(mda_data)
                        logger.info(f"Extracted MD&A from {filing.form} filing for {ticker}")
                
                # Rate limiting - be respectful to SEC servers
                time.sleep(0.1)  # 100ms delay between companies
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                continue
        
        # Convert to DataFrame
        df = pd.DataFrame(self.mda_data)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = self.output_dir / f"sp500_mda_data_{timestamp}.csv"
        excel_filename = self.output_dir / f"sp500_mda_data_{timestamp}.xlsx"
        
        df.to_csv(csv_filename, index=False)
        df.to_excel(excel_filename, index=False)
        
        logger.info(f"Extracted MD&A data for {len(df)} filings")
        logger.info(f"Results saved to {csv_filename} and {excel_filename}")
        
        return df

    def create_finbert_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for FinBERT analysis
        
        Args:
            df: DataFrame with MD&A data
            
        Returns:
            DataFrame formatted for FinBERT
        """
        logger.info("Preparing data for FinBERT analysis...")
        
        # Create FinBERT-ready dataset
        finbert_data = []
        
        for idx, row in df.iterrows():
            text = row['mda_text']
            
            # Split long texts into chunks for FinBERT (max 512 tokens)
            chunks = self._chunk_text(text, max_length=450)  # Leave room for special tokens
            
            for i, chunk in enumerate(chunks):
                finbert_data.append({
                    'id': f"{row['ticker']}_{row['form_type']}_{row['filing_date']}_{i}",
                    'ticker': row['ticker'],
                    'company_name': row['company_name'],
                    'form_type': row['form_type'],
                    'filing_date': row['filing_date'],
                    'period_end': row['period_end'],
                    'chunk_number': i,
                    'total_chunks': len(chunks),
                    'text': chunk,
                    'text_length': len(chunk),
                    'word_count': len(chunk.split())
                })
        
        finbert_df = pd.DataFrame(finbert_data)
        
        # Save FinBERT dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        finbert_filename = self.output_dir / f"sp500_mda_finbert_{timestamp}.csv"
        finbert_df.to_csv(finbert_filename, index=False)
        
        logger.info(f"FinBERT dataset created with {len(finbert_df)} text chunks")
        logger.info(f"FinBERT dataset saved to {finbert_filename}")
        
        return finbert_df
    
    def _chunk_text(self, text: str, max_length: int = 450) -> List[str]:
        """
        Split text into chunks suitable for FinBERT
        
        Args:
            text: Input text
            max_length: Maximum length per chunk (in words)
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_length):
            chunk = ' '.join(words[i:i + max_length])
            chunks.append(chunk)
        
        return chunks


def main():
    """Main function to run the extraction"""
    parser = argparse.ArgumentParser(description='Extract MD&A data from S&P 500 SEC filings')
    parser.add_argument('--email', required=True, help='Your email address (required by SEC)')
    parser.add_argument('--start-date', default='2005-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--max-companies', type=int, help='Limit number of companies (for testing)')
    parser.add_argument('--create-finbert', action='store_true', help='Create FinBERT-ready dataset')
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = SP500MDAExtractor(
            output_dir=args.output_dir,
            user_email=args.email
        )
        
        # Extract MD&A data
        df = extractor.extract_all_mda(
            start_date=args.start_date,
            end_date=args.end_date,
            max_companies=args.max_companies
        )
        
        print(f"\nExtraction completed!")
        print(f"Total MD&A sections extracted: {len(df)}")
        print(f"Companies covered: {df['ticker'].nunique()}")
        print(f"Date range: {df['filing_date'].min()} to {df['filing_date'].max()}")
        
        # Create FinBERT dataset if requested
        if args.create_finbert:
            finbert_df = extractor.create_finbert_dataset(df)
            print(f"FinBERT dataset created with {len(finbert_df)} text chunks")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()