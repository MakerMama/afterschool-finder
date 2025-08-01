import pandas as pd
from datetime import datetime
import requests
import time
from typing import Optional, Tuple, Dict
from math import radians, sin, cos, sqrt, atan2

# Cache for storing geocoded coordinates
coordinate_cache: Dict[str, Optional[Tuple[float, float]]] = {}

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    Returns distance in miles.
    """
    R = 3959.87433  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def parse_time(time_str: str) -> datetime.time:
    """Convert time string to datetime.time object"""
    try:
        return datetime.strptime(time_str, '%I:%M %p').time()
    except ValueError:
        return datetime.strptime(time_str, '%H:%M').time()

def is_time_in_range(start_time: str, end_time: str, range_start: str, range_end: str) -> bool:
    """Check if program time falls within specified range"""
    prog_start = parse_time(start_time)
    prog_end = parse_time(end_time)
    filter_start = parse_time(range_start)
    filter_end = parse_time(range_end)

    return prog_start >= filter_start and prog_end <= filter_end

def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address to coordinates using OpenStreetMap's Nominatim API.
    Includes caching and rate limiting.
    """
    if address in coordinate_cache:
        return coordinate_cache[address]

    try:
        # Rate limiting - be nice to the API
        time.sleep(1)

        # Create a properly formatted search URL
        search_url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'AfterSchoolProgramFinder/1.0'}
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }

        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()

        results = response.json()
        if results:
            lat = float(results[0]['lat'])
            lon = float(results[0]['lon'])
            coordinate_cache[address] = (lat, lon)
            return (lat, lon)

        coordinate_cache[address] = None
        return None

    except Exception as e:
        print(f"Error geocoding address {address}: {str(e)}")
        coordinate_cache[address] = None
        return None

def filter_programs(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Filter programs based on multiple criteria
    """
    filtered_df = df.copy()

    # Days filter
    if filters.get('selected_days'):
        filtered_df = filtered_df[filtered_df['Day of the week'].isin(filters['selected_days'])]

    # Child age filter - show programs where child's age falls within the program's age range
    if filters.get('child_age') is not None:
        child_age = filters['child_age']
        filtered_df = filtered_df[
            (filtered_df['Min Age'] <= child_age) & 
            (filtered_df['Max Age'] >= child_age)
        ]

    # Time range filter
    if filters.get('start_time') and filters.get('end_time'):
        filtered_df = filtered_df[
            filtered_df.apply(
                lambda row: is_time_in_range(
                    row['Start time'],
                    row['End time'],
                    filters['start_time'],
                    filters['end_time']
                ),
                axis=1
            )
        ]

    # Interest categories filter
    if filters.get('selected_interests'):
        filtered_df = filtered_df[filtered_df['Interest Category'].isin(filters['selected_interests'])]

    # Distance filter
    if filters.get('user_address') and filters.get('max_distance'):
        user_coords = geocode_address(filters['user_address'])
        if user_coords:
            # Calculate distances for all programs
            distances = []
            for _, program in filtered_df.iterrows():
                prog_coords = geocode_address(program['Address'])
                if prog_coords:
                    distance = calculate_distance(
                        user_coords[0], user_coords[1],
                        prog_coords[0], prog_coords[1]
                    )
                    distances.append(distance)
                else:
                    distances.append(float('inf'))

            # Add distances to dataframe and filter
            filtered_df['Distance'] = distances
            filtered_df = filtered_df[filtered_df['Distance'] <= filters['max_distance']]
            filtered_df = filtered_df.sort_values('Distance')  # Sort by distance

    return filtered_df

def load_and_process_data(file_path):
    """Load and process the CSV data with enhanced validation."""
    try:
        df = pd.read_csv(file_path)

        # Validate required columns
        required_columns = [
            'Provider Name', 'Program Name', 'Day of the week',
            'Start time', 'End time', 'Interest Category'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Convert date columns to datetime (allow both MM/DD/YYYY and M/D/YYYY)
        date_columns = ['Start date', 'End date']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%m/%d/%Y')
                except ValueError:
                    try:
                        df[col] = pd.to_datetime(df[col], format='%m/%d/%y')
                    except ValueError:
                        try:
                            df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
                        except Exception:
                            raise ValueError(f"Error in {col}: Dates must be in MM/DD/YYYY or similar format")

        # Convert time columns to proper format
        time_columns = ['Start time', 'End time']
        for col in time_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col]).dt.strftime('%I:%M %p')
                except ValueError as e:
                    raise ValueError(f"Error in {col}: Times must be in HH:MM AM/PM format")

        # Convert cost columns to numeric, removing '$' and ',' characters
        if 'Cost' in df.columns:
            df['Cost'] = df['Cost'].replace('[\$,]', '', regex=True).astype(float)
        if 'Cost Per Class' in df.columns:
            df['Cost Per Class'] = df['Cost Per Class'].replace('[\$,]', '', regex=True).astype(float)

        # Normalize day names (remove 's' from plural days)
        df['Day of the week'] = df['Day of the week'].str.rstrip('s')

        # Validate days of week
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        invalid_days = df[~df['Day of the week'].isin(valid_days)]['Day of the week'].unique()
        if len(invalid_days) > 0:
            raise ValueError(f"Invalid days found: {', '.join(invalid_days)}")

        return df
    except Exception as e:
        raise Exception(f"Error processing CSV file: {str(e)}")

def get_unique_values(df, column):
    """Get sorted unique values from a column."""
    return sorted(df[column].unique())