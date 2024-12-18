FROM python:3.10

ADD SatelliteDataAccumulator.py .

RUN pip install cdsapi numpy netCDF4 requests python-dotenv schedule

CMD ["python", "./SatelliteDataAccumulator.py"] 