"""Formatters for instrument data."""

from typing import Any, Dict, List


def format_odometer(raw: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format odometer information from a list to a dict.

    Args:
        raw: A list of instrument dictionaries, where each dictionary
             contains at least 'type' and 'value' keys, and optionally 'unit'.

    Returns:
        A flattened dictionary where keys are instrument types and values are
        the corresponding values. Units are stored with '_unit' suffix.

    Example:
        >>> format_odometer(
        ...     [
        ...         {"type": "distance", "value": 12345, "unit": "km"},
        ...         {"type": "speed", "value": 60},
        ...     ]
        ... )
        {'distance': 12345, 'distance_unit': 'km', 'speed': 60}

    """
    instruments: Dict[str, Any] = {}

    for instrument in raw:
        instrument_type = instrument["type"]
        instruments[instrument_type] = instrument["value"]

        if "unit" in instrument:
            instruments[f"{instrument_type}_unit"] = instrument["unit"]

    return instruments
