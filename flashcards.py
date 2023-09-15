import streamlit as st
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)
from langchain.document_loaders import *
from langchain.chains.summarize import load_summarize_chain
import tempfile
from langchain.docstore.document import Document
import csv
from io import StringIO

st.sidebar.title('Flash cards')

style = """
<style>
    .card {
        border: 2px solid black;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 3px 3px 15px rgba(0,0,0,0.2);
        background-color: white;
        color: black;
    }
</style>
"""
JOB_DESCRIPTIONS = {
    'Life coach': 'développer ses compétences de coach professionnel dans la vie de tous les jours',
    'Business coach': 'développer ses compétences de coach pour faire croître son entreprise',
    'Manager': 'devenir un manager d\'entreprise accompli',
    'Self development': 'se développer sur le plan personnel',
}

st.markdown(style, unsafe_allow_html=True)

def questionGenerator(prompt, job, difficulty):
    chat = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        openai_api_key="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"
    )
    system_template = f"""
    Vous êtes un expert en coaching et en enseignement du développement personnel.
    Votre tâche consiste à créer une question courte et concise basée sur le document : "{prompt}".
    La question doit s'adresser à un étudiant particulier, dont l'ambition est de {job_description}.
    La question doit être de difficulté {difficulty}.
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = """Based on the prompt: '{prompt}', please generate a relevant, short, concise question."""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(prompt=prompt)
    return result

def bulletPointAnswer(front, prompt):
    chat = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        openai_api_key="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"
    )
    system_template = """Vous êtes un expert en coaching et en enseignement du développement personnel.
    Votre tâche consiste à répondre à une question de manière claire et concise, en pas plus de 3 points clefs, en vous appuyant uniquement sur '{prompt}'
    Les points clefs ne peuvent pas dépasser 30 mots chacun. Au début de votre réponse, vous indiquerez une synthèse en gras, en moins de 25 mots.
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = """La question est: '{front}'. En vous basant sur '{prompt}', veuillez fournir une réponse en pas plus de 3 points clefs."""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(front=front, prompt=prompt)
    return result

def display_front(front):
    """"Displays the question, and an input box to gather user_input"""
    st.markdown(f"<div class='card'><b>{front}</b></div>", unsafe_allow_html=True)
    st.session_state.user_input = st.text_input("Your Answer:")

def display_back(front_content, back_content, user_input):
    """Displays the question, the Answer, the user_input, and the Je le savais déjà/Je ne le savais pas buttons"""
    st.markdown(f"<div class='card'><b>Question:</b>\n\n{front_content}</div>", unsafe_allow_html=True)
    if back_content:
        st.markdown(f"<div class='card'><b>Answer:</b>\n\n{back_content}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card'><b>Your Answer:</b>\n\n{user_input}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("🔁 Je ne le savais pas. 🔁")
    with col2:
        st.button("✅ Je le savais déjà ! ✅")

def load_flashcards_from_csv(uploaded_file):
    """Upload a CSV of flashcards into the session_state"""
    flashcards = []
    # Convert bytes to string
    decoded_file = uploaded_file.read().decode('utf-8')
    file_as_string = StringIO(decoded_file)
    reader = csv.reader(file_as_string, delimiter=',')
    # Skip the title and header
    next(reader, None)
    for row in reader:
        params, front, back  = row
        job, difficulty, temperature = params.split('_')
        flashcards.append({
            'front': front,
            'back': back,
            'job': job,
            'difficulty': difficulty,
            'temperature': temperature
        })
    return flashcards

def export_flashcards_to_csv(flashcards, title="Flashcards", filename='flashcards.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([title, "", ""])  # CSV title row
        writer.writerow(["Params", "Question", "Answer"])  # header
        for card in flashcards:
            params = f"{card['job']}_{card['difficulty']}_{card['temperature']}"
            writer.writerow(params, [card['front'], card['back']])

# Initialize session_states
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []

if 'side' not in st.session_state:
    st.session_state.side = 'front'

if 'txt_content' not in st.session_state:
    st.session_state.txt_content = None

if 'front_content' not in st.session_state:
    st.session_state.front_content = None

if 'back_content' not in st.session_state:
    st.session_state.back_content = None

if 'current_flashcard_index' not in st.session_state:
    st.session_state.current_flashcard_index = 0

# ------------ Upload ------------
st.sidebar.header("Upload")
uploaded_file = st.sidebar.file_uploader('Upload a CSV', type=["csv"])
if uploaded_file:
    if st.sidebar.button('Load Flashcards'):
        st.session_state.flashcards = load_flashcards_from_csv(uploaded_file)
        st.write('Flashcards loaded!')

# ------------ Settings ------------
st.sidebar.header("Settings")

if 'txt_content' not in st.session_state:
    prompt = st.sidebar.text_input('Enter your prompt (or upload a .txt file below)')
else:
    prompt = st.session_state.txt_content

# File
uploaded_file = st.sidebar.file_uploader('Upload a .txt file', type=["txt"])
if uploaded_file:
    txt_content = uploaded_file.read().decode("utf-8")
    st.session_state.txt_content = txt_content
    prompt = txt_content

# Job
job = st.sidebar.selectbox('Select desired job', ['Life coach', 'Business coach', 'Manager', 'Self Development'])
job_description = JOB_DESCRIPTIONS.get(job, job)

# Difficulty
difficulty = st.sidebar.selectbox('Select difficulty level', ['Facile', 'Moyenne', 'Avancée'])

# Temperature
temperature = st.sidebar.slider(label='Temperature', min_value=0.0, max_value=1.0, value=0.2, step=0.1)

# Go
go_button = st.sidebar.button('Go')
if go_button:
    with st.spinner('Generating Flashcard...'):
        if prompt:
            st.session_state.front_content = questionGenerator(prompt, job, difficulty)
            st.session_state.back_content = bulletPointAnswer(st.session_state.front_content, prompt)
            st.session_state.flashcards.append({
                'front': st.session_state.front_content,
                'back': st.session_state.back_content,
                'job': job,
                'difficulty': difficulty,
                'temperature': temperature
            })
            st.session_state.current_flashcard_index = len(st.session_state.flashcards) - 1

# Front and back
if st.session_state.get('front_content') and st.session_state.side == 'front':
    display_front(st.session_state.front_content)
    if st.button('Flip to Answer'):
        st.session_state.side = 'back'
elif st.session_state.get('front_content') and st.session_state.side == 'back':
    display_back(st.session_state.front_content, st.session_state.back_content, st.session_state.user_input)
    if st.button('Flip to Question'):
        st.session_state.side = 'front'
else:
    if not go_button:
        st.write("Please set all parameters and press 'Go'.")

# Select a flashcard
flashcard_options = [f"Flashcard {i+1} ({card['job']}_{card['difficulty']}_{card['temperature']}" for i, card in enumerate(st.session_state.flashcards)]
if flashcard_options:
    selected_flashcard = st.sidebar.selectbox("Choose a flashcard:", flashcard_options, index=st.session_state.current_flashcard_index or 0)
    if selected_flashcard and st.session_state.current_flashcard_index != flashcard_options.index(selected_flashcard):
        st.session_state.current_flashcard_index = flashcard_options.index(selected_flashcard)
        st.session_state.front_content = st.session_state.flashcards[st.session_state.current_flashcard_index]['front']
        st.session_state.back_content = st.session_state.flashcards[st.session_state.current_flashcard_index]['back']
        st.session_state.side = 'front'
else:
    selected_flashcard = None

# ------------ Export ------------
st.sidebar.header("Export")
title = st.sidebar.text_input("Enter the CSV title:", "apples_and_bananas")
if st.sidebar.button('Export Flashcards'):
    export_flashcards_to_csv(st.session_state.flashcards, filename=f'./Flaschard CSVs/{title}.csv')
    st.write(f'Flashcards exported to {title}.csv!')
