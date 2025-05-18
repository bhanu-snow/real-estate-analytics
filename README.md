# Real-Time Property Market Analytics Dashboard

## Overview
This project builds a real-time analytics dashboard for the Saudi Arabia (KSA) and UAE property markets, focusing on projects by ROSHN, WSP, Al-Arkam, Emaar, Tiger Properties, and Azizi Developments. It ingests property listings from the Bayut API, processes data using Kafka and Python, stores it in PostgreSQL, applies AI models for price prediction and property segmentation, and visualizes insights with Streamlit. A LinkedIn post promotes the dashboard to key UAE/KSA real estate and tech leaders. The pipeline demonstrates skills in data engineering, streaming, ETL, machine learning, and visualization, tailored for KSA and UAE real estate employers.

## Architecture
- **Data Ingestion**: Bayut API fetches UAE and KSA property listings (e.g., Dubai, Abu Dhabi, Riyadh, Jeddah) with pagination, sent to a Kafka topic (`property_data`).
- **Streaming**: Kafka producer (`producer.py`) sends data to the topic; consumer (`consumer.py`) stores it in PostgreSQL (`properties` table).
- **AI Models**: Python script (`ai_models.py`) trains linear regression for price prediction and K-means for property segmentation, saving results to PostgreSQL (`ai_results` table) and CSV (`ai_output.csv`).
- **Storage**: PostgreSQL stores raw data (`properties`) and AI outputs (`ai_results`).
- **Visualization**: Streamlit dashboard (`streamlit_app.py`) ranks properties by Investment Score for rental yield and future value growth.
- **Future Steps**: Power BI visuals (planned).

## Project Structure
```
real-estate-analytics/
├── data/
│   ├── ai_output.csv           # Backup AI output
│   ├── regression_model.pkl    # Price prediction model
│   ├── kmeans_model.pkl        # Clustering model
│   ├── label_encoder_location.pkl
│   ├── label_encoder_project.pkl
├── src/
│   ├── kafka/
│   │   ├── producer.py         # Kafka producer with Bayut API pagination
│   │   └── consumer.py         # Kafka consumer to PostgreSQL
│   ├── ai/
│   │   └── ai_models.py        # AI models with PostgreSQL storage
│   ├── dashboard/
│   │   └── streamlit_app.py    # Streamlit dashboard
├── docs/
├── docker-compose.yml          # Kafka, Zookeeper, PostgreSQL setup
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore file
```

## Prerequisites
- **Docker Desktop**: For Kafka, Zookeeper, and PostgreSQL.
- **Python 3.11**: For scripts and dependencies.
- **Bayut API Key**: From RapidAPI (replace in `producer.py`).
- **Windows 11**: Tested environment (adjust for other OS).

## Setup Instructions
1. **Clone Repository**:
    ```powershell
    git clone <repository-url>
    cd real-estate-analytics
    ```

2. **Set Up Python Environment**:
    ```powershell
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Start Docker Services**:
    - Update `docker-compose.yml` with correct host settings if needed (e.g., `localhost:9092`).
    - Run:
        ```powershell
        docker-compose up -d
        ```

4. **Create PostgreSQL Tables**:
    - Connect to PostgreSQL:
        ```powershell
        docker exec -it $(docker ps -q -f name=postgres) psql -U user -d property_db
        ```
    - Create `properties` table:
        ```sql
        CREATE TABLE properties (
            property_id INTEGER PRIMARY KEY,
            price INTEGER,
            location VARCHAR(100),
            size_sqm INTEGER,
            timestamp TIMESTAMP,
            project VARCHAR(50)
        );
        ```
    - Create `ai_results` table:
        ```sql
        CREATE TABLE ai_results (
            property_id INTEGER PRIMARY KEY,
            price INTEGER,
            predicted_price FLOAT,
            size_sqm INTEGER,
            location VARCHAR(100),
            project VARCHAR(50),
            cluster_label VARCHAR(20),
            timestamp TIMESTAMP
        );
        ```
    - Exit: `\q`

5. **Update Bayut API Key**:
    - In `src/kafka/producer.py`, replace `API_KEY` with your RapidAPI key and verify the endpoint.

## Usage
1. **Run Kafka Producer**:
    - Fetches paginated Bayut API data and sends to Kafka:
        ```powershell
        python src\kafka\producer.py
        ```

2. **Run Kafka Consumer**:
    - Consumes Kafka data and stores in `properties` table:
        ```powershell
        python src\kafka\consumer.py
        ```

3. **Run AI Models**:
    - Trains models and saves results to `ai_results` table and `data/ai_output.csv`:
        ```powershell
        python src\ai\ai_models.py
        ```

4. **Run Streamlit Dashboard**:
    - Ranks properties by Investment Score for investment decisions:
        ```powershell
        streamlit run src\dashboard\streamlit_app.py
        ```
    - Open `http://localhost:8501` in your browser.

5. **Verify Data**:
    - Check `properties` table:
        ```powershell
        docker exec -it $(docker ps -q -f name=postgres) psql -U user -d property_db -c "SELECT COUNT(*) FROM properties;"
        ```
    - Check `ai_results` table:
        ```powershell
        docker exec -it $(docker ps -q -f name=postgres) psql -U user -d property_db -c "SELECT * FROM ai_results LIMIT 5;"
        ```

## Data Pipeline
- **Ingestion**: `producer.py` fetches UAE and KSA property listings (e.g., Emaar’s Dubai Creek Harbour, ROSHN-SEDR) with pagination (up to 20 pages, 10 hits/page) via Bayut API.
- **Streaming**: Kafka topic `property_data` handles real-time data.
- **Storage**: `consumer.py` saves to `properties` table with `ON CONFLICT` to handle duplicate `property_id`.
- **AI Models**:
    - **Price Prediction**: Linear regression using `size_sqm`, `location`, `project`, `price_per_sqm`.
    - **Segmentation**: K-means clustering into Low-Value, Mid-Value, High-Value groups.
    - Results saved to `ai_results` table for reuse without retraining.
- **Visualization**: Streamlit dashboard ranks properties by Investment Score, combining predicted price growth, rental yield, and Vision 2030-driven demand.

## Business Value
- **Investment Score**: Helps buyers identify properties with high rental yield and future value potential, based on price trends, location demand (e.g., Dubai’s luxury market, Riyadh’s Vision 2030 projects), and cost efficiency.
- **Real-Time Insights**: Enables developers like Emaar and ROSHN to prioritize high-return projects, aligning with UAE’s Economic Vision 2030 and KSA’s Vision 2030.
- **Bayut API Integration**: Provides comprehensive UAE and KSA property data, enhancing decision-making for investors and developers.

## Troubleshooting
- **Kafka Issues**:
    - Verify `localhost:9092`:
    ```powershell
    telnet localhost 9092
    ```
    - Check logs:
    ```powershell
    docker logs $(docker ps -q -f name=kafka)
    ```
- **PostgreSQL Issues**:
    - Use container IP if `localhost:5432` fails:
    ```powershell
    docker inspect $(docker ps -q -f name=postgres) | findstr IPAddress
    ```
- **Bayut API**:
    - Validate endpoint and pagination parameter in `producer.py`.
    - Test API:
    ```powershell
    curl --request GET \
	--url 'https://bayut.p.rapidapi.com/properties/list?locationExternalIDs=5002%2C6020&purpose=for-rent&hitsPerPage=25&page=0&lang=en&sort=tuned-ranking&category=residential&rentFrequency=monthly&categoryExternalID=4' \
	--header 'x-rapidapi-host: bayut.p.rapidapi.com' \
	--header 'x-rapidapi-key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    ```
- **AI Models**:
    - Ensure 100+ properties in `properties` table.
    - Check logs in `ai_models.py` output.
- **Streamlit Issues**:
    - Ensure `ai_results` table has data.
    - Check terminal logs for errors.

## Next Steps
- **Power BI Reports**: Create professional reports for stakeholders.
- **Deployment**: Host dashboard on Streamlit Cloud or a KSA/UAE server.
