def getAQI(parameter, value):
    """
    Calculate the AQI for a given parameter and its value based on the breakpoints.

    Args:
        parameter (str): The name of the parameter (e.g., 'PM2.5', 'CO2').
        value (float): The measured value of the parameter.

    Returns:
        int: The calculated AQI value.

    Sources:
    This code provides a detailed categorization of air quality for various pollutants, including PM1, PM2.5, PM10, NH3 (ammonia), oxidized gases, reduced gases, CO2 (carbon dioxide), and dust. The AQI parameters are defined with specific breakpoints, reflecting pollutant concentration ranges and their associated health effects.

    The AQI parameters and breakpoints are derived from the following authoritative sources:

    1. Prana Air Blog: This source explains the concept of AQI, its calculation, and general pollutant categories.
    [What is Air Quality Index (AQI) and its Calculation](https://www.pranaair.com/in/blog/what-is-air-quality-index-aqi-and-its-calculation/)  

    

    2. U.S. Environmental Protection Agency (EPA): The EPA document outlines AQI breakpoints and their health implications for particulate matter (PM).
    [PM National Ambient Air Quality Standards (NAAQS) Air Quality Index Fact Sheet](https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf)  

    
    3. Central Pollution Control Board (CPCB), India: The CPCB source provides AQI standards specific to India, which are comparable to global AQI systems.
    [About AQI](http://app.cpcbccr.com/ccr_docs/About_AQI.pdf)  

    

    4. ResearchGate Publication: This paper offers insights into the integration of various air quality indices and their computational models.
    [Information Fusion for Computational Assessment of Air Quality and Health Effects](https://www.researchgate.net/publication/231814203_Information_Fusion_for_Computational_Assessment_of_Air_Quality_and_Health_Effects/link/5a3cdb95aca272dd65e5ec6e/download?_tp=eyJjb250ZXh0Ijp7ImZpcnN0UGFnZSI6Il9kaXJlY3QiLCJwYWdlIjoicHVibGljYXRpb24ifX0=)  

    
    The parameters and their corresponding AQI breakpoints were consolidated based on these sources. In cases where specific breakpoints were not defined (e.g., for dust or reduced gases), similar parameters like PM2.5 or oxidized gases were used to approximate the breakpoints.
    The compiled data can be used for environmental monitoring, public awareness, and policymaking. It is especially useful for projects requiring a detailed understanding of pollutant behavior and their health impacts, such as the development of live AQI monitoring systems.
    """

    aqi_ranges = [
        (0, 50),
        (51, 100),
        (101, 150),
        (151, 200),
        (201, 300),
        (301, 500),
    ]

    breakpoints = {
        "PM1": [
            (0, 9), 
            (9.1, 35.4), 
            (35.5, 55.4), 
            (55.5, 125.4), 
            (125.5, 225.4), 
            (225.5, 500)
            ],
        "PM2.5": [
            (0, 9), 
            (9.1, 35.4), 
            (35.5, 55.4), 
            (55.5, 125.4), 
            (125.5, 225.4), 
            (225.5, 500)
            ],
        "PM10": [
            (0, 54), 
            (54.1, 154), 
            (154.1, 254), 
            (254.1, 354), 
            (354.1, 424), 
            (424.1, 604)
            ],
        "NH3": [
            (0, 200), 
            (200.1, 400), 
            (400.1, 800), 
            (800.1, 1200), 
            (1200.1, 1800), 
            (1800.1, 2400)
            ],
        "Oxidized Gases": [
            (0, 100), 
            (100.1, 200), 
            (200.1, 300), 
            (300.1, 400), 
            (400.1, 500), 
            (500.1, 600)
            ],
        "Reduced Gases": [
            (0, 100), 
            (100.1, 200), 
            (200.1, 300), 
            (300.1, 400), 
            (400.1, 500), 
            (500.1, 600)
            ],
        "CO2": [
            (0, 350), 
            (350.1, 600), 
            (600.1, 1000), 
            (1000.1, 1500), 
            (1500.1, 2000), 
            (2000.1, 5000)
            ],
        "CO": [
            (0.0, 4.4),
            (4.5, 9.4),
            (9.5, 12.4),
            (12.5, 15.4),
            (15.5, 30.4),
            (30.5, 50.4),
        ],
        "Dust": [
            (0, 54), 
            (54.1, 154), 
            (154.1, 254), 
            (254.1, 354), 
            (354.1, 424), 
            (424.1, 604)
            ],
    }

    if parameter not in breakpoints:
        raise ValueError(f"Unknown parameter: {parameter}")

    for (low_bp, high_bp), (low_aqi, high_aqi) in zip(breakpoints[parameter], aqi_ranges):
        if low_bp <= value <= high_bp:
            aqi = ((high_aqi - low_aqi) / (high_bp - low_bp)) * (value - low_bp) + low_aqi
            return round(aqi)

    return None

if __name__=="__main__":
    example_aqi = getAQI("PM2.5", 40)
    print(example_aqi)