import unittest

from app.youtube import InvalidYouTubeUrlError, extract_video_id, format_timestamp


class YouTubeHelpersTest(unittest.TestCase):
    def test_extracts_video_id_from_watch_url(self):
        self.assertEqual(
            extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extracts_video_id_from_short_url(self):
        self.assertEqual(
            extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=45"),
            "dQw4w9WgXcQ",
        )

    def test_extracts_video_id_from_embed_url(self):
        self.assertEqual(
            extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_rejects_non_youtube_url(self):
        with self.assertRaises(InvalidYouTubeUrlError):
            extract_video_id("https://example.com/watch?v=dQw4w9WgXcQ")

    def test_formats_timestamp_under_one_hour(self):
        self.assertEqual(format_timestamp(12.4), "00:12")
        self.assertEqual(format_timestamp(754.2), "12:34")

    def test_formats_timestamp_over_one_hour(self):
        self.assertEqual(format_timestamp(3723.8), "01:02:03")


if __name__ == "__main__":
    unittest.main()
