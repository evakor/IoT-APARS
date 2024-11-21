% Json data from api
CREATE TABLE station_aqi(
	id INT PRIMARY KEY IDENTITY,
	uid UID UNIQUE,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	aqi INT 
); 

% Our artificial interpolated only from station data map
CREATE TABLE grid_station_aqi(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	aqi INT 
); 

% Tha doume
CREATE TABLE grid_satellite_aqi(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	measurement FLOAT, 
	aqi INT 
); 

% Corresponds to each car and its measurements
CREATE TABLE car_sensor_measurements(
	id INT PRIMARY KEY IDENTITY,
	timestamp TIMESTAMP, 
	latitude FLOAT, 
	longitude FLOAT, 
	co2 FLOAT, 
	humidity FLOAT, 
	temperature FLOAT, 
	pm1 FLOAT, 
	pm25 FLOAT, 
	pm10 FLOAT, 
	tvoc FLOAT, 
	eco2 FLOAT,
	aqi INT
); 
