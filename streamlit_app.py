"""Run with: streamlit run streamlit_app.py."""

import logging

import streamlit as st
from streamlit.errors import StreamlitAPIException, StreamlitSecretNotFoundError

from assessment import LETTERS, Session, assignment_for, load_videos, video_ready
from response_storage import StorageError, build_storage


logger = logging.getLogger(__name__)


def reset_assessment():
    for key in list(st.session_state):
        if key.startswith("answer_") or key in ("assessment", "participant_details", "save_path", "save_error"):
            del st.session_state[key]
    st.session_state.participant = ""
    st.session_state.group = None


def edit_participant():
    details = st.session_state.pop("participant_details")
    st.session_state.participant = details["name"]
    st.session_state.group = details["group"]


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
    st.write("Watch one short video, then answer 10 questions at your own pace.")
    st.caption("Enter the participant ID and confirm the group with the researcher.")
    ready = video_ready(videos[0])
    if not ready:
        st.warning("The quiz is not ready. Please ask the researcher for help.")
    with st.form("participant_setup"):
        name = st.text_input("Participant ID or name", max_chars=120, key="participant",
                             placeholder="For example, P01")
        group = st.selectbox("Participant group", (1, 2), index=None,
                             format_func=lambda value: f"Group {value}", key="group")
        st.caption("Group 1: fidget toy while watching · Group 2: no fidget toy")
        submitted = st.form_submit_button("Continue to video", type="primary",
                                          disabled=not (ready and storage_ready), key="continue")
    if submitted:
        if not name.strip():
            st.error("Enter a participant ID or name.")
        elif group is None:
            st.error("Choose participant group 1 or 2.")
        else:
            st.session_state.participant_details = {"name": name.strip(), "group": group}
            st.rerun()


def video_screen(videos, storage_ready):
    video = videos[0]
    details = st.session_state.participant_details
    _, condition = assignment_for(details["group"])
    st.title("Watch the video.")
    st.caption(f"{details['name']} · Group {details['group']} · {condition}")
    st.subheader(video["title"])
    st.iframe(video["embed_url"], height=400, alt="Study video: The surprising reasons animals play dead")
    st.write("Watch the entire video here. When it finishes, let the researcher know you're ready for the quiz.")
    st.caption("Return the fidget toy before beginning the quiz if you were given one. Quiz timing starts only when you press Begin assessment.")
    if st.button("Begin assessment", type="primary", disabled=not storage_ready, key="begin"):
        try:
            st.session_state.assessment = Session(details["name"], details["group"], videos)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()
    st.button("Back to participant details", on_click=edit_participant, key="edit_participant")


def question_screen(session):
    index = session.current_index
    question = session.questions[index]
    count = len(session.questions)
    st.caption(f"{session.name} · Group {session.group} · Quiz A · {session.condition}")
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
    st.caption(f"Group {session.group} · Quiz A · {session.condition}")
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
    except StreamlitAPIException:
        st.error("The app's Secrets settings contain invalid TOML. Please ask the researcher to correct them.")
        st.stop()
    storage = None
    try:
        storage = build_storage(secrets)
    except StorageError as error:
        logger.warning("Response storage configuration: %s", error)
        st.error("Response storage is not configured. Please ask the researcher to update the app's Secrets.")
        with st.expander("Researcher setup details"):
            st.write(str(error))
            st.write("Open the deployed app's Settings → Secrets, add the [github] token, then save and reload.")
            st.markdown("[Streamlit Secrets setup](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)")
    session = st.session_state.get("assessment")
    if session is None and "participant_details" not in st.session_state:
        start_screen(videos, storage is not None)
    elif session is None:
        video_screen(videos, storage is not None)
    elif session.completed_at:
        completion_screen(session, storage)
    else:
        question_screen(session)


if __name__ == "__main__":
    main()
