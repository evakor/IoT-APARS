import json
from collections import Counter


def classify_traffic(duration_without_traffic, duration_with_traffic):
    """Classifies traffic conditions based on duration ratios."""
    if duration_with_traffic == "N/A" or duration_without_traffic == "N/A":
        return "No data"

    # Convert durations to seconds for comparison
    duration_without_traffic_sec = int(duration_without_traffic.split()[0]) * 60
    duration_with_traffic_sec = int(duration_with_traffic.split()[0]) * 60

    if duration_with_traffic_sec > 1.5 * duration_without_traffic_sec:
        return "High"
    elif duration_with_traffic_sec > 1.2 * duration_without_traffic_sec:
        return "Medium"
    else:
        return "Low"


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
        traffic_data = json.load(json_file)

    traffic_conditions = []

    for region_id, region_info in traffic_data.items():
        origin = region_info["origin"]
        destination = region_info["destination"]
        if (
            abs(float(origin.split(",")[0]) - south) <= tolerance and
            abs(float(origin.split(",")[1]) - west) <= tolerance and
            abs(float(destination.split(",")[0]) - north) <= tolerance and
            abs(float(destination.split(",")[1]) - east) <= tolerance
        ):
            # Extract traffic durations
            traffic = region_info.get("traffic", {})
            duration_without_traffic = traffic.get("duration_without_traffic", "N/A")
            duration_with_traffic = traffic.get("duration_with_traffic", "N/A")

            # Classify traffic condition
            traffic_condition = classify_traffic(duration_without_traffic, duration_with_traffic)
            traffic_conditions.append(traffic_condition)

    return get_most_common_traffic_condition(traffic_conditions) if traffic_conditions else "Region not found"


# Testing or running this part
if __name__ == "__main__":
    filename = "traffic_only_data.json"  # Use traffic-only JSON file
    user_input_coordinates = {
        "south": 37.95,
        "west": 23.75,
        "north": 37.97,
        "east": 23.77
    }
    result = get_region_from_coordinates(
        filename,
        user_input_coordinates["south"],
        user_input_coordinates["west"],
        user_input_coordinates["north"],
        user_input_coordinates["east"],
        tolerance = 0.05
    )
    print(result)
