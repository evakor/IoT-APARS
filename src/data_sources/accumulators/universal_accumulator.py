import json
from datetime import datetime
from typing import List, Dict, Any, Union

# Smart Data Model Template
SMART_DATA_MODEL_TEMPLATE = {
    "id": "",
    "type": "SensorAirQualityObserved",
    "dateObserved": {
        "type": "DateTime",
        "value": ""
    },
    "aqi": {
        "type": "Number",
        "value": 0.0
    },
    "location": {
        "type": "geo:json",
        "value": {
            "type": "Point",
            "coordinates": []
        }
    }
}

def get_value_from_payload(data: Dict[str, Any], keys: List[Union[str, int]]) -> Any:
    """
    Retrieves a value from the nested payload based on the specified key path.
    """
    for key in keys:
        if isinstance(data, (list, dict)) and key in data:
            data = data[key]
        elif isinstance(data, list) and isinstance(key, int):
            data = data[key]
        else:
            return None
    return data

def map_to_sdm(config: Dict[str, Any], payload: Union[Dict[str, Any], List], position: int = None) -> Dict[str, Any]:
    """
    Maps data from the payload to the Smart Data Model format based on the provided configuration.
    """
    sdm = SMART_DATA_MODEL_TEMPLATE.copy()

    for key, mapping in config["mapping"].items():
        if mapping["getFromPayload"]:
            value = get_value_from_payload(payload, mapping["value"])
            if value in mapping.get("expectInCaseOfMissing", []):
                value = 10  # Default AQI if missing or invalid
            else:
                try:
                    value = float(value)
                except Exception:
                    value = 10  # Default if conversion fails
        else:
            if str(key) in ["id", "type", "dateObserved", "location"]:
                value = mapping["value"]
            else:
                try:
                    value = float(mapping["value"])
                except Exception:
                    value = 10  # Default if conversion fails

        if key == "id" and position is not None:
            value = value.replace("$position$", str(position))

        if key == "location":
            coordinates = [
                get_value_from_payload(payload, coord_keys)
                for coord_keys in mapping["value"]["coordinates"]
            ]
            value = {"type": "Point", "coordinates": coordinates}

        sdm[key] = {"type": mapping.get("type", ""), "value": value}

    sdm["dateObserved"]["value"] = datetime.utcnow().isoformat()
    sdm["id"]["type"] = "String" if type(sdm["id"]["value"]) == str else "Number"
    sdm["type"]["type"] = "String" if type(sdm["type"]["value"]) == str else "Number"
    return sdm

def process_payload(config: Dict[str, Any], payload: Union[Dict[str, Any], List], case: int) -> List[Dict[str, Any]]:
    """
    Processes the payload based on the specified case.
    """
    results = []

    if case == 1:
        results.append(map_to_sdm(config, payload))

    elif case == 2:
        if isinstance(payload, list):
            for position, element in enumerate(payload):
                results.append(map_to_sdm(config, element, position))

    elif case == 3:
        sdm = map_to_sdm(config, payload)
        sdm["aqi"]["value"] = convert_to_aqi(sdm["aqi"]["value"])
        results.append(sdm)

    elif case == 4:
        if isinstance(payload, list):
            for position, element in enumerate(payload):
                sdm = map_to_sdm(config, element, position)
                sdm["aqi"]["value"] = convert_to_aqi(sdm["aqi"]["value"])
                results.append(sdm)

    return results

def convert_to_aqi(value: Any) -> float:
    """
    Converts a metric to AQI.
    """
    try:
        return float(value) * 10  # Simplified example of conversion logic
    except (TypeError, ValueError):
        return 10.0

def load_config(file_path: str) -> Dict[str, Any]:
    """
    Loads the configuration from a JSON file.
    """
    with open(file_path, "r") as file:
        return json.load(file)

if __name__ == "__main__":
    config_path = "config.json"  # Path to the configuration file
    config = load_config(config_path)

    # Example payloads (replace with actual data)
    payload_case_1 = {
        "lat": -26.764724,
        "lon": 28.480081,
        "uid": 14050,
        "aqi": 50,
        "station": {
            "name": "Eskom-Grootvlei, Gert Sibande, South Africa",
            "time": "2024-11-19T23:00:00+09:00"
        }
    }

    payload_case_2 = [
        {
            "lat": -26.764724,
            "lon": 28.480081,
            "uid": 14050,
            "aqi": "-",
            "station": {
                "name": "Eskom-Grootvlei, Gert Sibande, South Africa",
                "time": "2024-11-19T23:00:00+09:00"
            }
        },
        {
            "lat": 14.57711,
            "lon": 120.9778,
            "uid": 14893,
            "aqi": "60",
            "station": {
                "name": "Manila US Embassy, Philippines",
                "time": "2024-11-20T19:00:00+09:00"
            }
        }
    ]

    results = process_payload(config, payload_case_2, config["case"])
    print(json.dumps(results, indent=4))
