from kafka import KafkaConsumer
import json
import psycopg2
from psycopg2 import Error

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
    print(f"Error connecting to PostgreSQL: {e}")
    exit(1)

consumer = KafkaConsumer(
    'property_data',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    data = message.value
    print(f"Received: {data}")
    try:
        cursor.execute(
            """
            INSERT INTO properties (property_id, price, location, size_sqm, timestamp, project)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (property_id) DO UPDATE
            SET price = EXCLUDED.price,
                location = EXCLUDED.location,
                size_sqm = EXCLUDED.size_sqm,
                timestamp = EXCLUDED.timestamp,
                project = EXCLUDED.project
            """,
            (
                data['property_id'],
                data['price'],
                data['location'],
                data['size_sqm'],
                data['timestamp'],
                data['project']
            )
        )
        conn.commit()
        print(f"Inserted/Updated: {data}")
    except Error as e:
        print(f"Error inserting data: {e}")
        conn.rollback()

# Cleanup
cursor.close()
conn.close()