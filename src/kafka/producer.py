from kafka import KafkaProducer
import json
import requests
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bayut API setup
API_KEY = '1b845d550amshd77019c2fa11e93p15333cjsn2cf9b9925961'  # Replace with your key
URL = 'https://bayut.p.rapidapi.com/properties/list'  # Update with correct endpoint
HEADERS = {
    'X-RapidAPI-Key': API_KEY,
    'X-RapidAPI-Host': 'bayut.p.rapidapi.com'
}
PARAMS = {
    'locationExternalIDs':6020,
    'purpose': 'for-sale',
    'hitsPerPage': 20,
    'categoryExternalID':4,
    #'location': 'Riyadh',  # Focus on ROSHN/Al-Arkam
    #'category': 'residential',
    #'purpose': 'for-sale',
    #'hitsPerPage': 10,
    'page': 1  # Start at page 1
}

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Track unique property IDs
seen_ids = set()

# Fetch data with pagination
max_pages = 20  # Limit to avoid excessive API calls
page = 1

while page <= max_pages:
    try:
        logger.info(f"Fetching page {page}")
        PARAMS['page'] = page
        response = requests.get(URL, headers=HEADERS, params=PARAMS)
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            break

        data = response.json()
        properties = data.get('hits', [])
        
        if not properties:
            logger.info("No more properties found")
            break

        for prop in properties:
            property_id = prop.get('id')
            if property_id in seen_ids:
                continue  # Skip duplicates
            seen_ids.add(property_id)

            prop_data = {                
                'property_id': property_id,
                'price': prop.get('price', 0),
                'location': (prop.get('location') or [{}])[0].get('name', 'Riyadh'),
                'size_sqm': prop.get('area', 0),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'project': prop.get('project', {}).get('agency',{}).get('name', '') 
            }

            # Check message size
            serialized_data = json.dumps(prop_data).encode('utf-8')
            if len(serialized_data) > 1000000:  # 1MB limit
                logger.warning(f"Skipping large message: {len(serialized_data)} bytes")
                continue

            producer.send('property_data', value=prop_data)
            logger.info(f"Sent: {prop_data}")

        page += 1
        time.sleep(5)  # Respect API rate limits

    except Exception as e:
        logger.error(f"Error fetching page {page}: {e}")
        break

producer.flush()
logger.info(f"Completed: Sent {len(seen_ids)} unique properties")