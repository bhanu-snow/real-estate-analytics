import pandas as pd
import psycopg2
from psycopg2 import Error
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
import pickle
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
    cursor = conn.cursor()
except Error as e:
    logger.error(f"Error connecting to PostgreSQL: {e}")
    exit(1)

# Extract data
query = "SELECT property_id, price, location, size_sqm, project, timestamp FROM properties"
df = pd.read_sql(query, conn)
logger.info(f"Loaded {len(df)} properties from PostgreSQL")

# Check data volume
if len(df) < 50:
    logger.warning("Insufficient data for modeling. Need 50+ properties.")
    conn.close()
    exit(1)

# Clean and prepare data
df = df.dropna(subset=['price', 'size_sqm', 'location', 'project'])
df['price_per_sqm'] = df['price'] / df['size_sqm']
logger.info(f"After cleaning, {len(df)} properties remain")

# Encode categorical features
le_location = LabelEncoder()
le_project = LabelEncoder()
df['location_encoded'] = le_location.fit_transform(df['location'])
df['project_encoded'] = le_project.fit_transform(df['project'])

# Price Prediction (Linear Regression)
features = ['size_sqm', 'location_encoded', 'project_encoded', 'price_per_sqm']
X = df[features]
y = df['price']
reg_model = LinearRegression()
reg_model.fit(X, y)
df['predicted_price'] = reg_model.predict(X)
logger.info(f"Price prediction model trained. Score: {reg_model.score(X, y):.2f}")

# Save regression model and encoders
with open('data/regression_model.pkl', 'wb') as f:
    pickle.dump(reg_model, f)
with open('data/label_encoder_location.pkl', 'wb') as f:
    pickle.dump(le_location, f)
with open('data/label_encoder_project.pkl', 'wb') as f:
    pickle.dump(le_project, f)

# Property Segmentation (K-means Clustering)
cluster_features = ['price', 'size_sqm', 'price_per_sqm']
X_cluster = df[cluster_features]
kmeans = KMeans(n_clusters=3, random_state=42)  # 3 clusters: high, mid, low value
df['cluster'] = kmeans.fit_predict(X_cluster)
cluster_labels = {0: 'Low-Value', 1: 'Mid-Value', 2: 'High-Value'}
df['cluster_label'] = df['cluster'].map(cluster_labels)
logger.info("Clustering completed")

# Save clustering model
with open('data/kmeans_model.pkl', 'wb') as f:
    pickle.dump(kmeans, f)

# Save to PostgreSQL
try:
    # Clear existing data (optional, comment out to append)
    cursor.execute("TRUNCATE TABLE ai_results")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO ai_results (property_id, price, predicted_price, size_sqm, location, project, cluster_label, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row['property_id'],
                row['price'],
                row['predicted_price'],
                row['size_sqm'],
                row['location'],
                row['project'],
                row['cluster_label'],
                row['timestamp']
            )
        )
    conn.commit()
    logger.info("Saved AI output to ai_results table")
except Error as e:
    logger.error(f"Error saving to PostgreSQL: {e}")
    conn.rollback()
    conn.close()
    exit(1)

# Optional: Save to CSV for backup
output_df = df[['property_id', 'price', 'predicted_price', 'size_sqm', 'location', 'project', 'cluster_label', 'timestamp']]
output_df.to_csv('data/ai_output.csv', index=False)
logger.info(f"Saved AI output to data/ai_output.csv")

# Summary
logger.info("Cluster Counts:")
logger.info(df['cluster_label'].value_counts())

# Cleanup
cursor.close()
conn.close()