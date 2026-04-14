import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import MinMaxScaler
import database as db

# Initialize
db.init_db()

st.set_page_config(page_title="Sales Forecaster", layout="wide")
st.title("📊 Enterprise Sales Forecaster")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📥 Data Ingestion", "📈 Forecast Engine", "⚠️ Error Logs", "🗄️ Database View"])

# --- TAB 1: DATA INGESTION ---
with tab1:
    # SECTION 1: BULK UPLOAD
    st.subheader("1. Universal Bulk Data Upload (Up to 1GB)")
    uploaded_file = st.file_uploader("Upload ANY file (CSV, Excel, TXT)", type=['csv', 'xlsx', 'txt'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df_raw = pd.read_excel(uploaded_file)
            else:
                df_raw = pd.read_csv(uploaded_file, sep=None, engine='python')

            # SMART SCANNER LOGIC
            date_col, amt_col = None, None
            
            # Find Date Column by trying to parse first few rows
            for col in df_raw.columns:
                try:
                    pd.to_datetime(df_raw[col].iloc[:3], errors='raise')
                    date_col = col
                    break
                except: continue
            
            # Find Amount Column (The first column that is numeric)
            num_cols = df_raw.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols: amt_col = num_cols[0]

            if date_col and amt_col:
                st.info(f"Auto-Detected: Dates in '{date_col}', Sales in '{amt_col}'")
                clean_df = pd.DataFrame({
                    'date': pd.to_datetime(df_raw[date_col]).dt.strftime('%Y-%m-%d'),
                    'amount': pd.to_numeric(df_raw[amt_col])
                }).dropna()
                db.insert_bulk_data(clean_df)
                st.success(f"Successfully uploaded {len(clean_df)} records!")
            else:
                st.error("Structure not recognized. Please ensure your file has a column for dates and a column for numbers.")
        except Exception as e:
            st.error(f"Critical System Error: {str(e)}")

    # VISUAL DIVIDER
    st.markdown("<br><hr style='border:2px solid #00BFFF'><br>", unsafe_allow_html=True)

    # SECTION 2: DAILY UPDATE (Always Visible)
    st.subheader("2. Daily Sales Update")
    st.write("Manually update today's sales or add a future entry for prediction context.")
    
    c1, c2 = st.columns(2)
    with c1:
        new_date = st.date_input("Entry Date", value=datetime.now())
    with c2:
        new_amount = st.text_input("Sales Amount (Negative for Loss)")
    
    if st.button("Update Daily Sales"):
        curr_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            val = float(new_amount)
            db.insert_sales_data(str(new_date), val)
            st.success(f"Recorded ${val} for {new_date}")
        except ValueError:
            db.log_error(curr_ts, str(new_date), str(new_amount), "Manual Input Error")
            st.error("Invalid amount. Please enter a number.")

# --- TAB 2: FORECAST ENGINE ---
with tab2:
    st.subheader("Predictive Analysis (CART Algorithm)")
    tf = st.selectbox("Forecast Timeframe", ["Daily", "Weekly", "Yearly"])
    steps = st.slider("Steps to predict", 1, 30, 7)
    
    data = db.get_aggregated_sales(tf)
    
    if len(data) < 5:
        st.warning("Insufficient data. Please upload or enter at least 5 historical entries.")
    else:
        # Normalization
        scaler = MinMaxScaler()
        data['norm'] = scaler.fit_transform(data[['amount']])
        
        # CART Model
        X = np.arange(len(data)).reshape(-1, 1)
        y = data['norm'].values
        model = DecisionTreeRegressor(max_depth=5)
        model.fit(X, y)
        
        # Prediction
        future_X = np.arange(len(data), len(data) + steps).reshape(-1, 1)
        pred_norm = model.predict(future_X)
        pred_actual = scaler.inverse_transform(pred_norm.reshape(-1, 1)).flatten()
        
        # Profit/Loss Calculation
        total_proj = np.sum(pred_actual)
        if total_proj >= 0:
            st.success(f"Projected Net Profit: ${total_proj:,.2f}")
        else:
            st.error(f"Projected Net Loss: ${total_proj:,.2f}")

        # High-Contrast Plotting
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#001220')
        ax.set_facecolor('#001220')
        ax.plot(range(len(data)), data['amount'], color='#00BFFF', label='History', marker='o')
        ax.plot(range(len(data), len(data)+steps), pred_actual, color='#FF4B4B', label='Forecast', linestyle='--', marker='x')
        ax.tick_params(colors='white')
        ax.set_title("Sales Sequence Analysis", color='white')
        ax.legend()
        st.pyplot(fig)

# --- TAB 3 & 4 (Error Logs and DB View) ---
with tab3:
    st.dataframe(db.get_error_logs(), use_container_width=True)
with tab4:
    st.dataframe(db.get_aggregated_sales('Daily'), use_container_width=True)