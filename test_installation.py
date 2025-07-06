#!/usr/bin/env python3
"""
Installation Test Script

This script tests the basic functionality of the S&P 500 MD&A extractor
to ensure all dependencies are properly installed and working.

Run this before attempting the full extraction.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False
    
    try:
        from edgar import *
        print("✅ edgartools imported successfully")
    except ImportError as e:
        print(f"❌ edgartools import failed: {e}")
        print("   Try: pip install edgartools")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4 imported successfully")
    except ImportError as e:
        print(f"❌ beautifulsoup4 import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✅ torch imported successfully (version: {torch.__version__})")
        if torch.cuda.is_available():
            print(f"   🚀 CUDA available with {torch.cuda.device_count()} GPU(s)")
        else:
            print("   💻 CUDA not available, will use CPU")
    except ImportError as e:
        print(f"❌ torch import failed: {e}")
        print("   Try: pip install torch")
        return False
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        print("✅ transformers imported successfully")
    except ImportError as e:
        print(f"❌ transformers import failed: {e}")
        return False
    
    try:
        import tqdm
        print("✅ tqdm imported successfully")
    except ImportError as e:
        print(f"❌ tqdm import failed: {e}")
        return False
    
    return True


def test_edgar_connection():
    """Test connection to SEC EDGAR"""
    print("\nTesting EDGAR connection...")
    
    try:
        # Set a test identity
        set_identity("test@example.com")
        print("✅ Edgar identity set successfully")
        
        # Try to get a simple company
        company = Company("AAPL")
        print(f"✅ Successfully connected to EDGAR and found {company.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ EDGAR connection failed: {e}")
        return False


def test_sp500_data_fetch():
    """Test fetching S&P 500 company data"""
    print("\nTesting S&P 500 data fetch...")
    
    try:
        import pandas as pd
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_df = tables[0]
        
        print(f"✅ Successfully fetched S&P 500 data: {len(sp500_df)} companies")
        return True
        
    except Exception as e:
        print(f"❌ S&P 500 data fetch failed: {e}")
        return False


def test_finbert_model():
    """Test loading FinBERT model"""
    print("\nTesting FinBERT model loading...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        
        model_name = "ProsusAI/finbert"
        print(f"Loading {model_name}...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Test a simple sentiment analysis
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            return_all_scores=True
        )
        
        test_text = "The company reported strong revenue growth this quarter."
        result = sentiment_pipeline(test_text)
        
        print("✅ FinBERT model loaded and tested successfully")
        print(f"   Test sentiment analysis result: {result[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ FinBERT model test failed: {e}")
        print("   This might be due to internet connection or model download issues")
        return False


def test_output_directory():
    """Test creating output directory"""
    print("\nTesting output directory creation...")
    
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Test write permissions
        test_file = output_dir / "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        
        test_file.unlink()  # Remove test file
        
        print("✅ Output directory created and writable")
        return True
        
    except Exception as e:
        print(f"❌ Output directory test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("S&P 500 MD&A EXTRACTOR - INSTALLATION TEST")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("EDGAR Connection", test_edgar_connection),
        ("S&P 500 Data Fetch", test_sp500_data_fetch),
        ("Output Directory", test_output_directory),
        ("FinBERT Model", test_finbert_model),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the MD&A extractor.")
        print("\nNext steps:")
        print("1. Run a small test: python sp500_mda_extractor.py --email your@email.com --max-companies 2")
        print("2. If that works, run the full extraction")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before proceeding.")
        print("\nCommon solutions:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Check internet connection for model downloads")
        print("- Ensure you have write permissions in the current directory")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)