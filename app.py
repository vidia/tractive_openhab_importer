import asyncio
import os
from aiotractive import Tractive
from aiotractive.exceptions import TractiveError, UnauthorizedError, NotFoundError
import aiohttp
from dotenv import load_dotenv

# Times are specified in seconds
DELAY = 60 * 5  # 5 minutes
RETRY_DELAY = DELAY
RETRY_COUNT = 5


async def send_to_item(item_name, payload):
    print(f"Sending {payload} to OpenHAB item {item_name}")
    async with aiohttp.ClientSession() as session:
        baseurl = os.getenv("OPENHAB_URL")
        url = f"{baseurl}/rest/items/{item_name}/state"
        async with session.put(url, data=payload) as response:
            if not (response.status >= 200 and response.status < 300):
                raise Exception(
                    f"Failed to update {item_name} to {payload} with {response.status}. Does the item exist in OpenHAB?"
                )


async def gather_tractive_data(client):
    # Reauth. Internally it will only reauth if needed.
    await client.authenticate()

    trackers = await client.trackers()
    for tracker in trackers:
        details = await tracker.details()
        hw_id = details["hw_id"]

        position = await tracker.pos_report()
        location = position["latlong"]

        print("Sending data for " + hw_id)
        print("Location: " + str(location))

        # TODO: Need a more general purpose way to do this.
        if position["power_saving_zone_id"] == "66183b1a8daa09e1aed7f017":
            await send_to_item(f"{hw_id}_Presence", "ON")
        else:
            await send_to_item(f"{hw_id}_Presence", "OFF")

        await send_to_item(f"{hw_id}_Location", f"{location[0]},{location[1]}")


async def main():
    username = os.getenv("TRACTIVE_USERNAME")
    password = os.getenv("TRACTIVE_PASSWORD")
    openhab_url = os.getenv("OPENHAB_URL")

    if not username or not password or not openhab_url:
        raise Exception("Missing required environment variables")

    print("=== Starting Tractive to OpenHAB bridge ===")

    print("Logging in to Tractive as : " + username)
    print("Sending data to OpenHAB at : " + openhab_url)

    failures = 0
    async with Tractive(username, password) as client:
        while True:
            try:
                await gather_tractive_data(client)
                # Reset counts on success
                failures = 0
            except TractiveError as e:
                # TractiveErrors can be 429s, so try again after a delay a few times.
                # TODO: Unfortunately other generic errors can be thrown as TractiveErrors.
                print(f"Failed with TractiveError: {e}")
                failures += 1
                if failures > RETRY_COUNT:
                    # Let the exception crash the app.
                    raise e
                else:
                    print("Waiting an additional delay before trying again.")
                    await asyncio.sleep(RETRY_DELAY)
                    continue
            except UnauthorizedError as e:
                print(f"Failed to authorize to Tractive. Check Username and password. Exiting.")
                # Let the exception crash the app.
                raise e

            # Repeat after delay
            print(f"Waiting {DELAY} seconds before repeating")
            await asyncio.sleep(DELAY)
    pass


if __name__ == "__main__":
    load_dotenv()

    asyncio.run(main())
