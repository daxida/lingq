import asyncio

from lingqhandler import LingqHandler


async def get_my_collections_titles_async(language_code: str) -> list[str]:
    async with LingqHandler(language_code) as handler:
        my_collections = await handler.get_my_collections()
        return [col["title"] for col in my_collections]


def show_my(language_code: str) -> None:
    """Show a list with my collections in the given language."""
    titles = asyncio.run(get_my_collections_titles_async(language_code))
    for idx, title in enumerate(titles, 1):
        print(f"{idx:02}: {title}")


if __name__ == "__main__":
    show_my(language_code="de")
