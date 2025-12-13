import asyncio
import datetime

from lingq.lingqhandler import LingqHandler


async def stats_async(lang: str) -> None:
    year = datetime.datetime.today().year

    async with LingqHandler(lang) as handler:
        stats = await handler.get_stats()
        for day in reversed(stats):
            name = day["name"]
            daily = round(float(day["daily"]))
            date_obj = datetime.datetime.strptime(f"{year}/{name}", "%Y/%m/%d")
            day_of_week = date_obj.strftime("%A")
            print(f"{day_of_week[:3]} {name} {daily}")


def stats(lang: str) -> None:
    """Show stats."""
    asyncio.run(stats_async(lang))


if __name__ == "__main__":
    # Defaults for manually running this script.
    stats(lang="ja")
