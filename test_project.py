"""
Test script to verify the Hyderabad House Price Prediction project is working
"""

from datetime import datetime
from home_price_time_series import HyderabadTimeSeriesPredictor, load_hyd_time_series_data

def test_project():
    """Test the project functionality"""
    try:
        print("=== Testing Hyderabad House Price Prediction Project ===")
        
        # Test data loading
        print("1. Testing data loading...")
        csv_path = load_hyd_time_series_data()
        print(f"   Data loaded from: {csv_path}")
        
        # Test predictor initialization
        print("2. Testing predictor initialization...")
        predictor = HyderabadTimeSeriesPredictor()
        print("   Predictor initialized successfully")
        
        # Test model training
        print("3. Testing model training...")
        performance = predictor.load_and_train(csv_path)
        print(f"   Model training completed: {len(performance)} models trained")
        
        # Test prediction
        print("4. Testing prediction...")
        prediction = predictor.predict_property_price(
            location='Jubilee Hills',
            total_sqft=1200,
            bhk=2,
            bath=2,
            prediction_date=datetime(2024, 12, 31)
        )
        print(f"   Prediction successful: ₹{prediction['predicted_price']:,.0f}")
        
        # Test forecast
        print("5. Testing forecast...")
        forecasts = predictor.forecast_price_trend(
            location='Jubilee Hills',
            total_sqft=1200,
            bhk=2,
            bath=2,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            frequency='quarterly'
        )
        print(f"   Forecast successful: {len(forecasts)} quarters predicted")
        
        print("\n✅ All tests passed! Project is working correctly.")
        print("🚀 Ready to run the Streamlit GUI!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_project()
    if success:
        print("\n🎯 Next step: Run 'streamlit run home_price_gui_time_series.py' to start the GUI")
    else:
        print("\n🔧 Please fix the errors before running the GUI")
