import asyncio
import os
from aiotractive import Tractive
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def send_to_item(item_name, payload):
    async with aiohttp.ClientSession() as session:
        baseurl = os.getenv("OPENHAB_URL")
        url = f"{baseurl}/rest/items/{item_name}/state"
        async with session.put(url, data=payload) as response:
            if not (response.status >= 200 and response.status < 300):
                raise Exception(f"Failed to update: {response.status}")

async def gather_tractive_data():
    async with Tractive(
        os.getenv("TRACTIVE_USERNAME"), os.getenv("TRACTIVE_PASSWORD")
    ) as client:
        await client.authenticate()

        # I just have one tracker.
        trackers = await client.trackers()

        for tracker in trackers:
            details = await tracker.details()
            hw_id = details["hw_id"]

            position = await tracker.pos_report()
            location = position["latlong"]

            # TODO: Need a more general purpose way to do this.
            if position["power_saving_zone_id"] == "66183b1a8daa09e1aed7f017":
                await send_to_item(f"{hw_id}_Presence", "ON")
            else:
                await send_to_item(f"{hw_id}_Presence", "OFF")

            await send_to_item(f"{hw_id}_Location", f"{location[0]},{location[1]}")
    pass

async def main():
    while True:
        await gather_tractive_data()
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
