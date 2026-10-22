import csv
import io
from pathlib import Path
import tempfile
import unittest

from assessment import CSV_COLUMNS, Session, assignment_for, load_videos


class AssessmentTests(unittest.TestCase):
    def session(self, name="P01", group=1, part=1, videos=None):
        self.tick = 10.0
        return Session(name, group, part, videos or load_videos(),
                       clock=lambda: self.tick, timestamp=lambda: "2026-10-22T14:00:00.000Z")

    def complete(self, session):
        for index in range(session.current_index, len(session.questions)):
            session.select(index % 4)
            self.tick += 1
            if index < len(session.questions) - 1:
                session.go_to(index + 1)
        session.finish()

    def test_assignments_match_existing_counterbalancing(self):
        expected = {
            1: (("A", "Fidget toy"), ("B", "No fidget toy")),
            2: (("A", "No fidget toy"), ("B", "Fidget toy")),
            3: (("B", "Fidget toy"), ("A", "No fidget toy")),
            4: (("B", "No fidget toy"), ("A", "Fidget toy")),
        }
        for group, assignments in expected.items():
            self.assertEqual(tuple(assignment_for(group, part) for part in (1, 2)), assignments)
        for group, part in ((0, 1), (1, 3), (True, 1), (1, None)):
            with self.assertRaises(ValueError):
                assignment_for(group, part)

    def test_timing_accumulates_reviews_and_freezes_on_submit(self):
        session = self.session()
        self.tick += 1.5
        session.select(0)
        session.go_to(1)
        self.tick += 2.25
        session.select(1)
        session.go_to(0)
        self.tick += 0.75
        session.select(3)
        session.go_to(1)
        self.complete(session)
        self.assertEqual(session.answers[0], 3)
        self.assertEqual(session.question_times[0], 2.25)
        self.assertEqual(session.question_times[1], 3.25)
        self.assertEqual(sum(session.question_times), session.total_seconds)
        csv_before = session.to_csv()
        self.tick += 10
        session.finish()
        self.assertEqual(session.to_csv(), csv_before)
        with self.assertRaisesRegex(ValueError, "already complete"):
            session.select(0)

    def test_csv_matches_the_existing_schema_and_quotes_text(self):
        videos = load_videos()
        videos[0]["questions"][0]["prompt"] = 'A question, with "quotes"\nand a newline'
        videos[0]["questions"][0]["answers"][0] = " =2+2"
        session = self.session(name="=P01", group=2, videos=videos)
        self.complete(session)
        data = session.to_csv()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
        rows = list(reader)
        self.assertEqual(tuple(reader.fieldnames), CSV_COLUMNS)
        self.assertEqual(len(rows), 10)
        first = rows[0]
        self.assertEqual(first["taker_name"], "'=P01")
        self.assertEqual(first["question_text"], videos[0]["questions"][0]["prompt"])
        self.assertEqual(first["option_a"], "' =2+2")
        self.assertEqual(first["answer_text"], "' =2+2")
        self.assertEqual(first["answer_letter"], "A")
        self.assertEqual(first["condition"], "No fidget toy")
        self.assertEqual(first["total_time_seconds"], "10.000")
        self.assertEqual(first["question_time_seconds"], "1.000")
        self.assertTrue(all(row["run_id"] == session.run_id for row in rows))

    def test_incomplete_and_blank_quizzes_cannot_submit(self):
        session = self.session()
        for action in (session.finish, session.to_csv):
            with self.assertRaises(ValueError):
                action()
        for answer in (4, -1, 1.5, True):
            with self.assertRaises(ValueError):
                session.select(answer)
        with self.assertRaisesRegex(ValueError, "not ready"):
            self.session(group=3)
        with self.assertRaises(ValueError):
            self.session(name="  ")

    def test_filenames_are_unique_and_fit_filesystem_limits(self):
        session = self.session(name='../Zoë 李:Study?')
        self.assertNotIn("/", session.filename)
        self.assertNotIn(":", session.filename)
        self.assertIn("Zoë 李", session.filename)
        self.assertNotEqual(session.filename, self.session(name=session.name).filename)
        self.assertLess(len(self.session(name="李" * 120).filename.encode("utf-8")), 255)

    def test_malformed_question_bank_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "questions.json"
            for data in ('{}', '[{}]', '[{}, {}]'):
                path.write_text(data)
                with self.assertRaises(ValueError):
                    load_videos(path)


if __name__ == "__main__":
    unittest.main()
