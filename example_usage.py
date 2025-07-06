#!/usr/bin/env python3
"""
Example Usage of S&P 500 MD&A Extractor

This script demonstrates how to use the extractor programmatically
for a small test case.
"""

import pandas as pd
from pathlib import Path
import sys

# Import our modules (make sure they're in the same directory)
try:
    from sp500_mda_extractor import SP500MDAExtractor
    from finbert_analyzer import FinBERTAnalyzer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure sp500_mda_extractor.py and finbert_analyzer.py are in the same directory")
    sys.exit(1)


def run_example():
    """Run a complete example with a few companies"""
    
    print("=" * 60)
    print("S&P 500 MD&A EXTRACTOR - EXAMPLE USAGE")
    print("=" * 60)
    
    # Replace with your actual email
    user_email = "your.email@example.com"
    
    # Initialize the extractor
    print("Initializing MD&A extractor...")
    extractor = SP500MDAExtractor(
        output_dir="example_output",
        user_email=user_email
    )
    
    # Extract MD&A data for a few companies (test mode)
    print("\nExtracting MD&A data for 3 companies (2020-2023)...")
    df = extractor.extract_all_mda(
        start_date="2020-01-01",
        end_date="2023-12-31",
        max_companies=3  # Just test with 3 companies
    )
    
    if len(df) == 0:
        print("No MD&A data extracted. This might be due to:")
        print("- Network issues")
        print("- SEC rate limiting")
        print("- Invalid email address")
        return
    
    print(f"\nExtracted {len(df)} MD&A sections from {df['ticker'].nunique()} companies")
    
    # Show some basic statistics
    print("\nBasic Statistics:")
    print(f"- Total companies: {df['ticker'].nunique()}")
    print(f"- Total filings: {len(df)}")
    print(f"- Date range: {df['filing_date'].min()} to {df['filing_date'].max()}")
    print(f"- Average MD&A length: {df['mda_length'].mean():.0f} characters")
    print(f"- Average word count: {df['word_count'].mean():.0f} words")
    
    # Show sample data
    print("\nSample MD&A data:")
    sample_columns = ['ticker', 'company_name', 'form_type', 'filing_date', 'word_count']
    print(df[sample_columns].head())
    
    # Create FinBERT dataset
    print("\nCreating FinBERT-ready dataset...")
    finbert_df = extractor.create_finbert_dataset(df)
    
    print(f"Created {len(finbert_df)} text chunks for FinBERT analysis")
    
    # Run sentiment analysis
    print("\nRunning FinBERT sentiment analysis...")
    analyzer = FinBERTAnalyzer()
    
    # Analyze sentiment (this might take a few minutes)
    sentiment_df = analyzer.analyze_dataframe(finbert_df)
    
    print("Sentiment analysis completed!")
    
    # Show sentiment results
    print("\nSentiment Analysis Results:")
    sentiment_summary = sentiment_df['dominant_sentiment'].value_counts()
    print(sentiment_summary)
    
    # Create aggregated company sentiment
    print("\nCreating company-level sentiment aggregation...")
    company_sentiment = analyzer.aggregate_company_sentiment(sentiment_df)
    
    print("\nCompany Sentiment Summary:")
    print(company_sentiment[['ticker', 'company_name', 'overall_sentiment', 'weighted_sentiment']].head())
    
    # Create comprehensive report
    print("\nGenerating comprehensive sentiment report...")
    summary = analyzer.create_sentiment_report(sentiment_df, "example_output")
    
    print("\n" + "=" * 60)
    print("EXAMPLE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Results saved to: example_output/")
    print("\nFiles created:")
    output_dir = Path("example_output")
    if output_dir.exists():
        for file in output_dir.iterdir():
            if file.is_file():
                print(f"- {file.name}")
    
    print("\nNext steps:")
    print("1. Review the generated files")
    print("2. Adjust parameters for your needs")
    print("3. Run the full extraction for all S&P 500 companies")


def quick_test():
    """Run a very quick test to verify everything works"""
    
    print("Running quick functionality test...")
    
    # Test imports
    try:
        from edgar import set_identity, Company
        print("✅ Edgar imports working")
    except:
        print("❌ Edgar imports failed")
        return False
    
    # Test S&P 500 data fetch
    try:
        import pandas as pd
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_df = tables[0]
        print(f"✅ S&P 500 data fetched: {len(sp500_df)} companies")
    except:
        print("❌ S&P 500 data fetch failed")
        return False
    
    # Test FinBERT
    try:
        from transformers import pipeline
        sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        result = sentiment_pipeline("Revenue increased significantly this quarter.")
        print("✅ FinBERT model working")
    except:
        print("❌ FinBERT model failed")
        return False
    
    print("✅ All quick tests passed!")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Example usage of S&P 500 MD&A extractor')
    parser.add_argument('--quick-test', action='store_true', help='Run quick functionality test only')
    parser.add_argument('--email', default='your.email@example.com', help='Your email address')
    
    args = parser.parse_args()
    
    if args.quick_test:
        success = quick_test()
        sys.exit(0 if success else 1)
    else:
        if args.email == 'your.email@example.com':
            print("⚠️  Please provide your actual email address with --email")
            print("Example: python example_usage.py --email your.actual.email@domain.com")
            sys.exit(1)
        
        # Update the email in the global variable
        globals()['user_email'] = args.email
        run_example()