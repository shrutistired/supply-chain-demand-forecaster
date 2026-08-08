from flask import Flask, render_template, request
from sqlalchemy import create_engine
import pandas as pd
import joblib
from datetime import datetime
import urllib.parse  # <--- CRUCIAL: Added to prevent NameError

app = Flask(__name__)
model = joblib.load('demand_model.pkl')

# Safely encode the password for Flask
safe_password = urllib.parse.quote_plus("shruti@123")
DB_URL = f"postgresql://postgres:{safe_password}@localhost:5433/supply_demand_chain"
engine = create_engine(DB_URL)

@app.route('/')
def home():
    return render_template('index.html')
'''   
@app.route('/predict', methods=['POST'])
def predict():
    # 1. GET USER INPUTS
    store_nbr = int(request.form.get('store_nbr'))
    family = request.form.get('family')
    onpromotion = int(request.form.get('onpromotion'))
    
    # 2. QUERY POSTGRES (Join sales history with store details)
    query = f"""
        SELECT h.date, h.sales, s.city, s.state, s.type as store_type, s.cluster
        FROM sales_history h
        JOIN stores s ON h.store_nbr = s.store_nbr
        WHERE h.store_nbr = {store_nbr} AND h.family = '{family}'
        ORDER BY h.date DESC 
        LIMIT 30;
    """
    history_df = pd.read_sql(query, engine)
    
    # 3. PROCESS THE DATA
    if history_df.empty:
        # Failsafe: If no history exists, default to 0s and generic store info
        lag_1, lag_7, lag_14 = 0, 0, 0
        roll_7, roll_14, roll_30 = 0, 0, 0
        city, state, store_type, cluster = 'Unknown', 'Unknown', 'D', 13
    else:
        sales_data = history_df['sales'].values
        
        # Calculate Lags
        lag_1 = sales_data[0] if len(sales_data) > 0 else 0
        lag_7 = sales_data[6] if len(sales_data) > 6 else 0
        lag_14 = sales_data[13] if len(sales_data) > 13 else 0
        
        # Calculate Rolling Averages
        roll_7 = sales_data[:7].mean() if len(sales_data) >= 7 else 0
        roll_14 = sales_data[:14].mean() if len(sales_data) >= 14 else 0
        roll_30 = sales_data.mean()
        
        # Extract Store Info (from the very first row)
        city = history_df['city'].iloc[0]
        state = history_df['state'].iloc[0]
        store_type = history_df['store_type'].iloc[0]
        cluster = history_df['cluster'].iloc[0]

    # 4. BUILD THE DYNAMIC FEATURE VECTOR
    today = datetime.now()
    
    input_data = pd.DataFrame([{
        'store_nbr': store_nbr,
        'family': family,
        'onpromotion': onpromotion,
        'city': city,              # Now dynamic!
        'state': state,            # Now dynamic!
        'store_type': store_type,  # Now dynamic!
        'cluster': cluster,        # Now dynamic!
        'dcoilwtico': 50.0,        
        'holiday_type': 'No Holiday',
        'locale': 'None',          
        'locale_name': 'None',     
        'transferred': 0,          
        'year': today.year,
        'month': today.month,
        'day': today.day,          
        'day_of_week': today.weekday(),
        'is_weekend': 1 if today.weekday() >= 5 else 0,
        'family_day': f"{family}_{today.weekday()}",
        'weekofyear': today.isocalendar()[1],
        'quarter': (today.month - 1) // 3 + 1,
        'is_holiday': 0,
        'rolling_7d_sales': roll_7,   
        'rolling_14d_sales': roll_14,
        'rolling_30d_sales': roll_30,
        'lag_1': lag_1,
        'lag_7': lag_7,
        'lag_14': lag_14
    }])
    
    # 5. PREDICT AND RENDER
    prediction = model.predict(input_data)[0]
    prediction = max(0, round(prediction))
    
    safety_stock = prediction * 0.2
    if prediction > 500:
        alert = f"🔴 High demand predicted. Order {prediction + int(safety_stock)} units immediately."
    elif prediction > 100:
        alert = f"🟡 Moderate demand. Recommended order: {prediction + int(safety_stock)} units."
    else:
        alert = f"🟢 Low demand expected. Standard reorder of {prediction} units sufficient."
    
    return render_template('result.html',
                           prediction=prediction,
                           alert=alert,
                           store=store_nbr,
                           family=family)
'''
@app.route('/predict', methods=['POST'])
def predict():
    store_nbr = int(request.form.get('store_nbr'))
    family = request.form.get('family')
    onpromotion = int(request.form.get('onpromotion'))
    
    # FETCHING 46 DAYS OF HISTORY
    query = f"""
        SELECT h.date, h.sales, s.city, s.state, s.type as store_type, s.cluster
        FROM sales_history h
        JOIN stores s ON h.store_nbr = s.store_nbr
        WHERE h.store_nbr = {store_nbr} AND h.family = '{family}'
        ORDER BY h.date DESC 
        LIMIT 46;
    """
    history_df = pd.read_sql(query, engine)
    
    if history_df.empty:
        lag_16, lag_21, lag_30 = 0, 0, 0
        roll_7, roll_14, roll_30 = 0, 0, 0
        city, state, store_type, cluster = 'Unknown', 'Unknown', 'D', 13
    else:
        sales_data = history_df['sales'].values
        
        # In DESC order, index 15 represents 16 days ago
        lag_16 = sales_data[15] if len(sales_data) > 15 else 0
        lag_21 = sales_data[20] if len(sales_data) > 20 else 0
        lag_30 = sales_data[29] if len(sales_data) > 29 else 0
        
        # Shifting the array by 16 days for rolling calculations
        shifted_sales = sales_data[15:] if len(sales_data) > 15 else []
        roll_7 = shifted_sales[:7].mean() if len(shifted_sales) >= 7 else 0
        roll_14 = shifted_sales[:14].mean() if len(shifted_sales) >= 14 else 0
        roll_30 = shifted_sales[:30].mean() if len(shifted_sales) > 0 else 0
        
        city = history_df['city'].iloc[0]
        state = history_df['state'].iloc[0]
        store_type = history_df['store_type'].iloc[0]
        cluster = history_df['cluster'].iloc[0]

    today = datetime.now()
    
    # MAKING SURE KEYS MATCH THE NEW FEATURE NAMES
    input_data = pd.DataFrame([{
        'store_nbr': store_nbr,
        'family': family,
        'onpromotion': onpromotion,
        'city': city,
        'state': state,
        'store_type': store_type,
        'cluster': cluster,
        'dcoilwtico': 50.0,        
        'holiday_type': 'No Holiday',
        'locale': 'None',          
        'locale_name': 'None',     
        'transferred': 0,          
        'year': today.year,
        'month': today.month,
        'day': today.day,          
        'day_of_week': today.weekday(),
        'is_weekend': 1 if today.weekday() >= 5 else 0,
        'family_day': f"{family}_{today.weekday()}",
        'weekofyear': today.isocalendar()[1],
        'quarter': (today.month - 1) // 3 + 1,
        'is_holiday': 0,
        'rolling_7d_sales': roll_7,   
        'rolling_14d_sales': roll_14,
        'rolling_30d_sales': roll_30,
        'lag_16': lag_16,
        'lag_21': lag_21,
        'lag_30': lag_30
    }])
    
    prediction = model.predict(input_data)[0]
    prediction = max(0, round(prediction))

    # ALERT LOGIC
    safety_stock = prediction * 0.2
    if prediction > 500:
        alert = f"🔴 High demand predicted. Order {prediction + int(safety_stock)} units immediately."
    elif prediction > 100:
        alert = f"🟡 Moderate demand. Recommended order: {prediction + int(safety_stock)} units."
    else:
        alert = f"🟢 Low demand expected. Standard reorder of {prediction} units sufficient."
    
    return render_template('result.html',
                           prediction=prediction,
                           alert=alert,
                           store=store_nbr,
                           family=family)
if __name__ == '__main__':
    app.run(debug=True)