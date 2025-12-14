import asyncio
import logging
from pathlib import Path

import aiohttp
from deepdiff.diff import DeepDiff

from lingq.lingqhandler import LingqHandler

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MOCK_APATH = Path("tests/fixtures/audios/10-seconds-of-silence.mp3")
TMPNAME = "__tmp"
# I don't know... LingQ is so slow these days...
WAIT_SECONDS = 0


def log_start(msg: str) -> None:
    logger.info(f"...{msg}")


def log_success(msg: str) -> None:
    logger.info(msg)


def test_handler() -> None:
    """Test the LingQ handler.

    NOTE: This is user dependent!
          Uses the german library since I do not have much there.
    """
    log_start("Starting test_pipeline")

    # Test get_user_langs
    test_lc = "de"
    langs = LingqHandler.get_user_langs()
    assert test_lc in langs
    logger.debug(f"User language codes: {langs}")

    asyncio.run(run_handler(test_lc))


async def quick_test(lang: str) -> None:
    """Course creation / deletion."""
    async with LingqHandler(lang) as handler:
        log_start("Testing course creation")
        responses = await asyncio.gather(
            handler.create_course(f"{TMPNAME}_create1"),
            handler.create_course(f"{TMPNAME}_create2", ""),
            handler.create_course(f"{TMPNAME}_create3", "long_description"),
            handler._create_course({"title": f"{TMPNAME}_create4"}),
        )
        course_ids = [r["id"] for r in responses]
        log_success(f"Created courses with {course_ids=}")
        log_start("Testing course deletion")
        # If delete_course fails, a RuntimeError would be raised inside the function.
        await asyncio.gather(*[handler.delete_course(cid) for cid in course_ids])
        log_success("Quick test passed")


async def run_handler(lang: str) -> None:
    await quick_test(lang)

    async with LingqHandler(lang) as handler:
        # 1.1 Create a course
        log_start("Creating new course")
        jres = await handler.create_course(TMPNAME)
        course_id = jres["id"]
        log_success(f"Created course with ID: {course_id}")
        await asyncio.sleep(WAIT_SECONDS)

        # 1.2. Check that there are no lessons
        log_start(f"Checking lessons in course {course_id}")
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert not clessons
        log_success(f"Course {course_id} has no lessons")

        # 2.1. Upload one lesson
        # https://www.lingq.com/apidocs/api-2.0.html#post
        log_start(f"Uploading lesson to course {course_id}")
        lesson1_text = "Hello, world!"
        data = {
            "title": "lesson1",
            "text": lesson1_text,
            "collection": str(course_id),
            "save": "true",
        }
        posted_lesson = await handler.post_from_data_dict(data)
        await asyncio.sleep(WAIT_SECONDS)

        # 2.2. Check that we have one lesson now
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert len(clessons) == 1
        log_success(f"One lesson uploaded to course {course_id}")

        # 2.3. Open the lesson to place it at the top of "Continue Studying"
        lesson_id = posted_lesson["id"]
        _ = await handler.get_lesson_from_id(lesson_id)
        log_success(f"Opened lesson with ID: {lesson_id}")

        # 2.4 Upload another lesson with audio, this time with post_from_multipart
        log_start("Uploading second lesson with audio")
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
        await asyncio.sleep(WAIT_SECONDS)

        # 2.5. Check that we have two lessons now
        log_start(f"Checking lessons in course {course_id}")
        clessons = await handler.get_collection_lessons_from_id(course_id)
        assert len(clessons) == 2
        log_success(f"Two lessons uploaded to course {course_id}")

        # 3.1. Getting lessons
        log_start("Getting lessons")
        lesson1, lesson2 = clessons
        l1_by_id, (l1, l2) = await asyncio.gather(
            handler.get_lesson_from_id(lesson1.id),
            handler.get_lesson_from_ids([lesson1.id, lesson2.id]),
        )
        diff = DeepDiff(l1, l1_by_id, ignore_order=True, exclude_paths=["root['lastOpenTime']"])
        assert diff == {}, f"JSON mismatch: {diff}"

        # 4.1. Audio testing
        log_start("Checking that only the second lesson has audio")
        assert l1.audio_url is None
        assert l2.audio_url is not None

        log_start("Getting audios")
        audio1, audio2 = await asyncio.gather(
            handler.get_audio_from_lesson(l1),
            handler.get_audio_from_lesson(l2),
        )
        assert audio1 is None
        assert audio2 is not None

        # 5.1. Patch methods
        log_start("Testing patch text")
        raw_text = l1.get_raw_text()
        assert raw_text == lesson1_text, f"'{raw_text}'"
        new_text = "Bye, world!"
        await handler.patch_text(l1.id, new_text)
        l1 = await handler.get_lesson_from_id(l1.id)  # Update l1
        raw_text = l1.get_raw_text()
        assert raw_text == new_text, f"'{raw_text}'"

        # 5.2. Replace title (act. a POST request)
        log_start("Testing patch text (replace title)")
        new_title = "1. lesson1"
        await handler.replace_title(l1.id, new_title)
        l1 = await handler.get_lesson_from_id(l1.id)  # Update l1
        assert l1.title == new_title, f"'{l1.title}'"

        # 5.3. Add audio to the first lesson
        log_start("Patching audio of the first lesson")
        await handler.patch_audio(l1.id, MOCK_APATH.open("rb"))
        l1 = await handler.get_lesson_from_id(l1.id)
        assert l1.audio_url is not None

        # 6.1. Add timestamps
        # Note that this test depends on the length of MOCK_APATH
        # (and also library versions, so it's probably better to skip it)
        #
        # log_start("Adding timestamps to the first lesson")
        # await handler.generate_timestamps(l1.id)
        # l1 = await handler.get_lesson_from_id(l1.id)
        # expected = "WEBVTT\n\n1\n00:00:05.030 --> 00:00:10.000\nBye, world!\n"
        # assert l1.to_vtt() == expected

        # 7.1. Clean up
        log_start(f"Waiting {WAIT_SECONDS} seconds before deleting course")
        await asyncio.sleep(WAIT_SECONDS)
        await handler.delete_course(course_id)
        log_success("Course deleted")

        # 7.2. Delete every temporary course
        log_start("Cleaning all temporary courses")
        await asyncio.sleep(WAIT_SECONDS)
        my_collections = await handler.get_my_collections()
        to_delete = [r for r in my_collections.results if TMPNAME in r.title]
        log_start(f"Deleting extra {len(to_delete)} temporary courses")
        await asyncio.gather(*(handler.delete_course(result.id) for result in to_delete))

    log_success("✅ Passed all tests")


if __name__ == "__main__":
    test_handler()
