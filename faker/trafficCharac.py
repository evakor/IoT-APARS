import json
from collections import Counter

def get_most_common_traffic_condition(traffic_conditions):
    """Returns the most common traffic condition from a list."""
    if not traffic_conditions:
        return "No data available"
    traffic_counter = Counter(traffic_conditions)
    most_common_condition, _ = traffic_counter.most_common(1)[0]
    return most_common_condition

def get_region_from_coordinates(filename, south, west, north, east, tolerance=0.01):
    """Retrieve traffic data for the region containing the given coordinates within a specified tolerance."""
    with open(filename, 'r') as json_file:
        athens_traffic_data = json.load(json_file)

    for region_id, region_info in athens_traffic_data.items():
        if "coordinates" in region_info:
            coords = region_info["coordinates"]
            if (
                coords["south"] <= south + tolerance and
                coords["north"] >= north - tolerance and
                coords["west"] <= west + tolerance and
                coords["east"] >= east - tolerance
            ):
                if "traffic_data" in region_info and "traffic_conditions" in region_info["traffic_data"]:
                    most_common_traffic = get_most_common_traffic_condition(region_info["traffic_data"]["traffic_conditions"])
                    # return f"Most common traffic condition: {most_common_traffic}"
                    return most_common_traffic
                else:
                    return "Traffic data not available"
    return "Region not found"

# Testing or running this parts
if __name__ == "__main__":
    filename = "athens_traffic_data.json"
    user_input_coordinates = {
        "south": 37.95,
        "west": 23.75,
        "north": 37.97,
        "east": 23.77
    }
    result = get_region_from_coordinates(filename, 
                                         user_input_coordinates["south"],
                                         user_input_coordinates["west"],
                                         user_input_coordinates["north"],
                                         user_input_coordinates["east"])
    print(result)
    
