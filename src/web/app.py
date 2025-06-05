import json
from typing import List, Tuple

from pydantic import BaseModel
import streamlit as st
from semantic_kernel.contents import (ChatMessageContent, ImageContent,
                                      TextContent, StreamingAnnotationContent,
                                      StreamingFileReferenceContent, StreamingTextContent,)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

from models.chat_output import deserialize_chat_output
from models.streaming_annotation_file_output import deserialize_streaming_annotation_file_output
from models.streaming_annotation_url_output import deserialize_streaming_annotation_url_output
from models.streaming_text_output import deserialize_streaming_text_output
from models.content_type_enum import ContentTypeEnum
from models.streaming_annotation_file_output import StreamingAnnotationFileOutput
from models.streaming_annotation_url_output import StreamingAnnotationUrlOutput
from services.chat import chat, create_thread, get_image
from utilities import replace_annotation_placeholder


def _handle_user_interaction():
    st.session_state["waiting_for_response"] = True


if "waiting_for_response" not in st.session_state:
    st.session_state["waiting_for_response"] = False

st.set_page_config(
    page_title="AI Assistant",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

with open('assets/css/style.css', encoding='utf-8') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# st.image("assets/images/aks.svg", width=192)
st.title("AI Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = ChatHistory()

if "thread_id" not in st.session_state:
    with st.spinner("Creating thread..."):
        thread_id = create_thread()
        st.session_state.thread_id = thread_id

def render_response(response):
    full_stream_content = ""
    individual_stream_content = ""

    class QuoteUrls(BaseModel):
        quote: str = ""
        url: str = ""

    quote_urls: List[QuoteUrls] = []  # List to store URL annotations

    images = []
    for chunk in response:
        delta = deserialize_chat_output(json.loads(chunk))

        match delta.content_type:
            case ContentTypeEnum.MARKDOWN:
                output = deserialize_streaming_text_output(json.loads(chunk))
                full_stream_content += output.text
                individual_stream_content += output.text

                st.markdown(full_stream_content)
            # case ContentTypeEnum.FILE:
            #     output = deserialize_streaming_annotation_file_output(json.loads(chunk))
            #     streaming_file_content = StreamingFileReferenceContent(file_id=output.file_id)
            #     file_id = streaming_file_content.file_id
            #     image = get_image(file_id=file_id)
            #     st.image(image=image, use_container_width=True)
            #     images.append(image)

            case ContentTypeEnum.ANNOTATION_FILE:
                output = deserialize_streaming_annotation_file_output(json.loads(chunk))

                streaming_annotation_content = StreamingAnnotationFileOutput(
                    content_type=ContentTypeEnum.ANNOTATION_FILE,
                    thread_id=st.session_state.thread_id,
                    file_id=output.file_id,
                    quote=output.quote,
                    start_index=output.start_index,
                    end_index=output.end_index,
                )

                individual_stream_content = str.replace(individual_stream_content,
                                                        streaming_annotation_content.quote,
                                                        f"([{streaming_annotation_content.file_id}]({streaming_annotation_content.file_id}))")

            case ContentTypeEnum.ANNOTATION_URL:
                output = deserialize_streaming_annotation_url_output(json.loads(chunk))

                streaming_annotation_content = StreamingAnnotationUrlOutput(
                    content_type=ContentTypeEnum.ANNOTATION_URL,
                    thread_id=st.session_state.thread_id,
                    url=output.url,
                    title=output.title,
                    quote=output.quote,
                    start_index=output.start_index,
                    end_index=output.end_index,
                )

                individual_stream_content = str.replace(individual_stream_content,
                                                        streaming_annotation_content.quote,
                                                        f"([{streaming_annotation_content.title}]({streaming_annotation_content.url}))")

            case ContentTypeEnum.SENTINEL:
                st.markdown(full_stream_content)

                updated_stream_content = individual_stream_content

                st.session_state.messages.add_assistant_message(updated_stream_content)
                individual_stream_content = ""

    for image in images:
        content = ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[
                ImageContent(data=image)
            ]
        )
        st.session_state.messages.add_message(content)


@st.fragment
def response(question):
    # Display assistant response in chat message container
    with st.chat_message(AuthorRole.ASSISTANT):
        with st.spinner("Reticulating splines..."):
            response = chat(thread_id=st.session_state.thread_id,
                            content=question)

            with st.empty():
                render_response(response)


@st.fragment
def display_chat_history():
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            for item in message.items:
                if isinstance(item, TextContent):
                    st.write(item.text)
                elif isinstance(item, ImageContent):
                    st.image(item.data, use_container_width=True)
                else:
                    raise TypeError(f"Unknown content type: {type(item)}")


if "thread_id" in st.session_state:
    with st.sidebar:
        st.subheader(body="Thread ID", divider=True)
        st.write(st.session_state.thread_id)

    display_chat_history()

    if question := st.chat_input(
        placeholder="Enter the name of the Azure service you wish to generate recommendations for...",
        on_submit=_handle_user_interaction,
        disabled=st.session_state["waiting_for_response"],
    ):
        # Add user message to chat history
        st.session_state.messages.add_user_message(question)
        # Display user message in chat message container
        with st.chat_message(AuthorRole.USER):
            st.markdown(question)

        response(question)

if st.session_state["waiting_for_response"]:
    st.session_state["waiting_for_response"] = False
    st.rerun()
