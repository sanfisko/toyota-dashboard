"""Simple test of new API Changes."""

import asyncio
import json
import sys
from pathlib import Path

from loguru import logger

from pytoyoda.client import MyT

# from pytoyoda.models.endpoints.climate import ACOperations, ACParameters, ClimateSettingsModel  # noqa: E501
# from pytoyoda.models.endpoints.command import CommandType

logger.remove(0)
logger.add(sys.stderr, level="INFO")


# Set your username and password in a file inside the "sandbox" folder called "credentials.json" in the format: # noqa: E501
#   {
#       "username": "<username>",
#       "password": "<password>"
#   }


def load_credentials():
    """Load credentials from 'credentials.json'."""
    try:
        with open(Path(__file__).parent / "credentials.json", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return None


credentials = load_credentials()
if not credentials:
    raise ValueError(
        "Did you forget to set your username and password?"
        "Or supply the credentials file inside the 'sandbox' folder?"
    )

USERNAME = credentials["username"]
PASSWORD = credentials["password"]

client = MyT(username=USERNAME, password=PASSWORD, use_metric=True)


async def get_information():
    """Test login and output from endpoints."""
    logger.info("Logging in...")
    await client.login()

    logger.info("Retrieving cars...")
    cars = await client.get_vehicles()

    for car in cars:
        if car:
            response = await car._api.update_vehicle_electric_realtime_status(
                vin=car.vin
            )
            logger.info(
                f"Requesting update to SOC: {response.model_dump_json(indent=4)}"
            )
            await car.update()
            logger.info(f"SOC {car.electric_status.model_dump_json(indent=4)}")


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(get_information())
loop.close()
