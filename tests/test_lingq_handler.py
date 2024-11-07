import asyncio
import logging
from pathlib import Path

import aiohttp
from deepdiff import DeepDiff

from lingqhandler import LingqHandler

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MOCK_APATH = Path("tests/fixtures/audios/10-seconds-of-silence.mp3")


def test_handler() -> None:
    """NOTE: This is user dependent!"""
    logger.info("Starting test_pipeline")

    # Test get_user_language_codes
    test_lc = "de"
    language_codes = LingqHandler.get_user_language_codes()
    assert test_lc in language_codes
    logger.debug(f"User language codes: {language_codes}")

    asyncio.run(run_handler(test_lc))


async def run_handler(language_code: str) -> None:
    tmpname = "__tmp"

    async with LingqHandler(language_code) as handler:
        # await handler.get_languages()
        # await handler._get_user_language_codes()

        # 1.1.1 Course creation / deletion
        logger.info("Testing course creation")
        responses = await asyncio.gather(
            handler.create_course(f"{tmpname}_create"),
            handler.create_course(f"{tmpname}_create2", ""),
            handler.create_course(f"{tmpname}_create3", "long_description"),
            handler._create_course({"title": f"{tmpname}_create4"}),
        )
        course_ids = [r["id"] for r in responses]
        logger.info(f"Created courses with {course_ids=}")
        logger.info("Testing course deletion")
        await asyncio.gather(*[handler.delete_course(cid) for cid in course_ids])

        # 1.1.2 Create a course
        logger.info("Creating new course")
        jres = await handler.create_course(tmpname)
        course_id = jres["id"]
        logger.info(f"Created course with ID: {course_id}")

        # 1.2. Check that there are no lessons
        logger.info(f"Checking lessons in course {course_id}")
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert not clessons
        logger.info(f"Course {course_id} has no lessons")

        # 2.1. Upload one lesson
        # https://www.lingq.com/apidocs/api-2.0.html#post
        logger.info(f"Uploading lesson to course {course_id}")
        data = {
            "title": "lesson2",
            "text": "Hello, world!",
            "collection": str(course_id),
            "save": "true",
        }
        posted_lesson = await handler.post_from_data_dict(data)

        # 2.2. Check that we have one lesson now
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert len(clessons) == 1
        logger.info(f"One lesson uploaded to course {course_id}")

        # 2.3. Open the lesson to place it at the top of "Continue Studying"
        lesson_id = posted_lesson["id"]
        _ = await handler.get_lesson_from_id(lesson_id)
        logger.info(f"Opened lesson with ID: {lesson_id}")

        # 2.4 Upload another lesson with audio, this time with post_from_multipart
        logger.info("Uploading second lesson with audio")
        data = {
            "title": "lesson2",
            "text": "Hello, world!",
            "collection": str(course_id),
            "save": "true",
        }
        fdata = aiohttp.FormData(data)
        mock_audio = MOCK_APATH.open("rb")
        fdata.add_field("audio", mock_audio, filename="audio.mp3", content_type="audio/mpeg")
        await handler.post_from_multipart(fdata)

        # 2.5. Check that we have two lessons now
        logger.info(f"Checking lessons in course {course_id}")
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert len(clessons) == 2
        logger.info(f"Two lessons uploaded to course {course_id}")

        # 3.1. Getting lessons
        logger.info("Getting lessons")
        lesson1, lesson2 = clessons
        l1_by_url, l1_by_id, (l1, l2) = await asyncio.gather(
            handler.get_lesson_from_id(lesson1.id),
            handler.get_lesson_from_id(lesson1.id),
            handler.get_lesson_from_ids([lesson1.id, lesson2.id]),
        )
        diff = DeepDiff(
            l1_by_url, l1_by_id, ignore_order=True, exclude_paths=["root['lastOpenTime']"]
        )
        assert diff == {}, f"JSON mismatch: {diff}"

        # 4.1. Audio testing
        logger.info("Checking that only the second lesson has audio...")
        assert l1.audio_url is None
        assert l2.audio_url is not None

        logger.info("Getting audios")
        audio1, audio2 = await asyncio.gather(
            handler.get_audio_from_lesson(l1),
            handler.get_audio_from_lesson(l2),
        )
        assert audio1 is None
        assert audio2 is not None

        # 5.1. Patch methods
        logger.info("Testing patch text")
        raw_text = l1.get_raw_text()
        assert raw_text == "Hello, world!", f"'{raw_text}'"
        new_text = "Bye, world!"
        await handler.patch_text(l1.id, new_text)
        l1 = await handler.get_lesson_from_id(l1.id)  # Update l1
        raw_text = l1.get_raw_text()
        assert raw_text == new_text, f"'{raw_text}'"

        # 5.2. Add audio to the first lesson
        logger.info("Patching audio of the first lesson")
        await handler.patch_audio(l1.id, MOCK_APATH.open("rb"))
        l1 = await handler.get_lesson_from_id(l2.id)
        assert l1.audio_url is not None

        # 6.1. Clean up
        logger.info("Waiting 5 seconds before deleting course")
        await asyncio.sleep(5)
        await handler.delete_course(course_id)
        logger.info("Course deleted")

        # 6.2. Delete every temporary course
        logger.info("Cleaning all temporary courses")
        await asyncio.sleep(2)
        my_collections = await handler.get_my_collections()
        to_delete = [r for r in my_collections.results if tmpname in r.title]
        logger.info(f"Deleting extra {len(to_delete)} temporary courses")
        await asyncio.gather(*(handler.delete_course(result.id) for result in to_delete))

    logging.info("Passed all tests")


if __name__ == "__main__":
    test_handler()
