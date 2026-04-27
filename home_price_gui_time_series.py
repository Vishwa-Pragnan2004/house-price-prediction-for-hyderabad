"""
Hyderabad House Price Predictor - Time Series GUI
Advanced interface with time series analysis and forecasting
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from home_price_time_series import HyderabadTimeSeriesPredictor, load_hyd_time_series_data

# Set page configuration
st.set_page_config(
    page_title="Hyderabad House Price Predictor - Time Series",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .prediction-card {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .constraint-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .price-info {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .time-series-badge {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid #bbdefb;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .model-info {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def validate_property_inputs(total_sqft, bhk, bath):
    """Validate property inputs against reasonable ranges"""
    
    errors = []
    warnings = []
    
    # Square feet validation
    if total_sqft < 500:
        errors.append("Square feet too low (minimum 500 sqft)")
    elif total_sqft > 5000:
        errors.append("Square feet too high (maximum 5000 sqft)")
    elif total_sqft > 3000:
        warnings.append("Very large property - prediction may be less accurate")
    
    # BHK validation
    if bhk < 1:
        errors.append("BHK too low (minimum 1 BHK)")
    elif bhk > 6:
        errors.append("BHK too high (maximum 6 BHK)")
    elif bhk > 4:
        warnings.append("Large BHK - prediction may be less accurate")
    
    # Bath validation
    if bath < 1:
        errors.append("Bathrooms too low (minimum 1)")
    elif bath > 6:
        errors.append("Bathrooms too high (maximum 6)")
    elif bath > bhk + 2:
        warnings.append("Many bathrooms for BHK count - unusual configuration")
    
    # Ratio validation
    if bhk > 0 and total_sqft / bhk < 150:
        warnings.append("Very small rooms - unusual configuration")
    elif bhk > 0 and total_sqft / bhk > 1500:
        warnings.append("Very large rooms - unusual configuration")
    
    return errors, warnings

@st.cache_resource(ttl=3600)  # Re-enabled caching for performance consistency per user request
def load_time_series_model():
    """Load and cache the time series model"""
    try:
        predictor = HyderabadTimeSeriesPredictor()
        
        # Load and train model
        csv_path = load_hyd_time_series_data()
        
        with st.spinner("Training time series model..."):
            performance = predictor.load_and_train(csv_path)
        
        st.success("✅ Time series model trained successfully!")
        return predictor, performance
        
    except Exception as e:
        st.error(f"Error loading time series model: {e}")
        return None, None

def create_time_series_chart(historical_data, forecasts=None, total_sqft=1200):
    """Create comprehensive time series visualization"""
    fig = go.Figure()
    
    # Historical data - normalized structurally to fix random variance scaling spikes 
    historical_data = historical_data.copy()
    historical_data['normalized_price'] = (historical_data['price'] / historical_data['total_sqft']) * total_sqft
    hist_agg = historical_data.groupby('date')['normalized_price'].mean().reset_index()
    
    fig.add_trace(go.Scatter(
        x=hist_agg['date'],
        y=hist_agg['normalized_price'],
        mode='lines+markers',
        name='Historical Trend (Normalized)',
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    # Forecasts
    if forecasts and len(forecasts) > 0:
        forecast_df = pd.DataFrame(forecasts)
        
        fig.add_trace(go.Scatter(
            x=forecast_df['date'],
            y=forecast_df['predicted_price'],
            mode='lines+markers',
            name='Forecasted Prices',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=6)
        ))
        
        # Add confidence band (if available)
        if 'base_price' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df['date'],
                y=forecast_df['base_price'],
                mode='lines',
                name='Base Forecast',
                line=dict(color='orange', width=1, dash='dot'),
                showlegend=False
            ))
    
    fig.update_layout(
        title='Hyderabad House Price Time Series Analysis',
        xaxis_title='Date',
        yaxis_title='Price (₹)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)')
    )
    
    return fig

def create_seasonal_decomposition_chart(data):
    """Create seasonal decomposition visualization"""
    if len(data) < 12:
        return None
    
    # Simple seasonal decomposition
    data_copy = data.copy()
    data_copy = data_copy.sort_values('date')
    data_copy.set_index('date', inplace=True)
    
    # Calculate moving average (trend)
    window = min(12, len(data_copy) // 3)
    data_copy['trend'] = data_copy['price'].rolling(window=window, center=True).mean()
    
    # Calculate seasonal component (simplified)
    data_copy['month'] = data_copy.index.month
    monthly_avg = data_copy.groupby('month')['price'].mean()
    data_copy['seasonal'] = data_copy['month'].map(monthly_avg)
    data_copy['seasonal'] = data_copy['seasonal'] / data_copy['seasonal'].mean()
    
    # Calculate residual
    data_copy['residual'] = data_copy['price'] / (data_copy['trend'] * data_copy['seasonal'])
    
    fig = go.Figure()
    
    # Original
    fig.add_trace(go.Scatter(
        x=data_copy.index,
        y=data_copy['price'],
        mode='lines',
        name='Original',
        line=dict(color='blue')
    ))
    
    # Trend
    fig.add_trace(go.Scatter(
        x=data_copy.index,
        y=data_copy['trend'],
        mode='lines',
        name='Trend',
        line=dict(color='red')
    ))
    
    # Seasonal (scaled)
    fig.add_trace(go.Scatter(
        x=data_copy.index,
        y=data_copy['seasonal'] * data_copy['price'].mean(),
        mode='lines',
        name='Seasonal',
        line=dict(color='green')
    ))
    
    fig.update_layout(
        title='Price Decomposition: Trend & Seasonality',
        xaxis_title='Date',
        yaxis_title='Price (₹)',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_location_comparison_chart(data):
    """Create location price comparison chart"""
    location_avg = data.groupby('location')['price'].mean().sort_values(ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=location_avg.index,
        y=location_avg.values,
        name='Average Price',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title='Average House Price by Location',
        xaxis_title='Location',
        yaxis_title='Average Price (₹)',
        template='plotly_white',
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def display_model_performance(performance):
    """Display model performance metrics"""
    st.markdown("## 📊 Model Performance")
    
    # Create performance table
    performance_data = []
    for model, metrics in performance.items():
        performance_data.append({
            'Model': model.replace('_', ' ').title(),
            'R² Score': f"{metrics['r2']:.4f}",
            'MAE': f"₹{metrics['mae']:,.0f}",
            'RMSE': f"₹{metrics['rmse']:,.0f}",
            'MAPE': f"{metrics['mape']:.2f}%",
            'CV Score': f"{metrics['cv_score']:.4f}"
        })
    
    df_performance = pd.DataFrame(performance_data)
    st.dataframe(df_performance, width='stretch')
    
    # Show best model
    best_model = max(performance.items(), key=lambda x: x[1]['cv_score'])
    st.markdown(f"### 🏆 Best Model: {best_model[0].replace('_', ' ').title()}")
    st.markdown(f"Cross-validation Score: {best_model[1]['cv_score']:.4f}")

def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏠 Hyderabad House Price Predictor - Time Series</h1>', unsafe_allow_html=True)
    st.markdown('<div class="time-series-badge">Advanced Time Series Analysis & Forecasting</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Load model
    predictor, performance = load_time_series_model()
    
    if predictor is None:
        st.error("❌ Unable to load time series model. Please check your data file.")
        st.info("💡 Make sure you have time series data in `data/hyd.csv` with columns: date, location, total_sqft, bhk, bath, price")
        return
    
    # Fetch model information (yellow box display was removed for cleaner UI)
    model_info = predictor.get_model_info()
    
    # Sidebar for inputs
    st.sidebar.markdown("## 🏠 Property Details")
    
    # Location selection
    location = st.sidebar.selectbox(
        "Location",
        options=model_info['locations'],
        help="Select the property location in Hyderabad"
    )
    
    # Property details
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        total_sqft = st.sidebar.number_input(
            "Total Square Feet",
            min_value=500,
            max_value=5000,
            value=1200,
            step=100,
            help="Total built-up area in square feet (500-5000)"
        )
        
        bhk = st.sidebar.number_input(
            "BHK",
            min_value=1,
            max_value=6,
            value=2,
            step=1,
            help="Number of bedrooms (1-6)"
        )
    
    with col2:
        bath = st.sidebar.number_input(
            "Bathrooms",
            min_value=1,
            max_value=6,
            value=2,
            step=1,
            help="Number of bathrooms (1-6)"
        )
    
    # Validate inputs and show warnings/errors
    errors, warnings = validate_property_inputs(total_sqft, bhk, bath)
    
    if errors:
        st.sidebar.error("❌ " + "\n❌ ".join(errors))
    if warnings:
        st.sidebar.warning("⚠️ " + "\n⚠️ ".join(warnings))
    
    # Prediction type
    prediction_type = st.sidebar.radio(
        "Prediction Type",
        options=['Single Date', 'Date Range Forecast'],
        help="Choose between single prediction or trend forecast"
    )
    
    if prediction_type == 'Single Date':
        prediction_date = st.sidebar.date_input(
            "Prediction Date",
            value=datetime.now().date(),
            help="Date for price prediction"
        )
        
        # Predict button
        predict_button = st.sidebar.button(
            "🔮 Predict Price",
            type="primary",
            width='stretch'
        )
        
    else:  # Date Range Forecast
        col_date1, col_date2 = st.sidebar.columns(2)
        
        with col_date1:
            start_date = st.sidebar.date_input(
                "Start Date",
                value=datetime.now().date(),
                help="Forecast start date"
            )
        
        with col_date2:
            end_date = st.sidebar.date_input(
                "End Date",
                value=datetime.now().date() + timedelta(days=365),
                help="Forecast end date"
            )
        
        frequency = st.sidebar.selectbox(
            "Forecast Frequency",
            options=['daily', 'weekly', 'biweekly', 'monthly'],
            help="Frequency of forecast points"
        )
        
        # Forecast button
        forecast_button = st.sidebar.button(
            "📈 Generate Forecast",
            type="primary",
            width='stretch'
        )
    
    # Main content area
    if prediction_type == 'Single Date' and predict_button:
        # Check for validation errors first
        if errors:
            st.error("❌ Please fix the input errors before making a prediction:")
            for error in errors:
                st.error(f"• {error}")
        else:
            try:
                with st.spinner("Generating price prediction..."):
                    result = predictor.predict_property_price(
                        location=location,
                        total_sqft=total_sqft,
                        bhk=bhk,
                        bath=bath,
                        prediction_date=prediction_date
                    )
                
                # Display prediction result
                st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                st.markdown('<h2>🎯 Price Prediction Result</h2>', unsafe_allow_html=True)
                
                col_price1, col_price2 = st.columns(2)
                
                with col_price1:
                    st.metric(
                        "Predicted Price",
                        f"₹{result['predicted_price']:,.0f}",
                        help="Predicted price for the specified date"
                    )
                
                with col_price2:
                    st.metric(
                        "Base Price",
                        f"₹{result['base_price']:,.0f}",
                        f"Trend: {result['trend_factor']:.2f}x",
                        help="Base price before adjustments"
                    )
                
                # Additional information
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.info(f"**Location:** {location}")
                
                with col_info2:
                    st.info(f"**Date:** {result['date'].strftime('%Y-%m-%d')}")
                
                with col_info3:
                    st.info(f"**Price per Sqft:** ₹{result['predicted_price']/total_sqft:,.0f}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show historical data for the location
                st.markdown("## 📊 Historical Data")
                location_data = predictor.training_data[predictor.training_data['location'] == location]
                
                # Create time series chart
                fig = create_time_series_chart(location_data, total_sqft=total_sqft)
                st.plotly_chart(fig, width='stretch')
                
                # Success message
                st.markdown(
                    '<div class="success-message">✅ Price prediction completed successfully!</div>',
                    unsafe_allow_html=True
                )
                
            except Exception as e:
                st.error(f"Error making prediction: {e}")
    
    elif prediction_type == 'Date Range Forecast' and forecast_button:
        # Check for validation errors first
        if errors:
            st.error("❌ Please fix the input errors before making a forecast:")
            for error in errors:
                st.error(f"• {error}")
        else:
            try:
                with st.spinner("Generating price forecast..."):
                    forecasts = predictor.forecast_price_trend(
                        location=location,
                        total_sqft=total_sqft,
                        bhk=bhk,
                        bath=bath,
                        start_date=start_date,
                        end_date=end_date,
                        frequency=frequency
                    )
                
                # Display forecast results
                st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                st.markdown('<h2>📈 Price Forecast Results</h2>', unsafe_allow_html=True)
                
                # Summary metrics
                forecast_df = pd.DataFrame(forecasts)
                
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                
                with col_sum1:
                    st.metric(
                        "Starting Price",
                        f"₹{forecast_df['predicted_price'].iloc[0]:,.0f}",
                        help="Predicted price at start date"
                    )
                
                with col_sum2:
                    st.metric(
                        "Ending Price",
                        f"₹{forecast_df['predicted_price'].iloc[-1]:,.0f}",
                        f"{((forecast_df['predicted_price'].iloc[-1] / forecast_df['predicted_price'].iloc[0]) - 1) * 100:+.1f}%",
                        help="Predicted price at end date"
                    )
                
                with col_sum3:
                    avg_price = forecast_df['predicted_price'].mean()
                    st.metric(
                        "Average Price",
                        f"₹{avg_price:,.0f}",
                        help="Average predicted price over the period"
                    )
                
                with col_sum4:
                    price_change = forecast_df['predicted_price'].iloc[-1] - forecast_df['predicted_price'].iloc[0]
                    st.metric(
                        "Total Change",
                        f"₹{price_change:,.0f}",
                        f"{(price_change/forecast_df['predicted_price'].iloc[0]) * 100:+.1f}%",
                        help="Total price change over period"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Create forecast chart
                location_data = predictor.training_data[predictor.training_data['location'] == location]
                fig = create_time_series_chart(location_data, forecasts, total_sqft=total_sqft)
                st.plotly_chart(fig, width='stretch')
                
                # Detailed forecast table
                st.markdown("### 📋 Detailed Forecast")
                display_df = forecast_df.copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                display_df['predicted_price'] = display_df['predicted_price'].map('₹{:,.0f}'.format)
                display_df['base_price'] = display_df['base_price'].map('₹{:,.0f}'.format)
                display_df['trend_factor'] = display_df['trend_factor'].map('{:.3f}'.format)
                
                st.dataframe(
                    display_df[['date', 'predicted_price', 'base_price', 'trend_factor']],
                    width='stretch',
                    height=300
                )
                
                # Success message
                st.markdown(
                    '<div class="success-message">✅ Price forecast completed successfully!</div>',
                    unsafe_allow_html=True
                )
                
                # Show seasonal analysis only when generating trends
                st.markdown("---")
                st.markdown("### 📈 Seasonal Analysis")
                fig_seasonal = create_seasonal_decomposition_chart(predictor.training_data)
                if fig_seasonal:
                    st.plotly_chart(fig_seasonal, width='stretch')
                else:
                    st.info("Insufficient data for seasonal analysis")
                
            except Exception as e:
                st.error(f"Error generating forecast: {e}")
    
    # Analysis section
    st.markdown("---")
    st.markdown("## 📊 Data Analysis")
    
    # Model performance
    display_model_performance(performance)
    
    # Historical analysis
    st.markdown("### 📍 Location Comparison")
    fig_location = create_location_comparison_chart(predictor.training_data)
    st.plotly_chart(fig_location, width='stretch')
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🏠 Hyderabad House Price Predictor - Time Series | Powered by Advanced ML | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
