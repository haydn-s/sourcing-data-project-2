"""Run with: streamlit run streamlit_app.py."""

import logging

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from assessment import LETTERS, Session, assignment_for, load_videos, video_ready
from response_storage import StorageError, build_storage


logger = logging.getLogger(__name__)


def reset_assessment(*, next_quiz=False):
    session = st.session_state.get("assessment")
    for key in list(st.session_state):
        if key.startswith("answer_") or key in ("assessment", "save_path", "save_error"):
            del st.session_state[key]
    st.session_state.participant = session.name if next_quiz else ""
    st.session_state.group = session.group if next_quiz else None
    st.session_state.part = 2 if next_quiz else None


def navigate(direction):
    session = st.session_state.assessment
    answer = st.session_state.get(f"answer_{session.current_index}")
    if answer is not None:
        session.select(answer)
    if direction == -1:
        session.go_to(session.current_index - 1)
    elif answer is not None:
        if session.current_index < len(session.questions) - 1:
            session.go_to(session.current_index + 1)
        else:
            session.finish()


def start_screen(videos, storage_ready):
    st.title("Ready when you are.")
    st.write("A little focus. One question at a time. Take the quiz for the video you watched.")
    st.caption("Enter the participant ID and confirm the group and quiz with the researcher.")
    name = st.text_input("Participant ID or name", max_chars=120, key="participant",
                         placeholder="For example, P01")
    left, right = st.columns(2)
    group = left.selectbox("Participant group", (1, 2, 3, 4), index=None,
                           format_func=lambda value: f"Group {value}", key="group")
    part = right.selectbox("Which quiz", (1, 2), index=None,
                          format_func=lambda value: "First" if value == 1 else "Second", key="part")
    ready = False
    if group is not None and part is not None:
        video_id, condition = assignment_for(group, part)
        video = next(v for v in videos if v["id"] == video_id)
        with st.container(border=True):
            st.write(f"**Video {video_id}** · {video['title']}")
            st.write(f"**Condition:** {condition}")
            st.caption(f"{len(video['questions'])} questions · 4 choices each")
        ready = video_ready(video)
        if not ready:
            st.warning("This video's quiz is not ready. Please check your assignment with the researcher.")
    st.caption("Timing starts when you press Begin. Work at your own pace. Keep this page open until your results are saved.")
    if st.button("Begin assessment", type="primary", disabled=not (ready and storage_ready), key="begin"):
        try:
            st.session_state.assessment = Session(name, group, part, videos)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()


def question_screen(session):
    index = session.current_index
    question = session.questions[index]
    count = len(session.questions)
    st.caption(f"{session.name} · Group {session.group} · Quiz {session.part} · Video {session.video_id} · {session.condition}")
    st.progress(session.answered_count / count, text=f"{session.answered_count} of {count} answered")
    st.subheader(f"Question {index + 1} of {count}")
    st.write(question["prompt"])
    # Model answers survive Streamlit's cleanup of widgets on other question screens.
    key = f"answer_{index}"
    if key not in st.session_state:
        st.session_state[key] = session.answers[index]
    with st.form(f"question_{index}"):
        st.radio("Choose one answer", range(4), index=None, key=key,
                 format_func=lambda answer: f"{LETTERS[answer]}. {question['answers'][answer]}")
        previous, following = st.columns(2)
        previous.form_submit_button("Previous", disabled=index == 0, on_click=navigate, args=(-1,))
        label = "Submit quiz" if index == count - 1 else "Next question"
        following.form_submit_button(label, type="primary", on_click=navigate, args=(1,))
    st.caption("Select an answer before continuing. Use Previous to review or change an earlier answer.")


def completion_screen(session, storage):
    st.title("Quiz complete.")
    st.write(f"Thank you, {session.name}. You've answered all {len(session.questions)} questions.")
    st.caption(f"Group {session.group} · Quiz {session.part} · Video {session.video_id} · {session.condition}")
    content = session.to_csv()
    if not st.session_state.get("save_path") and not st.session_state.get("save_error"):
        with st.spinner("Saving your results…"):
            try:
                if storage is None:
                    raise StorageError("Response storage is unavailable.")
                st.session_state.save_path = storage.save(session.filename, content)
            except StorageError as error:
                logger.warning("Response save failed: %s", error)
                st.session_state.save_error = True
    saved = bool(st.session_state.get("save_path"))
    if saved:
        st.success("Your results have been saved. You can let the researcher know you're finished.")
    else:
        st.error("Your results haven't been saved yet. Keep this page open and ask the researcher for help, then try again. You can also download a backup below.")
        if st.button("Try saving again", key="retry"):
            st.session_state.pop("save_error", None)
            st.rerun()
    answered, duration = st.columns(2)
    answered.metric("Questions answered", len(session.questions))
    seconds = round(session.total_seconds)
    duration.metric("Total time", f"{seconds // 60}m {seconds % 60:02d}s")
    st.download_button("Download a copy of results", content, session.filename,
                       mime="text/csv", on_click="ignore")
    st.button("Start a new assessment", disabled=not saved, on_click=reset_assessment, key="restart")
    if session.part == 1:
        next_video_id, _ = assignment_for(session.group, 2)
        if video_ready(next(v for v in load_videos() if v["id"] == next_video_id)):
            st.button("Start the next quiz", disabled=not saved,
                      on_click=reset_assessment, kwargs={"next_quiz": True}, key="next_quiz")


def main():
    st.set_page_config(page_title="Study Assessment · AIPI 510", page_icon="◫", layout="centered")
    st.caption("STUDY / ASSESSMENT                                      AIPI 510 · PROJECT 02")
    try:
        videos = load_videos()
    except (OSError, ValueError) as error:
        logger.error("Question bank configuration: %s", error)
        st.error("The assessment isn't ready yet. Please ask the researcher for help.")
        st.stop()
    try:
        secrets = st.secrets.to_dict()
    except StreamlitSecretNotFoundError:
        secrets = {}
    storage = None
    try:
        storage = build_storage(secrets)
    except StorageError as error:
        logger.warning("Response storage configuration: %s", error)
        st.error("The assessment isn't ready yet. Please ask the researcher to finish setting up response storage.")
    session = st.session_state.get("assessment")
    if session is None:
        start_screen(videos, storage is not None)
    elif session.completed_at:
        completion_screen(session, storage)
    else:
        question_screen(session)


if __name__ == "__main__":
    main()
