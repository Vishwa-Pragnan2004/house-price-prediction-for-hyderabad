"""
Hyderabad House Price Prediction System - Time Series Architecture
Advanced system with time series data analysis and forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import json
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeSeriesDataProcessor:
    """Handle time series data preprocessing and feature engineering"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.date_features = ['year', 'month', 'quarter', 'day_of_year', 'week_of_year']
        
    def load_time_series_data(self, file_path):
        """Load and validate time series data"""
        try:
            df = pd.read_csv(file_path)
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort by date
            df = df.sort_values('date')
            
            # Basic validation
            required_columns = ['date', 'location', 'total_sqft', 'bhk', 'bath', 'price']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            logger.info(f"Loaded time series data: {df.shape}")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"Locations: {df['location'].unique()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading time series data: {e}")
            raise
    
    def extract_date_features(self, df):
        """Extract time-based features from date column"""
        df = df.copy()
        
        # Basic date features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Cyclical features for seasonality
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['quarter_sin'] = np.sin(2 * np.pi * df['quarter'] / 4)
        df['quarter_cos'] = np.cos(2 * np.pi * df['quarter'] / 4)
        
        # Economic indicators (simplified)
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['is_quarter_end'] = df['month'].isin([3, 6, 9, 12]).astype(int)
        df['is_year_end'] = (df['month'] == 12).astype(int)
        
        return df
    
    def create_lag_features(self, df, target_col='price', lags=[1]):
        """Create lag features for time series analysis"""
        df = df.copy()
        
        # Sort by location and date for proper lag calculation
        df = df.sort_values(['location', 'date'])
        
        for location in df['location'].unique():
            location_mask = df['location'] == location
            location_data = df[location_mask].copy()
            
            # Only create lag features if we have enough data
            if len(location_data) > 1:
                for lag in lags:
                    if len(location_data) > lag:
                        # Price lags
                        location_data[f'price_lag_{lag}'] = location_data[target_col].shift(lag)
                        
                        # Price change lags
                        location_data[f'price_change_lag_{lag}'] = location_data[target_col].pct_change(lag)
                    else:
                        # Use default values for insufficient data
                        location_data[f'price_lag_{lag}'] = location_data[target_col].iloc[0]
                        location_data[f'price_change_lag_{lag}'] = 0.01  # Small positive change
                
                df.loc[location_mask, location_data.columns.difference(df.columns)] = location_data[location_data.columns.difference(df.columns)]
        
        return df
    
    def create_rolling_features(self, df, target_col='price', windows=[3]):
        """Create rolling window features"""
        df = df.copy()
        
        # Sort by location and date
        df = df.sort_values(['location', 'date'])
        
        for location in df['location'].unique():
            location_mask = df['location'] == location
            location_data = df[location_mask].copy()
            
            # Only create rolling features if we have enough data
            if len(location_data) >= 2:
                for window in windows:
                    if len(location_data) >= window:
                        # Rolling statistics
                        location_data[f'price_rolling_mean_{window}'] = location_data[target_col].rolling(window).mean()
                        location_data[f'price_rolling_std_{window}'] = location_data[target_col].rolling(window).std()
                        location_data[f'price_rolling_min_{window}'] = location_data[target_col].rolling(window).min()
                        location_data[f'price_rolling_max_{window}'] = location_data[target_col].rolling(window).max()
                        
                        # Rolling trend
                        location_data[f'price_rolling_trend_{window}'] = location_data[target_col].rolling(window).apply(
                            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == window else np.nan
                        )
                    else:
                        # Use available data for insufficient data
                        recent_prices = location_data[target_col]
                        location_data[f'price_rolling_mean_{window}'] = recent_prices.mean()
                        location_data[f'price_rolling_std_{window}'] = recent_prices.std()
                        location_data[f'price_rolling_min_{window}'] = recent_prices.min()
                        location_data[f'price_rolling_max_{window}'] = recent_prices.max()
                        location_data[f'price_rolling_trend_{window}'] = 1000  # Default positive trend
                
                df.loc[location_mask, location_data.columns.difference(df.columns)] = location_data[location_data.columns.difference(df.columns)]
        
        return df
    
    def create_location_features(self, df):
        """Create location-specific features"""
        df = df.copy()
        
        # Location-based price statistics
        location_stats = df.groupby('location')['price'].agg(['mean', 'median', 'std', 'min', 'max'])
        
        for stat in location_stats.columns:
            df[f'location_price_{stat}'] = df['location'].map(location_stats[stat])
        
        # Location price level (categorical)
        df['location_price_level'] = pd.cut(df['location_price_mean'], 
                                         bins=5, 
                                         labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        
        # Property features
        df['price_per_sqft'] = df['price'] / df['total_sqft']
        df['bhk_per_sqft'] = df['bhk'] / df['total_sqft']
        df['bath_per_sqft'] = df['bath'] / df['total_sqft']
        df['bhk_to_bath_ratio'] = df['bhk'] / df['bath']
        
        return df
    
    def encode_categorical_features(self, df):
        """Encode categorical features"""
        df = df.copy()
        
        categorical_columns = ['location', 'location_price_level']
        
        for col in categorical_columns:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    # Handle unseen categories
                    unique_values = set(df[col].astype(str).unique())
                    known_values = set(self.label_encoders[col].classes_)
                    
                    if unique_values - known_values:
                        # Add new categories to encoder
                        new_values = list(unique_values - known_values)
                        self.label_encoders[col].classes_ = np.append(
                            self.label_encoders[col].classes_, new_values
                        )
                    
                    df[col] = self.label_encoders[col].transform(df[col].astype(str))
        
        return df
    
    def preprocess_data(self, df):
        """Main preprocessing pipeline"""
        logger.info("Starting time series data preprocessing...")
        
        # Extract date features
        df = self.extract_date_features(df)
        
        # Create lag features
        df = self.create_lag_features(df)
        
        # Create rolling features
        df = self.create_rolling_features(df)
        
        # Create location features
        df = self.create_location_features(df)
        
        # Encode categorical features
        df = self.encode_categorical_features(df)
        
        # Remove rows with NaN values (from lag/rolling features)
        initial_rows = len(df)
        df = df.dropna()
        logger.info(f"Removed {initial_rows - len(df)} rows with NaN values")
        
        # Define feature columns
        exclude_columns = ['date', 'price']
        self.feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        logger.info(f"Final dataset shape: {df.shape}")
        logger.info(f"Feature columns: {len(self.feature_columns)}")
        
        return df

class TimeSeriesModelTrainer:
    """Handle time series model training and evaluation"""
    
    def __init__(self):
        self.models = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.best_model = None
        self.best_model_name = None
        self.model_performance = {}
        
    def train_time_series_split(self, X, y, test_size=0.2):
        """Train models using time series split"""
        logger.info("Training models with time series split...")
        
        # Time series split (no shuffling to maintain temporal order)
        split_index = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_index], X[split_index:]
        y_train, y_test = y[:split_index], y[split_index:]
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        # Train each model
        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            
            # Metrics
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            
            # Cross-validation (adjust folds based on data size)
            if len(X_train) >= 5:
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
            else:
                cv_scores = cross_val_score(model, X_train, y_train, cv=2, scoring='r2')
            
            self.model_performance[name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'mape': mape,
                'cv_score': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            logger.info(f"{name} - R²: {r2:.4f}, MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        # Select best model
        best_score = -float('inf')
        for name, performance in self.model_performance.items():
            if performance['cv_score'] > best_score:
                best_score = performance['cv_score']
                self.best_model = self.models[name]
                self.best_model_name = name
        
        # Fallback: if no model has valid CV score, use linear regression
        if self.best_model is None and 'linear_regression' in self.models:
            self.best_model = self.models['linear_regression']
            self.best_model_name = 'linear_regression'
            best_score = 0.0  # Default score
            logger.warning("Using linear regression as fallback due to invalid CV scores")
        
        logger.info(f"Best model: {self.best_model_name} (CV Score: {best_score:.4f})")
        
        return self.model_performance
    
    def predict(self, X):
        """Make predictions using the best model"""
        if self.best_model is None:
            raise ValueError("Model not trained yet")
        
        return self.best_model.predict(X)

class TimeSeriesForecaster:
    """Handle time series forecasting"""
    
    def __init__(self, model_trainer, data_processor):
        self.model_trainer = model_trainer
        self.data_processor = data_processor
        self.best_model = None
        self.best_model_name = None
    
    def predict(self, X):
        """Make predictions using the best model"""
        if self.best_model is None:
            raise ValueError("Model not trained yet")
        
        return self.best_model.predict(X)
    
    def forecast_future_prices(self, base_data, future_dates, location, property_features):
        """Forecast prices for future dates"""
        logger.info(f"Forecasting prices for {len(future_dates)} future dates...")
        
        forecasts = []
        
        # Get the latest data for the location
        location_data = base_data[base_data['location'] == location].copy()
        
        if len(location_data) == 0:
            raise ValueError(f"No historical data found for location: {location}")
        
        # Get the most recent data point
        latest_data = location_data.iloc[-1:].copy()
        
        # Calculate location statistics once
        location_stats = base_data[base_data['location'] == location]['price'].agg(['mean', 'median', 'std', 'min', 'max'])
        all_location_means = base_data.groupby('location')['price'].mean()
        price_levels = pd.cut(all_location_means, bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        
        for future_date in future_dates:
            try:
                # Convert to datetime if needed
                future_date_dt = pd.to_datetime(future_date)
                
                # Create future data point
                future_data = latest_data.copy()
                future_data['date'] = future_date_dt
                
                # Update date features
                future_data['year'] = future_date_dt.year
                future_data['month'] = future_date_dt.month
                future_data['quarter'] = (future_date_dt.month - 1) // 3 + 1
                future_data['day_of_year'] = future_date_dt.timetuple().tm_yday
                future_data['week_of_year'] = future_date_dt.isocalendar()[1]
                
                # Update cyclical features
                future_data['month_sin'] = np.sin(2 * np.pi * future_date_dt.month / 12)
                future_data['month_cos'] = np.cos(2 * np.pi * future_date_dt.month / 12)
                quarter = (future_date_dt.month - 1) // 3 + 1
                future_data['quarter_sin'] = np.sin(2 * np.pi * quarter / 4)
                future_data['quarter_cos'] = np.cos(2 * np.pi * quarter / 4)
                
                # Update time-based features
                future_data['days_since_start'] = (future_date_dt - base_data['date'].min()).days
                future_data['is_quarter_end'] = int(future_date_dt.month in [3, 6, 9, 12])
                future_data['is_year_end'] = int(future_date_dt.month == 12)
                
                # Update property features
                for feature, value in property_features.items():
                    if feature in future_data.columns:
                        future_data[feature] = value
                
                # Create location features
                future_data['location_price_mean'] = location_stats['mean']
                future_data['location_price_median'] = location_stats['median']
                future_data['location_price_std'] = location_stats['std']
                future_data['location_price_min'] = location_stats['min']
                future_data['location_price_max'] = location_stats['max']
                
                # Location price level (categorical)
                if location in price_levels.index:
                    future_data['location_price_level'] = price_levels[location]
                else:
                    future_data['location_price_level'] = 'Medium'  # Default
                
                # Property features (use actual input values)
                future_data['price_per_sqft'] = property_features.get('total_sqft', 1200) * 0.35  # Realistic price per sqft
                future_data['bhk_per_sqft'] = property_features.get('bhk', 2) / property_features.get('total_sqft', 1200)
                future_data['bath_per_sqft'] = property_features.get('bath', 2) / property_features.get('total_sqft', 1200)
                future_data['bhk_to_bath_ratio'] = property_features.get('bhk', 2) / property_features.get('bath', 2)
                
                # Apply trend and seasonality adjustments
                # Convert both to same datetime type for calculation
                future_date_dt = pd.to_datetime(future_date)
                latest_date_dt = pd.to_datetime(latest_data['date'].iloc[0])
                days_from_latest = (future_date_dt - latest_date_dt).days
                annual_trend = 0.05  # 5% annual appreciation
                seasonal_factor = 1.0 + 0.015 * np.sin(2 * np.pi * future_date_dt.month / 12)  # Reduced realistic seasonal variation
                
                # Create lag features (use latest available)
                for lag in [1]:
                    if len(location_data) >= lag:
                        future_data[f'price_lag_{lag}'] = location_data['price'].iloc[-lag]
                        future_data[f'price_change_lag_{lag}'] = (
                            location_data['price'].iloc[-1] / location_data['price'].iloc[-lag] - 1
                        )
                    else:
                        # Use available data or defaults
                        if len(location_data) > 0:
                            future_data[f'price_lag_{lag}'] = location_data['price'].iloc[-1]
                            future_data[f'price_change_lag_{lag}'] = 0.01  # Small positive change
                        else:
                            future_data[f'price_lag_{lag}'] = location_stats['mean']
                            future_data[f'price_change_lag_{lag}'] = 0.01
                
                # Create rolling features (use latest available)
                for window in [3]:
                    if len(location_data) >= window:
                        recent_prices = location_data['price'].tail(window)
                        future_data[f'price_rolling_mean_{window}'] = recent_prices.mean()
                        future_data[f'price_rolling_std_{window}'] = recent_prices.std()
                        future_data[f'price_rolling_min_{window}'] = recent_prices.min()
                        future_data[f'price_rolling_max_{window}'] = recent_prices.max()
                        
                        # Simple trend calculation
                        if len(recent_prices) == window:
                            x = np.arange(len(recent_prices))
                            trend_coeff = np.polyfit(x, recent_prices, 1)[0]
                            future_data[f'price_rolling_trend_{window}'] = trend_coeff
                        else:
                            future_data[f'price_rolling_trend_{window}'] = 1000  # Default positive trend
                    else:
                        # Use available data or defaults
                        if len(location_data) > 0:
                            recent_prices = location_data['price']
                            future_data[f'price_rolling_mean_{window}'] = recent_prices.mean()
                            future_data[f'price_rolling_std_{window}'] = recent_prices.std()
                            future_data[f'price_rolling_min_{window}'] = recent_prices.min()
                            future_data[f'price_rolling_max_{window}'] = recent_prices.max()
                            future_data[f'price_rolling_trend_{window}'] = 1000
                        else:
                            future_data[f'price_rolling_mean_{window}'] = location_stats['mean']
                            future_data[f'price_rolling_std_{window}'] = location_stats['std']
                            future_data[f'price_rolling_min_{window}'] = location_stats['min']
                            future_data[f'price_rolling_max_{window}'] = location_stats['max']
                            future_data[f'price_rolling_trend_{window}'] = 1000
                
                # Prepare for prediction
                future_data_processed = self.data_processor.encode_categorical_features(future_data)
                X_future = future_data_processed[self.data_processor.feature_columns]
                
                # Make prediction
                predicted_price = self.predict(X_future)[0]
                
                # The prediction model has learned the property feature relationships directly from the training data.
                # No manual scaling of base prices (like size or bhk multipliers) is necessary.
                adjusted_base_price = predicted_price
                
                # Apply trend and seasonal adjustments to the property-adjusted price
                adjusted_price = adjusted_base_price * (1 + annual_trend * days_from_latest / 365) * seasonal_factor
                
                forecasts.append({
                    'date': future_date,
                    'predicted_price': adjusted_price,
                    'base_price': adjusted_base_price,
                    'days_from_latest': days_from_latest,
                    'trend_factor': (1 + annual_trend * days_from_latest / 365),
                    'seasonal_factor': seasonal_factor
                })
                
            except Exception as e:
                logger.error(f"Error forecasting for date {future_date}: {e}")
                # Create a fallback forecast
                base_price = location_stats['mean']
                days_from_latest = (future_date - latest_data['date'].iloc[0]).days
                annual_trend = 0.05
                seasonal_factor = 1.0 + 0.015 * np.sin(2 * np.pi * future_date.month / 12)
                adjusted_price = base_price * (1 + annual_trend * days_from_latest / 365) * seasonal_factor
                
                forecasts.append({
                    'date': future_date,
                    'predicted_price': adjusted_price,
                    'base_price': base_price,
                    'days_from_latest': days_from_latest,
                    'trend_factor': (1 + annual_trend * days_from_latest / 365),
                    'seasonal_factor': seasonal_factor
                })
        
        return forecasts

class HyderabadTimeSeriesPredictor:
    """Main time series prediction system for Hyderabad house prices"""
    
    def __init__(self):
        self.data_processor = TimeSeriesDataProcessor()
        self.model_trainer = TimeSeriesModelTrainer()
        self.forecaster = None
        self.training_data = None
        self.is_trained = False
    
    def load_and_train(self, csv_path):
        """Load time series data and train models"""
        logger.info("=== Hyderabad Time Series House Price Prediction System ===")
        
        # Load data
        self.training_data = self.data_processor.load_time_series_data(csv_path)
        
        # Preprocess data
        processed_data = self.data_processor.preprocess_data(self.training_data)
        
        # Prepare features and target
        X = processed_data[self.data_processor.feature_columns]
        y = processed_data['price']
        
        # Train models
        performance = self.model_trainer.train_time_series_split(X, y)
        
        # Initialize forecaster
        self.forecaster = TimeSeriesForecaster(self.model_trainer, self.data_processor)
        self.is_trained = True
        
        # Pass the trained model to the forecaster
        self.forecaster.best_model = self.model_trainer.best_model
        self.forecaster.best_model_name = self.model_trainer.best_model_name
        
        return performance
    
    def predict_property_price(self, location, total_sqft, bhk, bath, prediction_date):
        """Predict price for a specific property on a specific date"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        property_features = {
            'total_sqft': total_sqft,
            'bhk': bhk,
            'bath': bath
        }
        
        forecasts = self.forecaster.forecast_future_prices(
            self.training_data, [prediction_date], location, property_features
        )
        
        if forecasts:
            return forecasts[0]
        else:
            raise ValueError("Unable to generate forecast")
    
    def forecast_price_trend(self, location, total_sqft, bhk, bath, start_date, end_date, frequency='monthly'):
        """Forecast price trend over a date range"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        # Generate date range
        if frequency == 'daily':
            dates = pd.date_range(start_date, end_date, freq='D')
        elif frequency == 'weekly':
            dates = pd.date_range(start_date, end_date, freq='W')
        elif frequency == 'biweekly':
            dates = pd.date_range(start_date, end_date, freq='2W')
        else:  # monthly
            dates = pd.date_range(start_date, end_date, freq='M')
        
        property_features = {
            'total_sqft': total_sqft,
            'bhk': bhk,
            'bath': bath
        }
        
        forecasts = self.forecaster.forecast_future_prices(
            self.training_data, dates, location, property_features
        )
        
        return forecasts
    
    def get_model_info(self):
        """Get model information"""
        if not self.is_trained:
            return {'status': 'not_trained'}
        
        return {
            'status': 'trained',
            'best_model': self.model_trainer.best_model_name,
            'performance': self.model_trainer.model_performance,
            'training_data_shape': self.training_data.shape,
            'date_range': [self.training_data['date'].min(), self.training_data['date'].max()],
            'locations': list(self.training_data['location'].unique()),
            'feature_count': len(self.data_processor.feature_columns)
        }

# Convenience function for loading time series data
def load_hyd_time_series_data():
    """Load Hyderabad time series data from hyd.csv"""
    csv_path = "data/hyd.csv"
    
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        return csv_path
    else:
        # Fallback to expanded BHK dataset (most realistic)
        template_path = "data/hyd_expanded_bhk_dataset.csv"
        if os.path.exists(template_path):
            logger.warning("Using expanded BHK dataset with realistic price differences")
            return template_path
        else:
            # Fallback to all locations template
            template_path = "data/hyd_all_locations_template.csv"
            if os.path.exists(template_path):
                logger.warning("Using all locations template data. Please add your data to hyd.csv")
                return template_path
            else:
                # Fallback to realistic template
                template_path = "data/hyd_realistic_template.csv"
                if os.path.exists(template_path):
                    logger.warning("Using realistic time series template data. Please add your data to hyd.csv")
                    return template_path
                else:
                    # Fallback to comprehensive template
                    template_path = "data/hyd_time_series_comprehensive.csv"
                    if os.path.exists(template_path):
                        logger.warning("Using comprehensive time series template data. Please add your data to hyd.csv")
                        return template_path
                    else:
                        raise FileNotFoundError("No time series data found. Please add data to data/hyd.csv")

if __name__ == "__main__":
    # Example usage
    try:
        # Initialize predictor
        predictor = HyderabadTimeSeriesPredictor()
        
        # Load and train
        csv_path = load_hyd_time_series_data()
        performance = predictor.load_and_train(csv_path)
        
        # Display results
        print("\n=== Training Results ===")
        for model, metrics in performance.items():
            print(f"{model}:")
            print(f"  R²: {metrics['r2']:.4f}")
            print(f"  MAE: {metrics['mae']:,.2f}")
            print(f"  RMSE: {metrics['rmse']:,.2f}")
            print(f"  CV Score: {metrics['cv_score']:.4f}")
        
        # Example prediction
        prediction = predictor.predict_property_price(
            location='Madhapur',
            total_sqft=1200,
            bhk=2,
            bath=2,
            prediction_date=datetime(2024, 6, 1)
        )
        
        print(f"\n=== Sample Prediction ===")
        print(f"Predicted price: ₹{prediction['predicted_price']:,.0f}")
        print(f"Date: {prediction['date']}")
        
        # Example trend forecast
        trend = predictor.forecast_price_trend(
            location='Madhapur',
            total_sqft=1200,
            bhk=2,
            bath=2,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            frequency='monthly'
        )
        
        print(f"\n=== Price Trend Forecast ===")
        for forecast in trend[:3]:  # Show first 3
            print(f"{forecast['date'].strftime('%Y-%m-%d')}: ₹{forecast['predicted_price']:,.0f}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        print("Please ensure you have time series data in data/hyd.csv")
