import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import MinMaxScaler
import database as db

# Initialize the Database
db.init_db()

st.title("📊 Enterprise Sales Forecaster")
st.markdown("Database Management System Project utilizing SQL, CART algorithm, and Data Normalization.")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["Input Daily Data", "Forecast Engine", "Error Logs", "Database View"])

# --- TAB 1: INPUT DATA ---
# --- TAB 1: INPUT DATA ---
with tab1:
    st.subheader("1. Bulk Data Upload")
    uploaded_file = st.file_uploader("Upload your historical dataset (.csv or .txt)", type=['csv', 'txt'])
    
    if uploaded_file is not None:
        try:
            # Assuming CSV format with 'date' and 'amount' columns
            bulk_df = pd.read_csv(uploaded_file)
            if 'date' in bulk_df.columns and 'amount' in bulk_df.columns:
                db.insert_bulk_data(bulk_df)
                st.success(f"Successfully imported {len(bulk_df)} records!")
            else:
                st.error("Invalid File Format: Ensure columns are named 'date' and 'amount'.")
        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.markdown("---")
    st.subheader("2. Daily Update")
    st.write("Enter individual daily data entries below.")
    # (Keep your existing daily input logic here...)
    col1, col2 = st.columns(2)

    with col1:
        date_input = st.date_input("Date")
    with col2:
        amount_input = st.text_input("Amount")
    if st.button("Submit Daily Entry"):
        # (Keep your existing insert_sales_data logic here...)


# --- TAB 2: FORECAST ENGINE (CART Algorithm) ---
with tab2:
    st.subheader("Sales Forecasting Analysis")
    timeframe = st.selectbox("Select SQL Aggregation Level", ["Daily", "Weekly", "Yearly"])
    forecast_steps = st.slider("Periods to Forecast Ahead", min_value=1, max_value=30, value=7)
    
    df = db.get_aggregated_sales(timeframe)
    
    if len(df) < 5:
        st.info("Please enter at least 5 days of data in the 'Input Daily Data' tab to generate a CART forecast.")
    else:
        st.write("### Historical Data (SQL Query Result)")
        st.dataframe(df, use_container_width=True)
        
        # Data Preparation & Normalization
        scaler = MinMaxScaler()
        # Normalizing the amount for best CART results
        df['Normalized_Amount'] = scaler.fit_transform(df[['amount']])
        
        # Feature Engineering for CART (Creating sequence index)
        df['Time_Index'] = np.arange(len(df))
        X = df[['Time_Index']]
        y = df['Normalized_Amount']
        
        # CART Algorithm (Decision Tree Regressor) to find patterns
        cart_model = DecisionTreeRegressor(max_depth=5, random_state=42)
        cart_model.fit(X, y)
        
        # Forecasting Future Sequences
        future_indices = np.arange(len(df), len(df) + forecast_steps).reshape(-1, 1)
        future_normalized_pred = cart_model.predict(future_indices)
        
        # Inverse transform to get actual currency values back
        future_pred_actual = scaler.inverse_transform(future_normalized_pred.reshape(-1, 1)).flatten()
        
        # Calculate Projected Profit/Loss
        total_forecast = np.sum(future_pred_actual)
        st.write(f"### 📈 Projected Total for next {forecast_steps} {timeframe.lower()}s: **${total_forecast:.2f}**")
        if total_forecast < 0:
            st.error("Forecast indicates an approximate NET LOSS.")
        else:
            st.success("Forecast indicates an approximate NET PROFIT.")
        
        # Graphing
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#001220') # Matches dark theme
        ax.set_facecolor('#001220')
        
        ax.plot(df['Time_Index'], df['amount'], label='Historical Sales (SQL)', color='#00BFFF', marker='o')
        ax.plot(future_indices, future_pred_actual, label='CART Forecast', color='#FF4B4B', linestyle='--', marker='x')
        
        ax.set_title(f"CART Algorithm Sales Forecast ({timeframe})", color='white')
        ax.set_xlabel("Time Sequence", color='white')
        ax.set_ylabel("Amount ($)", color='white')
        ax.tick_params(colors='white')
        ax.legend(facecolor='#002B4A', edgecolor='white', labelcolor='white')
        
        st.pyplot(fig)

# --- TAB 3: ERROR LOGS ---
with tab3:
    st.subheader("Data Cleaning & Error Logs")
    st.write("This section tracks missing values and incorrect data types rejected by the system.")
    error_df = db.get_error_logs()
    if error_df.empty:
        st.success("No database errors logged.")
    else:
        st.dataframe(error_df, use_container_width=True)

# --- TAB 4: RAW DATABASE VIEW ---
with tab4:
    st.subheader("Raw SQL Data View")
    st.write("Direct pull from `sales_data` table.")
    raw_df = db.get_aggregated_sales('Daily')
    st.dataframe(raw_df, use_container_width=True)