# S&P 500 MD&A Data Extractor for FinBERT Analysis

This project extracts Management Discussion and Analysis (MD&A) sections from SEC filings (10-K and 10-Q) for all S&P 500 companies and creates structured datasets suitable for FinBERT sentiment analysis.

## Overview

The project consists of two main components:

1. **MD&A Data Extractor** (`sp500_mda_extractor.py`) - Extracts MD&A sections from SEC filings
2. **FinBERT Sentiment Analyzer** (`finbert_analyzer.py`) - Performs sentiment analysis on extracted MD&A text

## Features

- ✅ **Complete S&P 500 Coverage**: Automatically fetches all current S&P 500 companies with CIK codes
- ✅ **Bulk SEC Data Extraction**: Downloads and processes 10-K and 10-Q filings from 2005-2024
- ✅ **MD&A Section Parsing**: Intelligently extracts Item 7 (MD&A) sections using multiple methods
- ✅ **Clean Text Processing**: Removes HTML, formatting artifacts, and prepares text for analysis
- ✅ **FinBERT Integration**: Ready-to-use sentiment analysis with financial domain-specific BERT
- ✅ **Multiple Output Formats**: CSV, Excel, and JSON outputs
- ✅ **Progress Tracking**: Detailed logging and progress bars
- ✅ **Rate Limiting**: Respectful to SEC servers with built-in delays
- ✅ **Error Handling**: Robust error handling and recovery

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd sp500-mda-extractor
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install PyTorch (if not included):**
```bash
# For CPU only
pip install torch

# For GPU (CUDA 11.8)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

### Step 1: Extract MD&A Data

Extract MD&A sections from SEC filings for all S&P 500 companies:

```bash
python sp500_mda_extractor.py --email your.email@example.com
```

**Options:**
- `--email`: Your email address (required by SEC)
- `--start-date`: Start date (default: 2005-01-01)
- `--end-date`: End date (default: 2024-12-31)  
- `--output-dir`: Output directory (default: output)
- `--max-companies`: Limit companies for testing (optional)
- `--create-finbert`: Create FinBERT-ready dataset

### Step 2: Perform Sentiment Analysis

Analyze sentiment using FinBERT:

```bash
python finbert_analyzer.py --input-file output/sp500_mda_finbert_*.csv --create-report --aggregate
```

**Options:**
- `--input-file`: Input CSV file with MD&A data
- `--output-dir`: Output directory (default: output)
- `--text-column`: Text column name (default: text)
- `--model`: FinBERT model (default: ProsusAI/finbert)
- `--aggregate`: Create company-level aggregated results
- `--create-report`: Generate comprehensive report with visualizations

## Example Usage

### Testing with Limited Companies

Start with a small test to verify everything works:

```bash
# Test with just 5 companies
python sp500_mda_extractor.py \
    --email your.email@example.com \
    --max-companies 5 \
    --create-finbert

# Analyze the test results
python finbert_analyzer.py \
    --input-file output/sp500_mda_finbert_*.csv \
    --create-report \
    --aggregate
```

### Full S&P 500 Extraction

For the complete dataset:

```bash
# Extract all S&P 500 companies (this will take several hours)
python sp500_mda_extractor.py \
    --email your.email@example.com \
    --start-date 2005-01-01 \
    --end-date 2024-12-31 \
    --create-finbert

# Perform comprehensive sentiment analysis
python finbert_analyzer.py \
    --input-file output/sp500_mda_finbert_*.csv \
    --create-report \
    --aggregate
```

### Custom Date Range

Extract data for specific time periods:

```bash
# Focus on recent years
python sp500_mda_extractor.py \
    --email your.email@example.com \
    --start-date 2020-01-01 \
    --end-date 2024-12-31 \
    --create-finbert
```

## Output Files

### MD&A Extraction Outputs

1. **`sp500_companies.csv`** - S&P 500 company list with CIK codes
2. **`sp500_mda_data_TIMESTAMP.csv`** - Raw MD&A sections with metadata
3. **`sp500_mda_data_TIMESTAMP.xlsx`** - Excel version of MD&A data
4. **`sp500_mda_finbert_TIMESTAMP.csv`** - FinBERT-ready text chunks
5. **`sp500_mda_extraction.log`** - Detailed extraction logs

### Sentiment Analysis Outputs

1. **`mda_sentiment_analysis_TIMESTAMP.csv`** - Individual text sentiment scores
2. **`company_sentiment_aggregated_TIMESTAMP.csv`** - Company-level aggregated sentiment
3. **`sentiment_summary_TIMESTAMP.json`** - Summary statistics
4. **`company_sentiment_TIMESTAMP.csv`** - Company sentiment rankings
5. **`sentiment_analysis_charts.png`** - Visualization charts

## Data Schema

### MD&A Data Fields

| Column | Description |
|--------|-------------|
| `ticker` | Company stock ticker |
| `company_name` | Company name |
| `cik` | SEC Central Index Key |
| `form_type` | Filing type (10-K or 10-Q) |
| `filing_date` | Date filing was submitted |
| `period_end` | Reporting period end date |
| `accession_number` | SEC accession number |
| `url` | Filing URL |
| `mda_text` | Cleaned MD&A text |
| `mda_length` | Character count |
| `word_count` | Word count |

### FinBERT Analysis Fields

| Column | Description |
|--------|-------------|
| `id` | Unique text chunk identifier |
| `ticker` | Company ticker |
| `chunk_number` | Chunk sequence number |
| `text` | Text chunk for analysis |
| `sentiment_positive` | Positive sentiment score (0-1) |
| `sentiment_negative` | Negative sentiment score (0-1) |
| `sentiment_neutral` | Neutral sentiment score (0-1) |
| `dominant_sentiment` | Strongest sentiment class |
| `sentiment_confidence` | Confidence score |

## Advanced Usage

### Custom FinBERT Models

Use different FinBERT models:

```bash
# Use a different FinBERT variant
python finbert_analyzer.py \
    --input-file output/sp500_mda_finbert_*.csv \
    --model yiyanghkust/finbert-tone \
    --create-report
```

### Programmatic Usage

```python
from sp500_mda_extractor import SP500MDAExtractor
from finbert_analyzer import FinBERTAnalyzer

# Extract MD&A data
extractor = SP500MDAExtractor(
    output_dir="my_output",
    user_email="your.email@example.com"
)

# Extract for specific date range
df = extractor.extract_all_mda(
    start_date="2020-01-01",
    end_date="2023-12-31",
    max_companies=10  # For testing
)

# Create FinBERT dataset
finbert_df = extractor.create_finbert_dataset(df)

# Perform sentiment analysis
analyzer = FinBERTAnalyzer()
results = analyzer.analyze_dataframe(finbert_df)

# Create aggregated results
company_sentiment = analyzer.aggregate_company_sentiment(results)
```

## Performance Considerations

### Extraction Performance

- **Full S&P 500**: ~6-12 hours depending on connection speed
- **Rate Limiting**: 100ms delay between companies (SEC requirement)
- **Memory Usage**: ~2-4GB RAM for full dataset
- **Storage**: ~1-5GB for complete dataset

### FinBERT Analysis Performance

- **CPU**: ~1-2 texts per second
- **GPU**: ~10-20 texts per second  
- **Memory**: 4-8GB RAM recommended
- **GPU Memory**: 4GB+ VRAM for optimal performance

## Troubleshooting

### Common Issues

1. **SEC Rate Limiting**
   ```
   Error: Too many requests
   ```
   - Solution: The script has built-in rate limiting. If you still get errors, increase the delay in the code.

2. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'edgar'
   ```
   - Solution: `pip install edgartools`

3. **CUDA/GPU Issues**
   ```
   RuntimeError: CUDA out of memory
   ```
   - Solution: Use CPU by setting `--device cpu` or reduce batch size

4. **Empty MD&A Sections**
   - Some filings may not have extractable MD&A sections due to formatting
   - The script uses multiple extraction methods as fallbacks

### Memory Optimization

For large datasets, consider:

```python
# Process in smaller batches
extractor = SP500MDAExtractor(user_email="email@example.com")
companies = extractor.get_sp500_companies()

# Process in batches of 50 companies
batch_size = 50
for i in range(0, len(companies), batch_size):
    batch = companies.iloc[i:i+batch_size]
    # Process batch...
```

## Data Quality Notes

- **Coverage**: Not all filings contain extractable MD&A sections
- **Quality**: Text quality varies by company and filing date
- **Completeness**: Earlier filings (2005-2010) may have lower extraction rates
- **Formatting**: Some text may contain formatting artifacts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Legal and Compliance

- **SEC Compliance**: Always provide a valid email address to identify yourself to the SEC
- **Rate Limiting**: The tool respects SEC fair usage policies
- **Data Usage**: Ensure you comply with SEC terms of service
- **Academic/Research Use**: This tool is designed for research and analysis purposes

## License

This project is released under the MIT License. See LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the logs in `sp500_mda_extraction.log`
3. Open an issue on GitHub with:
   - Error message
   - Command used
   - Sample of the log file

## Acknowledgments

- **EdgarTools**: Excellent SEC filing library
- **FinBERT**: Financial sentiment analysis model
- **SEC**: For providing public access to corporate filings

---

**Happy analyzing! 📊📈**