For context broker

Station Schema:

{
	"id": f"station_{uid}",
	"type": "ground_station",
	"timestamp": {
		"type": "DateTime",
		"value": timestamp
	},
	"latitude": {
		"type": "Float",
		"value": latitude
	},
	"longitude": {
		"type": "Float",
		"value": longitude
	},
	"aqi": {
		"type": "Integer",
		"value": aqi
	}
}

Satellite Schema:

{
	"id": f"satellite_{lat}_{lon}",
	"type": "satellite",
	"timestamp": {
		"type": "DateTime",
		"value": timestamp
	},
	"latitude": {
		"type": "Float",
		"value": latitude
	},
	"longitude": {
		"type": "Float",
		"value": longitude
	},
	"aqi": {
		"type": "Integer",
		"value": aqi
	}
}

Car Schema:

{
    "id": "car_{serial}",
    "type": "car",
    "timestamp": {
        "type": "DateTime",
        "value": timestamp
    },
    "latitude": {
        "type": "Float",
        "value": latitude
    },
    "longitude": {
        "type": "Float",
        "value": longitude
    },
    "oxidised": {
        "type": "Float",
        "value": oxidised
    },
    "reduced": {
        "type": "Float",
        "value": reduced
    },
    "nh3": {
        "type": "Float",
        "value": nh3
    },
    "pm1": {
        "type": "Float",
        "value": pm1
    },
    "pm25": {
        "type": "Float",
        "value": pm25
    },
    "pm10": {
        "type": "Float",
        "value": pm10
    }
}

For database:


CREATE TABLE car_sensor_measurements(
	id INT PRIMARY KEY IDENTITY,
	car_id VARCHAR,
	timestamp TIMESTAMP,
	longitude FLOAT,
	latitude FLOAT,
	oxidised FLOAT,
	reduced FLOAT,
	nh3 FLOAT,
	pm1 FLOAT,
	pm25 FLOAT,
	pm10 FLOAT
);

CREATE TABLE station_aqi_grid(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	aqi INT 
); 

CREATE TABLE satellite_aqi_grid(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	aqi INT 
); 

CREATE TABLE interpolated_aqi_grid(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	aqi INT 
); 

CREATE TABLE users(
	id INT PRIMARY KEY IDENTITY,
	username VARCHAR, 
	password VARCHAR
); 