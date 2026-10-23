import csv
import io
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from assessment import ROOT
from response_storage import LocalStorage, StorageError


class StreamlitAppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.storage = LocalStorage(self.directory.name)
        self.patch = patch("response_storage.build_storage", return_value=self.storage)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def watch(self, name="P01", group=1):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=10).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.selectbox), 1)
        self.assertEqual(app.selectbox(key="group").options, ["Group 1", "Group 2"])
        app.text_input(key="participant").set_value(name)
        app.selectbox(key="group").select(group)
        app.button(key="continue").click().run()
        self.assertFalse(app.exception)
        return app

    def start(self, name="P01", group=1):
        app = self.watch(name, group)
        app.button(key="begin").click().run()
        self.assertFalse(app.exception)
        return app

    def finish(self, app, answer=0):
        while app.radio:
            app.radio[0].set_value(answer)
            app.button[-1].click().run()
            self.assertFalse(app.exception)

    def test_full_quiz_saves_raw_csv_and_reruns_do_not_duplicate(self):
        app = self.start(group=2)
        self.assertIsNone(app.radio[0].value)
        app.button[-1].click().run()
        self.assertEqual(app.subheader[0].value, "Question 1 of 10")
        app.radio[0].set_value(1)
        app.button[-1].click().run()
        app.radio[0].set_value(2)
        app.button[0].click().run()
        self.assertEqual(app.radio[0].value, 1)
        app.radio[0].set_value(3)
        app.button[-1].click().run()
        self.assertEqual(app.radio[0].value, 2)
        self.finish(app, answer=2)
        self.assertTrue(app.success)
        files = list(self.storage.directory.glob("*.csv"))
        self.assertEqual(len(files), 1)
        data = files[0].read_bytes()
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["answer_letter"], "D")
        self.assertEqual(rows[1]["answer_letter"], "C")
        self.assertEqual(rows[0]["condition"], "No fidget toy")
        app.run()
        self.assertEqual(list(self.storage.directory.glob("*.csv")), files)
        self.assertEqual(files[0].read_bytes(), data)
        self.assertNotIn("next_quiz", [button.key for button in app.button])
        app.button(key="restart").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="participant").value, "")
        self.assertIsNone(app.selectbox(key="group").value)

    def test_failed_save_retains_the_run_and_retry_saves_once(self):
        app = self.start()
        with patch.object(self.storage, "save", side_effect=StorageError("offline")):
            self.finish(app)
        self.assertTrue(app.error)
        self.assertTrue(app.button(key="restart").disabled)
        original_csv = app.session_state.assessment.to_csv()
        app.button(key="retry").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.success)
        files = list(self.storage.directory.glob("*.csv"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_bytes(), original_csv)

    def test_embedded_video_precedes_quiz_and_is_not_timed(self):
        app = self.watch()
        self.assertEqual(app.title[0].value, "Watch the video.")
        self.assertNotIn("assessment", app.session_state)
        self.assertEqual(len(app.get("iframe")), 1)
        self.assertIn("embed.ted.com/talks/tierney_thys", app.get("iframe")[0].proto.src)
        app.button(key="edit_participant").click().run()
        self.assertEqual(app.text_input(key="participant").value, "P01")
        self.assertEqual(app.selectbox(key="group").value, 1)
        app.button(key="continue").click().run()
        app.button(key="begin").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.get("iframe"))
        self.assertEqual(app.session_state.assessment.video_id, "A")
        self.assertEqual(app.session_state.assessment.part, 1)

    def test_participant_sessions_are_isolated(self):
        first = self.start("P01")
        second = self.start("P02", group=2)
        self.finish(first, answer=1)
        self.assertIsNone(second.radio[0].value)
        self.finish(second, answer=3)
        files = list(self.storage.directory.glob("*.csv"))
        self.assertEqual(len(files), 2)
        rows = [next(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig")))) for path in files]
        self.assertEqual({(row["taker_name"], row["answer_letter"]) for row in rows}, {("P01", "B"), ("P02", "D")})
        self.assertEqual(len({row["run_id"] for row in rows}), 2)

    def test_unconfigured_storage_blocks_collection(self):
        with patch("response_storage.build_storage", side_effect=StorageError("missing token")):
            app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run()
            app.selectbox(key="group").select(1).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertTrue(app.button(key="continue").disabled)


if __name__ == "__main__":
    unittest.main()
