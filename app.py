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
                print(f"Failed to update: {response.status}")

async def main():
    async with Tractive(
        os.getenv("TRACTIVE_USERNAME"), os.getenv("TRACTIVE_PASSWORD")
    ) as client:
        await client.authenticate()

        # I just have one tracker.
        trackers = await client.trackers()
        tracker = trackers[0]

        position = await tracker.pos_report()

        location = position["latlong"]
        if position["power_saving_zone_id"] == "66183b1a8daa09e1aed7f017":
                await send_to_item("Cosmo_Presence", "ON")
        else:
                await send_to_item("Cosmo_Presence", "OFF")

        await send_to_item("Cosmo_Location", f"{location[0]},{location[1]}")
    pass

if __name__ == "__main__":
    asyncio.run(main())
