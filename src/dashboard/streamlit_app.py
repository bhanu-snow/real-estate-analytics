import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import Error
import plotly.express as px
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL connection
try:
    conn = psycopg2.connect(
        user="user",
        password="password",
        host="localhost",
        port="5432",
        database="property_db"
    )
except Error as e:
    st.error(f"Error connecting to PostgreSQL: {e}")
    logger.error(f"PostgreSQL connection error: {e}")
    st.stop()

# Load data from ai_results
query = "SELECT property_id, price, predicted_price, size_sqm, location, project, cluster_label, timestamp FROM ai_results"
try:
    df = pd.read_sql(query, conn)
    logger.info(f"Loaded {len(df)} records from ai_results")
except Error as e:
    st.error(f"Error querying ai_results: {e}")
    logger.error(f"Query error: {e}")
    conn.close()
    st.stop()
conn.close()

# Calculate Investment Score
def calculate_investment_score(df):
    # Location weights (Vision 2030 demand)
    location_weights = {'UAE': 1.0, 'Jeddah': 0.8, 'Dammam': 0.6}  # Add more as needed
    df['location_weight'] = df['location'].map(location_weights).fillna(0.5)

    # Appreciation Score
    df['appreciation_score'] = ((df['predicted_price'] - df['price']) / df['price'] * 100).clip(0, 50)
    df['appreciation_score'] += df['cluster_label'].apply(lambda x: 10 if x == 'High-Value' else 0)

    # Rental Score
    max_price_per_sqm = df['price'].max() / df['size_sqm'].min()  # Approx benchmark
    df['price_per_sqm'] = df['price'] / df['size_sqm']
    df['rental_score'] = ((max_price_per_sqm - df['price_per_sqm']) / max_price_per_sqm * 50) * df['location_weight']

    # Demand Score
    df['demand_score'] = df['location_weight'] * 50

    # Investment Score
    df['investment_score'] = (0.4 * df['appreciation_score']) + (0.4 * df['rental_score']) + (0.2 * df['demand_score'])
    df['investment_score'] = df['investment_score'].clip(0, 100)  # Normalize to 0-100
    return df

df = calculate_investment_score(df)

# Streamlit app
st.title("UAE Property Market Analytics Dashboard")
st.markdown("Identify top investment properties in UAE for rental yield and future value growth")

# Project filter
projects = ['All'] + sorted(df['project'].unique().tolist())
selected_project = st.selectbox("Select Project", projects)

# Filter data
filtered_df = df if selected_project == 'All' else df[df['project'] == selected_project]

# Top Investment Properties
st.subheader("Top Properties for Investment")
top_invest_df = filtered_df[['property_id', 'investment_score', 'price', 'predicted_price', 'size_sqm', 'location', 'project', 'cluster_label']].sort_values(by='investment_score', ascending=False).head(10)
top_invest_df['investment_score'] = top_invest_df['investment_score'].round(2)
st.dataframe(top_invest_df)

# Scatter Plot: Investment Score vs Price
st.subheader("Investment Score vs Price")
fig_scatter = px.scatter(
    filtered_df,
    x='price',
    y='investment_score',
    color='cluster_label',
    size='size_sqm',
    hover_data=['property_id', 'location', 'project'],
    title="Investment Potential by Price and Cluster",
    labels={'price': 'Price (AED)', 'investment_score': 'Investment Score (0-100)'}
)
st.plotly_chart(fig_scatter)

# Bar Chart: Average Investment Score by Project
st.subheader("Average Investment Score by Project")
avg_score_df = filtered_df.groupby('project')['investment_score'].mean().reset_index().sort_values(by='investment_score', ascending=False)
avg_score_df['investment_score'] = avg_score_df['investment_score'].round(2)
fig_bar = px.bar(
    avg_score_df,
    x='project',
    y='investment_score',
    title="Average Investment Score by Project",
    labels={'investment_score': 'Avg Investment Score (0-100)', 'project': 'Project'},
    color='project'
)
st.plotly_chart(fig_bar)