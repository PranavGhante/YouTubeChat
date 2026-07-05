import unittest

from app.chunking import chunk_transcript
from app.schemas import TranscriptEntry


class ChunkingTest(unittest.TestCase):
    def test_chunks_preserve_timestamp_ranges(self):
        transcript = [
            TranscriptEntry(
                text="alpha beta gamma",
                start=0.0,
                duration=2.0,
                end=2.0,
                timestamp="00:00",
            ),
            TranscriptEntry(
                text="delta epsilon zeta",
                start=2.0,
                duration=2.0,
                end=4.0,
                timestamp="00:02",
            ),
            TranscriptEntry(
                text="eta theta iota",
                start=4.0,
                duration=2.0,
                end=6.0,
                timestamp="00:04",
            ),
        ]

        chunks = chunk_transcript(
            "dQw4w9WgXcQ",
            transcript,
            max_words=6,
            overlap_words=3,
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].start, 0.0)
        self.assertEqual(chunks[0].end, 4.0)
        self.assertEqual(chunks[0].start_timestamp, "00:00")
        self.assertEqual(chunks[0].end_timestamp, "00:04")
        self.assertEqual(chunks[1].start, 2.0)
        self.assertEqual(chunks[1].end, 6.0)
        self.assertIn("delta epsilon zeta", chunks[1].text)


if __name__ == "__main__":
    unittest.main()
