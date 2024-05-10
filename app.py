import streamlit as st
import cohere
import os
from dotenv import load_dotenv
from BinaryVectorDB import BinaryVectorDB


summarizer_preamble = """\
You'll be working with segments from official documentation, \
Your task is to respond accurately and truthfully to user queries based on these segments. \
"""

instructions = """\
## instructions \
Step 1. If you retrieved from documentation, say 'I found something in documentation' and begin summarizing\
Step 2. Summarize Each Section: After reading, summarize each section concisely and clearly. Make sure to include main points and necessary technical details. \
Step 3. At the end of response, print all the source paths, something like: "python-3.12.3-docs-text/library/functools.txt", "python-3.12.3-docs-text/library/typing.txt" \
"""


load_dotenv(override=True)

model_id = 'command-r'

with st.sidebar:
    st.markdown(
        "Add your Cohere API Key to continue.\n"
        "https://dashboard.cohere.com/api-keys\n"
    )
    COHERE_API_KEY = st.text_input("Cohere API Key", key="chatbot_api_key", type="password")
    on = st.toggle("Search Web")

# COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
co = cohere.Client(api_key=COHERE_API_KEY)

db_folder = "python_docs_db"
db = BinaryVectorDB(folder=db_folder, api_key=COHERE_API_KEY)


st.title("Python documentation Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "message": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["message"])


prompt = st.chat_input()
if prompt:
    if not COHERE_API_KEY:
        st.info("Please add your Cohere API Key to continue.\nhttps://dashboard.cohere.com/api-keys")
        st.stop()

    # input
    st.chat_message("USER").write(prompt)
    st.session_state.messages.append({"role": "USER", "message": prompt})


    # output

    if on:
        response = co.chat_stream(chat_history=st.session_state.messages, message=prompt, model=model_id, connectors=[{"id": "web-search"}])
        msg = st.chat_message("assistant").write_stream(event.text for event in response if event.event_type == "text-generation")
        st.session_state.messages.append({"role": "assistant", "message": msg})
        st.stop()

    result = db.search(prompt, k=10)
    if result:
        hits, score = result

        docs = []
        for idx in hits:
            docs.append(
                {
                    "title" : idx["doc"]["title"],
                    "text" : idx["doc"]["text"],
                    "url" : idx["doc"]["url"]
                }
            )

        # msg = ""
        # for hit in hits:
        #     msg += hit["doc"]["text"] + "\n\n"

        # for hit in hits:
        #     msg += hit["doc"]["url"] + "\n\n"

        # st.chat_message("assistant").write_stream((char for char in msg))
        # response = co.chat_stream(chat_history=st.session_state.messages, message=instructions, model=model_id, documents=docs, preamble=summarizer_preamble)
        prompt = prompt + "And at the end of response, print all the source paths, something like: 'python-3.12.3-docs-text/library/functools.txt', 'python-3.12.3-docs-text/library/typing.txt'"
        response = co.chat_stream(chat_history=st.session_state.messages, message=prompt, model=model_id, documents=docs)
    else:
        response = co.chat_stream(chat_history=st.session_state.messages, message=prompt, model=model_id)

    msg = st.chat_message("assistant").write_stream(event.text for event in response if event.event_type == "text-generation")
    st.session_state.messages.append({"role": "assistant", "message": msg})
