import asyncio

from lingqhandler import LingqHandler


async def get_my_collections_titles_async(
    lang: str, shared_only: bool, codes: bool
) -> list[str]:
    async with LingqHandler(lang) as handler:
        if not shared_only:
            my_collections = await handler.get_my_collections()
            collections = my_collections.results
        else:
            collections = await handler.get_my_collections_shared()

        titles = []
        for col in collections:
            if not codes:
                title = col.title
            else:
                title = f"{col.id:>7} {col.title}"
            titles.append(title)

        return titles


def show_my(lang: str, shared_only: bool, codes: bool) -> None:
    """Show a list with my collections in the given language."""
    titles = asyncio.run(get_my_collections_titles_async(lang, shared_only, codes))
    for idx, title in enumerate(titles, 1):
        print(f"{idx:02}: {title}")


if __name__ == "__main__":
    show_my(lang="de", shared_only=True, codes=False)
