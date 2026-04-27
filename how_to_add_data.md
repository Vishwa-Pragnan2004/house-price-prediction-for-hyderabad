# How to Add Your Real Housing Data

## Step 1: Prepare Your CSV File
Create a CSV file with the following columns:
- `location`: Property location (string)
- `total_sqft`: Total square footage (number)
- `bhk`: Number of bedrooms (number)
- `bath`: Number of bathrooms (number)
- `price`: Actual price (number)

## Step 2: Replace the Sample Data
Replace the content of `data/real_housing_data.csv` with your data:

```csv
location,total_sqft,bhk,bath,price
Your_Location1,1200,2,2,280000
Your_Location2,1500,3,2,350000
Your_Location3,1800,3,3,420000
```

## Step 3: Run the System
The system will automatically:
1. Load your real data from `data/real_housing_data.csv`
2. Detect data changes and retrain if needed
3. Cache the model for future use
4. Provide predictions based on your real patterns

## Step 4: Minimum Data Requirements
- **Minimum rows**: 10-15 properties for basic training
- **Recommended rows**: 100+ properties for better accuracy
- **Required columns**: All 5 columns must be present
- **Data quality**: Remove extreme outliers and invalid entries

## Step 5: Test Your Data
Run this to test your data loading:
```bash
python load_real_data.py
```

## Notes:
- The system automatically falls back to synthetic data if your file is missing
- More diverse locations and property types improve model performance
- Consistent data formatting is important for best results
