"""Conversion utilities for distance and fuel efficiency."""

from loguru import logger

# Conversion constants
KM_TO_MILES = 0.621371192
MILES_TO_KM = 1.60934
L_TO_MPG_FACTOR = 282.5


def convert_to_miles(kilometers: float) -> float:
    """Convert kilometers to miles.

    Args:
        kilometers: Distance in kilometers

    Returns:
        Equivalent distance in miles

    """
    logger.debug("Converting %s kilometers to miles...", kilometers)
    return kilometers * KM_TO_MILES


def convert_to_km(miles: float) -> float:
    """Convert miles to kilometers.

    Args:
        miles: Distance in miles

    Returns:
        Equivalent distance in kilometers

    """
    logger.debug("Converting %s miles to kilometers...", miles)
    return miles * MILES_TO_KM


def convert_distance(
    convert_to: str,
    convert_from: str,
    value: float,
    decimal_places: int = 3,
):
    """Convert distance between kilometers and miles.

    Args:
        convert_to: Target unit ("km" or "miles")
        convert_from: Source unit ("km" or "miles")
        value: Distance value to convert
        decimal_places: Number of decimal places for result rounding

    Returns:
        Converted distance value

    """
    if convert_to == convert_from:
        return round(value, decimal_places)
    if convert_to == "km":
        return round(convert_to_km(value), decimal_places)
    return round(convert_to_miles(value), decimal_places)


def convert_to_liter_per_100_miles(liters: float) -> float:
    """Convert liters per 100 km to liters per 100 miles.

    Args:
        liters: Fuel consumption in liters per 100 km

    Returns:
        Fuel consumption in liters per 100 miles

    """
    logger.debug("Converting %s L/100km to L/100miles...", liters)
    return round(liters * MILES_TO_KM, 4)


def convert_to_mpg(liters_per_100_km: float) -> float:
    """Convert to miles per UK gallon (MPG).

    Args:
        liters_per_100_km: Fuel consumption in liters per 100 km

    Returns:
        Fuel efficiency in miles per gallon

    """
    logger.debug("Converting %s L/100km to MPG...", liters_per_100_km)
    return (
        round(L_TO_MPG_FACTOR / liters_per_100_km, 4) if liters_per_100_km > 0 else 0.0
    )
