# Hyderabad House Price Prediction System - UML Architecture

## System Overview

The Hyderabad House Price Prediction System is a comprehensive time-series forecasting application that predicts property prices using machine learning models with temporal and spatial features.

## 1. High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        GUI[Streamlit GUI]
        CLI[Command Line Interface]
    end
    
    subgraph "Business Logic Layer"
        TS[HyderabadTimeSeriesPredictor]
        FT[TimeSeriesForecaster]
        MT[ModelTrainer]
        DP[DataProcessor]
    end
    
    subgraph "Data Layer"
        CSV[CSV Data Files]
        CACHE[Streamlit Cache]
    end
    
    subgraph "Machine Learning Layer"
        LR[Linear Regression]
        RF[Random Forest]
        GB[Gradient Boosting]
    end
    
    GUI --> TS
    CLI --> TS
    TS --> FT
    TS --> MT
    TS --> DP
    DP --> CSV
    MT --> LR
    MT --> RF
    MT --> GB
    GUI --> CACHE
```

## 2. Class Architecture Diagram

```mermaid
classDiagram
    class HyderabadTimeSeriesPredictor {
        -data_processor: TimeSeriesDataProcessor
        -model_trainer: TimeSeriesModelTrainer
        -forecaster: TimeSeriesForecaster
        -training_data: DataFrame
        -is_trained: boolean
        +__init__()
        +load_and_train(csv_path: str): dict
        +predict_property_price(location, sqft, bhk, bath, date): dict
        +forecast_price_trend(location, sqft, bhk, bath, start_date, end_date, frequency): list
    }
    
    class TimeSeriesDataProcessor {
        -feature_columns: list
        -categorical_columns: list
        +__init__()
        +preprocess_time_series_data(data: DataFrame): DataFrame
        +create_date_features(data: DataFrame): DataFrame
        +create_lag_features(data: DataFrame): DataFrame
        +create_rolling_features(data: DataFrame): DataFrame
        +encode_categorical_features(data: DataFrame): DataFrame
    }
    
    class TimeSeriesModelTrainer {
        -models: dict
        -model_performance: dict
        -best_model: object
        -best_model_name: str
        +__init__()
        +train_time_series_split(X, y): dict
        +train_single_model(name, model, X_train, y_train, X_test, y_test): dict
        +predict(X): array
    }
    
    class TimeSeriesForecaster {
        -model_trainer: TimeSeriesModelTrainer
        -data_processor: TimeSeriesDataProcessor
        -best_model: object
        -best_model_name: str
        +__init__(model_trainer, data_processor)
        +forecast_future_prices(base_data, future_dates, location, property_features): list
        +predict(X): array
    }
    
    HyderabadTimeSeriesPredictor --> TimeSeriesDataProcessor
    HyderabadTimeSeriesPredictor --> TimeSeriesModelTrainer
    HyderabadTimeSeriesPredictor --> TimeSeriesForecaster
    TimeSeriesForecaster --> TimeSeriesModelTrainer
    TimeSeriesForecaster --> TimeSeriesDataProcessor
```

## 3. Data Flow Architecture

```mermaid
flowchart TD
    A[User Input] --> B{Input Type}
    B -->|Single Date Prediction| C[Property Features]
    B -->|Date Range Forecast| D[Date Range]
    
    C --> E[Data Loading]
    D --> E
    
    E --> F[Time Series Preprocessing]
    F --> G[Feature Engineering]
    G --> H[Model Training]
    H --> I[Best Model Selection]
    I --> J[Prediction/Forecasting]
    J --> K[Property Feature Adjustments]
    K --> L[Price Output]
    
    subgraph "Feature Engineering Details"
        G1[Date Features]
        G2[Lag Features]
        G3[Rolling Features]
        G4[Location Features]
        G5[Cyclical Features]
    end
    
    G --> G1
    G --> G2
    G --> G3
    G --> G4
    G --> G5
```

## 4. Component Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant GUI as Streamlit GUI
    participant Predictor as HyderabadTimeSeriesPredictor
    participant Processor as DataProcessor
    participant Trainer as ModelTrainer
    participant Forecaster as Forecaster
    
    User->>GUI: Select Location & Properties
    User->>GUI: Choose Date(s)
    User->>GUI: Click Predict
    
    GUI->>Predictor: predict_property_price()
    
    Predictor->>Processor: preprocess_time_series_data()
    Processor-->>Predictor: Processed Data
    
    Predictor->>Trainer: train_time_series_split()
    Trainer->>Trainer: train_single_model() for each model
    Trainer-->>Predictor: Best Model
    
    Predictor->>Forecaster: forecast_future_prices()
    Forecaster->>Forecaster: Apply Property Adjustments
    Forecaster-->>Predictor: Adjusted Predictions
    
    Predictor-->>GUI: Price Results
    GUI-->>User: Display Predictions
```

## 5. Data Model Architecture

```mermaid
erDiagram
    Property {
        date datetime PK
        location string
        total_sqft int
        bhk int
        bath int
        price float
        year int
        month int
        quarter int
        day_of_year int
        week_of_year int
        month_sin float
        month_cos float
        quarter_sin float
        quarter_cos float
        days_since_start int
        is_quarter_end boolean
        is_year_end boolean
        price_lag_1 float
        price_change_lag_1 float
        price_rolling_mean_3 float
        price_rolling_std_3 float
        price_rolling_min_3 float
        price_rolling_max_3 float
        price_rolling_trend_3 float
        location_price_mean float
        location_price_median float
        location_price_std float
        price_per_sqft float
        bhk_per_sqft float
        bath_per_sqft float
        bhk_to_bath_ratio float
        location_price_level string
    }
    
    Location {
        name string PK
        price_level string
        avg_price float
        price_variance float
    }
    
    Property ||--o{ Location
```

## 6. Model Architecture

```mermaid
graph LR
    subgraph "Input Features"
        F1[Temporal Features]
        F2[Location Features]
        F3[Property Features]
        F4[Engineered Features]
    end
    
    subgraph "Model Ensemble"
        M1[Linear Regression]
        M2[Random Forest]
        M3[Gradient Boosting]
    end
    
    subgraph "Model Selection"
        S1[Cross-Validation]
        S2[Performance Metrics]
        S3[Best Model Selection]
    end
    
    subgraph "Output Processing"
        O1[Base Prediction]
        O2[Property Adjustments]
        O3[Trend/Seasonal Adjustments]
        O4[Final Price]
    end
    
    F1 --> M1
    F1 --> M2
    F1 --> M3
    F2 --> M1
    F2 --> M2
    F2 --> M3
    F3 --> M1
    F3 --> M2
    F3 --> M3
    F4 --> M1
    F4 --> M2
    F4 --> M3
    
    M1 --> S1
    M2 --> S1
    M3 --> S1
    S1 --> S2
    S2 --> S3
    
    S3 --> O1
    O1 --> O2
    O2 --> O3
    O3 --> O4
```

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Local Development]
        TEST[Testing Scripts]
        DATA[Training Data]
    end
    
    subgraph "Production Environment"
        WEB[Streamlit Web App]
        API[REST API Optional]
        DOCKER[Docker Container]
    end
    
    subgraph "Infrastructure"
        CACHE[Redis Cache]
        LOGS[Logging System]
        MONITOR[Monitoring]
    end
    
    DEV --> WEB
    TEST --> WEB
    DATA --> WEB
    
    WEB --> DOCKER
    API --> DOCKER
    
    DOCKER --> CACHE
    DOCKER --> LOGS
    DOCKER --> MONITOR
```

## 8. Feature Engineering Pipeline

```mermaid
flowchart TD
    A[Raw CSV Data] --> B[Data Validation]
    B --> C[Date Feature Extraction]
    C --> D[Lag Feature Creation]
    D --> E[Rolling Statistics]
    E --> F[Location Encoding]
    F --> G[Cyclical Encoding]
    G --> H[Property Ratios]
    H --> I[Feature Selection]
    I --> J[Final Feature Matrix]
    
    subgraph "Date Features"
        C1[Year, Month, Quarter]
        C2[Day of Year, Week]
        C3[Quarter/Year End Flags]
    end
    
    subgraph "Lag Features"
        D1[Price Lag 1]
        D2[Price Change Lag 1]
    end
    
    subgraph "Rolling Features"
        E1[Rolling Mean 3]
        E2[Rolling Std 3]
        E3[Rolling Min/Max 3]
        E4[Rolling Trend 3]
    end
    
    subgraph "Location Features"
        F1[Location Price Stats]
        F2[Location Price Level]
    end
    
    subgraph "Property Features"
        H1[Price per Sqft]
        H2[BHK per Sqft]
        H3[Bath per Sqft]
        H4[BHK to Bath Ratio]
    end
    
    C --> C1
    C --> C2
    C --> C3
    D --> D1
    D --> D2
    E --> E1
    E --> E2
    E --> E3
    E --> E4
    F --> F1
    F --> F2
    H --> H1
    H --> H2
    H --> H3
    H --> H4
```

## 9. File Structure Architecture

```mermaid
graph TD
    ROOT[Project Root]
    
    ROOT --> CORE[Core Logic]
    ROOT --> DATA[Data Files]
    ROOT --> GUI[GUI Files]
    ROOT --> TESTS[Test Scripts]
    ROOT --> DOCS[Documentation]
    
    CORE --> TS[home_price_time_series.py]
    CORE --> UTILS[Utility Functions]
    
    DATA --> HYD[hyd.csv]
    DATA --> TEMPLATES[Template Files]
    TEMPLATES --> ALL[hyd_all_locations_template.csv]
    TEMPLATES --> REAL[hyd_realistic_template.csv]
    TEMPLATES --> EXPANDED[hyd_expanded_bhk_dataset.csv]
    
    GUI --> MAIN[home_price_gui_time_series_fixed.py]
    GUI --> CSS[Styling Components]
    
    TESTS --> FUTURE[test_future_dates.py]
    TESTS --> BHK[test_bhk_differences.py]
    TESTS --> DEBUG[debug_features.py]
    
    DOCS --> UML[UML_ARCHITECTURE.md]
    DOCS --> GUIDES[Integration Guides]
```

## 10. Technology Stack Architecture

```mermaid
graph TB
    subgraph "Frontend"
        STREAMLIT[Streamlit]
        HTML[HTML/CSS]
        PLOTLY[Plotly Charts]
    end
    
    subgraph "Backend"
        PYTHON[Python 3.8+]
        PANDAS[pandas]
        NUMPY[NumPy]
        SCIKIT[scikit-learn]
    end
    
    subgraph "Data Processing"
        ML[Machine Learning]
        TS[Time Series Analysis]
        FE[Feature Engineering]
    end
    
    subgraph "Deployment"
        DOCKER[Docker]
        GITHUB[Git/GitHub]
        CLOUD[Cloud Platform]
    end
    
    STREAMLIT --> PYTHON
    HTML --> STREAMLIT
    PLOTLY --> STREAMLIT
    
    PYTHON --> PANDAS
    PYTHON --> NUMPY
    PYTHON --> SCIKIT
    
    PANDAS --> ML
    NUMPY --> TS
    SCIKIT --> FE
    
    DOCKER --> CLOUD
    GITHUB --> CLOUD
```

## Key Architectural Principles

1. **Separation of Concerns**: Clear separation between data processing, model training, and prediction logic
2. **Modularity**: Each component can be tested and developed independently
3. **Scalability**: Architecture supports adding new models, features, and data sources
4. **Maintainability**: Well-structured codebase with clear interfaces
5. **Performance**: Efficient caching and optimized data processing pipelines
6. **Extensibility**: Easy to add new locations, features, and prediction types

## Design Patterns Used

1. **Strategy Pattern**: Multiple model training strategies
2. **Factory Pattern**: Model creation and selection
3. **Observer Pattern**: GUI updates based on model changes
4. **Template Method**: Standardized prediction workflow
5. **Decorator Pattern**: Caching and logging functionality
