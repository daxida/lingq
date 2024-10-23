import asyncio
import logging
from pathlib import Path

import aiohttp
from deepdiff import DeepDiff

from lingqhandler import LingqHandler

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_pipeline():
    """NOTE: This is user dependent!"""
    logger.info("Starting test_pipeline")

    # Test get_user_language_codes
    test_lc = "de"
    language_codes = LingqHandler.get_user_language_codes()
    assert test_lc in language_codes
    logger.debug(f"User language codes: {language_codes}")

    asyncio.run(_test_pipeline(test_lc))


async def _test_pipeline(language_code):
    async with LingqHandler(language_code) as handler:
        # await handler.get_languages()
        # await handler._get_user_language_codes()

        # 1.1.1 Course creation / deletion
        logger.info("Testing course creation")
        responses = await asyncio.gather(
            handler.create_course("test_create"),
            handler.create_course("test_create2", ""),
            handler.create_course("test_create3", "long_description"),
            handler._create_course({"title": "test_create4"}),
        )
        course_ids = [r["id"] for r in responses]
        logger.info(f"Created courses with {course_ids=}")
        logger.info("Testing course deletion")
        await asyncio.gather(*[handler.delete_course(cid) for cid in course_ids])

        # 1.1.2 Create a course
        logger.info("Creating new course")
        jres = await handler.create_course("tmp")
        course_id = jres["id"]
        logger.info(f"Created course with ID: {course_id}")

        # 1.2. Check that there are no lessons
        logger.info(f"Checking lessons in course {course_id}")
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert not collection_json["lessons"]
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
        post_res = await handler.post_from_data_dict(data)

        # 2.2. Check that we have one lesson now
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert len(collection_json["lessons"]) == 1
        logger.info(f"One lesson uploaded to course {course_id}")

        # 2.3. Open the lesson to place it at the top of "Continue Studying"
        json_res = await post_res.json()
        lesson_id = json_res["id"]
        _ = await handler.get_lesson_from_id(lesson_id)
        logger.info(f"Opened lesson with ID: {lesson_id}")

        # 2.4.1 Upload another lesson with audio, this time with post_from_multipart
        logger.info("Uploading second lesson with audio")
        data = {
            "title": "lesson2",
            "text": "Hello, world!",
            "collection": str(course_id),
            "save": "true",
        }
        fdata = aiohttp.FormData()
        for key, value in data.items():
            fdata.add_field(key, value)
        mock_audio = Path("tests/fixtures/audios/10-seconds-of-silence.mp3").open("rb")
        fdata.add_field("audio", mock_audio, filename="audio.mp3", content_type="audio/mpeg")
        post_res = await handler.post_from_multipart(fdata)

        # 2.5. Check that we have two lessons now
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert len(collection_json["lessons"]) == 2
        logger.info(f"Two lessons uploaded to course {course_id}")

        # 3.1. Getting lessons
        logger.info("Getting lessons")
        lessons = collection_json["lessons"]
        lesson1, lesson2 = lessons
        l1_by_url, l1_by_id, (l1, l2) = await asyncio.gather(
            handler.get_lesson_from_url(lesson1["url"]),
            handler.get_lesson_from_id(lesson1["id"]),
            handler.get_lessons_from_urls([lesson1["url"], lesson2["url"]]),
        )
        diff = DeepDiff(
            l1_by_url, l1_by_id, ignore_order=True, exclude_paths=["root['lastOpenTime']"]
        )
        assert diff == {}, f"JSON mismatch: {diff}"

        # 4.1. Audio testing
        logger.info("Checking that only the second lesson has audio...")
        assert l1["audioUrl"] is None
        assert l2["audioUrl"] is not None

        logger.info("Getting audios")
        audio1, audio2 = await asyncio.gather(
            handler.get_audio_from_lesson(l1),
            handler.get_audio_from_lesson(l2),
        )
        assert audio1 is None
        assert audio2 is not None

        logger.info("Waiting 5 seconds before deleting course")
        await asyncio.sleep(5)
        await handler.delete_course(course_id)
        logger.info("Course deleted")

    logging.info("Passed all tests")


test_pipeline()
