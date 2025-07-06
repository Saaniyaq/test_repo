#!/usr/bin/env python3
"""
FinBERT Sentiment Analysis for MD&A Data

This script performs sentiment analysis on the extracted MD&A sections
using the FinBERT model, which is specifically trained for financial text.

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from datetime import datetime
import logging
from pathlib import Path
import argparse
from tqdm import tqdm
import json
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinBERTAnalyzer:
    """Class for performing FinBERT sentiment analysis on MD&A data"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize the FinBERT analyzer
        
        Args:
            model_name: Hugging Face model name for FinBERT
        """
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Load tokenizer and model
        logger.info(f"Loading FinBERT model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        
        # Create sentiment analysis pipeline
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1,
            return_all_scores=True
        )
        
        logger.info("FinBERT model loaded successfully")
    
    def analyze_sentiment(self, text: str) -> dict:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        try:
            # Truncate text if too long (FinBERT max length is 512 tokens)
            inputs = self.tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
            
            # Get predictions
            results = self.sentiment_pipeline(text)
            
            # Extract scores
            sentiment_scores = {}
            for result in results[0]:
                label = result['label'].lower()
                score = result['score']
                sentiment_scores[label] = score
            
            # Determine dominant sentiment
            dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            confidence = sentiment_scores[dominant_sentiment]
            
            return {
                'positive': sentiment_scores.get('positive', 0.0),
                'negative': sentiment_scores.get('negative', 0.0),
                'neutral': sentiment_scores.get('neutral', 0.0),
                'dominant_sentiment': dominant_sentiment,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return {
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 0.0,
                'dominant_sentiment': 'neutral',
                'confidence': 0.0
            }
    
    def analyze_dataframe(self, df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
        """
        Analyze sentiment for all texts in a DataFrame
        
        Args:
            df: DataFrame with text data
            text_column: Name of column containing text to analyze
            
        Returns:
            DataFrame with added sentiment columns
        """
        logger.info(f"Analyzing sentiment for {len(df)} text samples...")
        
        # Initialize result columns
        df = df.copy()
        df['sentiment_positive'] = 0.0
        df['sentiment_negative'] = 0.0
        df['sentiment_neutral'] = 0.0
        df['dominant_sentiment'] = 'neutral'
        df['sentiment_confidence'] = 0.0
        
        # Analyze each text
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Analyzing sentiment"):
            text = row[text_column]
            
            if pd.isna(text) or len(text.strip()) == 0:
                continue
                
            sentiment_result = self.analyze_sentiment(text)
            
            # Update DataFrame with results
            df.at[idx, 'sentiment_positive'] = sentiment_result['positive']
            df.at[idx, 'sentiment_negative'] = sentiment_result['negative']
            df.at[idx, 'sentiment_neutral'] = sentiment_result['neutral']
            df.at[idx, 'dominant_sentiment'] = sentiment_result['dominant_sentiment']
            df.at[idx, 'sentiment_confidence'] = sentiment_result['confidence']
        
        logger.info("Sentiment analysis completed")
        return df
    
    def aggregate_company_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate sentiment scores by company and time period
        
        Args:
            df: DataFrame with sentiment analysis results
            
        Returns:
            DataFrame with aggregated company sentiment metrics
        """
        logger.info("Aggregating sentiment by company...")
        
        # Group by company and filing date
        agg_results = []
        
        for (ticker, filing_date), group in df.groupby(['ticker', 'filing_date']):
            # Calculate average sentiment scores
            avg_positive = group['sentiment_positive'].mean()
            avg_negative = group['sentiment_negative'].mean()
            avg_neutral = group['sentiment_neutral'].mean()
            
            # Calculate weighted sentiment (positive - negative)
            weighted_sentiment = avg_positive - avg_negative
            
            # Determine overall sentiment
            if weighted_sentiment > 0.1:
                overall_sentiment = 'positive'
            elif weighted_sentiment < -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Calculate sentiment volatility (standard deviation)
            sentiment_volatility = group['sentiment_confidence'].std()
            
            agg_results.append({
                'ticker': ticker,
                'company_name': group['company_name'].iloc[0],
                'filing_date': filing_date,
                'form_type': group['form_type'].iloc[0],
                'period_end': group['period_end'].iloc[0] if 'period_end' in group.columns else None,
                'total_chunks': len(group),
                'avg_positive': avg_positive,
                'avg_negative': avg_negative,
                'avg_neutral': avg_neutral,
                'weighted_sentiment': weighted_sentiment,
                'overall_sentiment': overall_sentiment,
                'sentiment_volatility': sentiment_volatility,
                'avg_confidence': group['sentiment_confidence'].mean()
            })
        
        agg_df = pd.DataFrame(agg_results)
        logger.info(f"Created aggregated sentiment data for {len(agg_df)} company-period combinations")
        
        return agg_df
    
    def create_sentiment_report(self, df: pd.DataFrame, output_dir: str = "output"):
        """
        Create comprehensive sentiment analysis report
        
        Args:
            df: DataFrame with sentiment analysis results
            output_dir: Directory to save report files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        logger.info("Creating sentiment analysis report...")
        
        # 1. Overall sentiment distribution
        sentiment_dist = df['dominant_sentiment'].value_counts()
        
        # 2. Sentiment by company
        company_sentiment = df.groupby('ticker').agg({
            'sentiment_positive': 'mean',
            'sentiment_negative': 'mean',
            'sentiment_neutral': 'mean',
            'dominant_sentiment': lambda x: x.value_counts().index[0]
        }).round(3)
        
        # 3. Sentiment trends over time
        if 'filing_date' in df.columns:
            df['filing_year'] = pd.to_datetime(df['filing_date']).dt.year
            yearly_sentiment = df.groupby('filing_year').agg({
                'sentiment_positive': 'mean',
                'sentiment_negative': 'mean',
                'sentiment_neutral': 'mean'
            }).round(3)
        
        # 4. Top positive and negative companies
        top_positive = company_sentiment.nlargest(10, 'sentiment_positive')
        top_negative = company_sentiment.nlargest(10, 'sentiment_negative')
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create visualizations
        self._create_sentiment_visualizations(df, output_path)
        
        # Save summary statistics
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "total_texts_analyzed": len(df),
            "companies_analyzed": df['ticker'].nunique() if 'ticker' in df.columns else 'N/A',
            "overall_sentiment_distribution": sentiment_dist.to_dict(),
            "average_sentiment_scores": {
                "positive": df['sentiment_positive'].mean(),
                "negative": df['sentiment_negative'].mean(),
                "neutral": df['sentiment_neutral'].mean()
            }
        }
        
        with open(output_path / f"sentiment_summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed company results
        company_sentiment.to_csv(output_path / f"company_sentiment_{timestamp}.csv")
        
        logger.info(f"Sentiment analysis report saved to {output_path}")
        
        return summary
    
    def _create_sentiment_visualizations(self, df: pd.DataFrame, output_path: Path):
        """Create sentiment analysis visualizations"""
        
        plt.style.use('default')
        
        # 1. Overall sentiment distribution
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Sentiment distribution pie chart
        sentiment_counts = df['dominant_sentiment'].value_counts()
        axes[0, 0].pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%')
        axes[0, 0].set_title('Overall Sentiment Distribution')
        
        # Sentiment scores histogram
        sentiment_scores = df[['sentiment_positive', 'sentiment_negative', 'sentiment_neutral']]
        sentiment_scores.plot(kind='hist', alpha=0.7, bins=30, ax=axes[0, 1])
        axes[0, 1].set_title('Sentiment Score Distributions')
        axes[0, 1].set_xlabel('Score')
        
        # Sentiment by company (top 20)
        if 'ticker' in df.columns:
            company_avg = df.groupby('ticker')['sentiment_positive'].mean().nlargest(20)
            company_avg.plot(kind='bar', ax=axes[1, 0])
            axes[1, 0].set_title('Top 20 Companies by Positive Sentiment')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Sentiment trends over time
        if 'filing_date' in df.columns:
            df['filing_date'] = pd.to_datetime(df['filing_date'])
            monthly_sentiment = df.set_index('filing_date').resample('M')[
                ['sentiment_positive', 'sentiment_negative', 'sentiment_neutral']
            ].mean()
            monthly_sentiment.plot(ax=axes[1, 1])
            axes[1, 1].set_title('Sentiment Trends Over Time')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path / 'sentiment_analysis_charts.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Sentiment visualizations created")


def main():
    """Main function for FinBERT analysis"""
    parser = argparse.ArgumentParser(description='Perform FinBERT sentiment analysis on MD&A data')
    parser.add_argument('--input-file', required=True, help='Input CSV file with MD&A data')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--text-column', default='text', help='Name of text column to analyze')
    parser.add_argument('--model', default='ProsusAI/finbert', help='FinBERT model name')
    parser.add_argument('--aggregate', action='store_true', help='Create aggregated company sentiment')
    parser.add_argument('--create-report', action='store_true', help='Create comprehensive report')
    
    args = parser.parse_args()
    
    try:
        # Load data
        logger.info(f"Loading data from {args.input_file}")
        df = pd.read_csv(args.input_file)
        logger.info(f"Loaded {len(df)} records")
        
        # Initialize analyzer
        analyzer = FinBERTAnalyzer(model_name=args.model)
        
        # Perform sentiment analysis
        df_with_sentiment = analyzer.analyze_dataframe(df, text_column=args.text_column)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(args.output_dir)
        output_path.mkdir(exist_ok=True)
        
        output_file = output_path / f"mda_sentiment_analysis_{timestamp}.csv"
        df_with_sentiment.to_csv(output_file, index=False)
        logger.info(f"Sentiment analysis results saved to {output_file}")
        
        # Create aggregated results if requested
        if args.aggregate and 'ticker' in df.columns:
            agg_df = analyzer.aggregate_company_sentiment(df_with_sentiment)
            agg_file = output_path / f"company_sentiment_aggregated_{timestamp}.csv"
            agg_df.to_csv(agg_file, index=False)
            logger.info(f"Aggregated sentiment results saved to {agg_file}")
        
        # Create comprehensive report if requested
        if args.create_report:
            summary = analyzer.create_sentiment_report(df_with_sentiment, args.output_dir)
            logger.info("Comprehensive sentiment report created")
            
            # Print summary
            print("\n" + "="*50)
            print("SENTIMENT ANALYSIS SUMMARY")
            print("="*50)
            print(f"Total texts analyzed: {summary['total_texts_analyzed']}")
            if summary['companies_analyzed'] != 'N/A':
                print(f"Companies analyzed: {summary['companies_analyzed']}")
            print(f"Average sentiment scores:")
            for sentiment, score in summary['average_sentiment_scores'].items():
                print(f"  {sentiment.capitalize()}: {score:.3f}")
            print(f"Sentiment distribution:")
            for sentiment, count in summary['overall_sentiment_distribution'].items():
                print(f"  {sentiment.capitalize()}: {count}")
        
        print(f"\nAnalysis completed successfully!")
        print(f"Results saved to: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise


if __name__ == "__main__":
    main()