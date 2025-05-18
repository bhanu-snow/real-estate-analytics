CREATE TABLE properties (
    property_id INTEGER PRIMARY KEY,
    price INTEGER,
    location VARCHAR(100),
    size_sqm INTEGER,
    timestamp TIMESTAMP,
    project VARCHAR(50)
);
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