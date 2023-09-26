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
import pandas as pd
import openai
import os
import random

openai.api_key = st.secrets["OPENAI_API_KEY"]

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
    'Business coach': 'développer ses compétences de coach pour faire croître son entreprise'
}

st.markdown(style, unsafe_allow_html=True)

def get_taxonomy_instruction(rua):
    if rua == "Remember":
        return random.choice(["Formattez la question sous forme de choix multiples avec une liste à puces, pour tester la mémoire directe de l'étudiant.",
                "Créez une question Vrai ou Faux pour tester la capacité de l'étudiant à identifier des informations exactes.",
                "Créez une question à trou, où l'étudiant doit remplir le blanc avec le terme ou le concept approprié, centrée sur un concept clé."])
    elif rua == "Understand":
        return random.choice([
            "Créez une question qui guide l'étudiant à interpréter des informations ou des idées, démontrant leur compréhension.",
            "Rédigez une question qui guide l'étudiant à résumer des informations ou des idées principales.",
            "Élaborez une question qui amène l'étudiant à inférer ou faire des déductions, basées sur des informations données.",
            "Concevez une question qui requiert que l'étudiant explique des concepts, des idées, des procédures, ou des phénomènes."
        ])
    elif rua == "Apply":
        return random.choice([
            "Formulez une question qui demande à l'étudiant d'exécuter une procédure ou une méthode dans une situation donnée.",
            "Concevez une question qui guide l'étudiant à mettre en œuvre ou appliquer des concepts ou des idées à une nouvelle situation.",
            "Créez une question qui encourage l'étudiant à résoudre un problème, en appliquant des connaissances et des compétences acquises.",
            "Élaborez une question qui amène l'étudiant à démontrer comment appliquer un concept ou une théorie dans un contexte pratique.",
            "Rédigez une question qui incite l'étudiant à utiliser des informations pour accomplir une tâche ou résoudre un problème concret.",
            "Formulez une question qui demande à l'étudiant de montrer comment un concept ou une idée peut être utilisé dans un contexte réel."
        ])
    else:
        return ""

def questionGenerator(prompt, job, difficulty, personal=None):
    chat = ChatOpenAI(
        model="gpt-4",
        temperature=0.5
    )
    taxonomy_instruction = get_taxonomy_instruction(rua)
    if personal:
        system_template = f"""
        Vous êtes un expert en coaching et en enseignement du développement personnel.
        Votre tâche consiste à créer une question courte et concise basée sur le document : "{prompt}"
        pour un étudiant visant à {job_description}.
        La situation personnelle de l'étudiant est la suivante : '{personal}'.
        Ne formulez pas de questions complexes, composées, ni au mode subjonctif. Formatez la question en Markdown, en plusieurs lignes si nécessaire, et sans gras.
        {taxonomy_instruction}. 
        Difficulté: {difficulty}.
        """
    else:
        system_template = f"""
        Vous êtes un expert en coaching et en enseignement du développement personnel.
        Votre tâche consiste à créer une question courte et concise basée sur le document : "{prompt}"
        pour un étudiant visant à {job_description}. 
        Ne formulez pas de questions complexes, composées, ni au mode subjonctif. Formatez la question en Markdown, en plusieurs lignes si nécessaire, et sans gras.
        {taxonomy_instruction}. 
        Difficulté: {difficulty}.
        """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = """Basé sur le document: '{prompt}', formulez une question pertinente, courte et concise."""
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
        temperature=0.5
    )
    system_template = """
    Vous êtes un expert en coaching et en développement personnel.
    Votre tâche consiste à répondre à une question de manière claire et concise, en vous basant sur '{prompt}'.
    - Si la question est de type 'choix multiples', 'vrai ou faux' ou 'remplissez les blancs', identifiez et présentez clairement la réponse correcte.
    - Si la question est un texte à trous, identifiez et présentez clairement le mot manquant.
    - Vous pouvez formater votre réponse en trois points clefs, chacun ne dépassant pas 30 mots.
    - Commencez votre réponse par une synthèse en gras, en moins de 25 mots.
    - Vos réponses doivent être formulées comme des vérités générales et doivent strictement répondre à la question posée. Évitez tout contenu superflu ou hors sujet.

    """

    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

    human_template = """
    La question est: '{front}'. Veuillez fournir une réponse basée sur '{prompt}', en suivant strictement le format et les directives fournies.
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(front=front, prompt=prompt)
    return result

def getFeedback(front, user_input, back):
    chat = ChatOpenAI(
        model="gpt-4",
        temperature=0.2
    )
    system_template = """Vous êtes un expert en coaching et en enseignement du développement personnel, et devez adresser un feedback concis à l'étudiant qui a répondu à la question: '{front}'
    La réponse attendue est : '{back}'.
    Evitez les informations superflues, analysez les mots clefs fournis par l'étudiant, et identifiez les éléments manquants ou hors-sujet dans la réponse.
    Structurez la réponse avec des points-clefs si nécessaire. La réponse ne doit pas dépasser 75 mots. Restez toujours dans une démarche bienveillante et pédagogue.
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = """Donnez un feedback à l'étudiant qui a répondu '{user_input}'."""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(front=front, user_input=user_input, back=back)
    return result

def getExample(front, prompt, personal, back):
    chat = ChatOpenAI(
        model="gpt-4",
        temperature=0.2
    )
    system_template = """Vous êtes un expert en coaching et en enseignement du développement personnel, et devez illustrer d'un exemple la réponse '{back}' à la question: '{front}'. Vous devez vous servir de '{prompt}'. Créez un scénario fictif. La réponse ne doit pas dépasser 90 mots. Restez toujours dans une démarche bienveillante et pédagogue.
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = """Illustrer la réponse '{back}' à la question {front}. Personnalisez la réponse à l'étudiant: {personal}"""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(front=front, prompt=prompt, personal=personal, back=back)
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
    feedback_placeholder = st.empty()
    example_placeholder = st.empty()
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("⛔ Difficile ⛔")
            if st.button('Flip to Question'):
                st.session_state.side = 'front'
        with col2:
            st.button("🟠 Moyen 🟠")
            if st.button("Get Example"):
                example = getExample(st.session_state.front_content, prompt, personal, st.session_state.back_content)
                example_placeholder.markdown(f"<div class='card'><b>{example}</b></div>", unsafe_allow_html=True)
        with col3:
            st.button("✅ Facile ✅")
            if st.button("Get Feedback"):
                feedback = getFeedback(st.session_state.front_content, st.session_state.user_input, st.session_state.back_content)
                feedback_placeholder.markdown(f"<div class='card'><b>{feedback}</b></div>", unsafe_allow_html=True)

def load_flashcards_from_csv(uploaded_file):
    """Upload a CSV of flashcards into the session_state"""
    flashcards = []
    decoded_file = uploaded_file.read().decode('utf-8')
    file_as_string = StringIO(decoded_file)
    reader = csv.reader(file_as_string, delimiter=',')
    next(reader)
    next(reader)
    for row in reader:
        params, front, back  = row
        job, difficulty = params.split('_')
        flashcards.append({
            'front': front,
            'back': back,
            'job': job,
            'difficulty': difficulty,
            'taxonomy': rua
        })
    return flashcards

def export_flashcards_to_csv(flashcards, title="Flashcards"):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([title, "", ""])  # CSV title row
    writer.writerow(["Params", "Question", "Answer"])  # header
    for card in flashcards:
        params = f"{card['job']}_{card['difficulty']}_{card['taxonomy']}"
        writer.writerow([params, card['front'], card['back']])
    
    # Get the content of the output and return it
    content = output.getvalue()
    output.close()
    return content

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

# ------------ Settings ------------
st.sidebar.header("Commencez ici 👇")

if 'txt_content' not in st.session_state:
    prompt = st.sidebar.text_input('Entrez un prompt (ou chargez un fichier .txt ci-dessous)')
else:
    prompt = st.session_state.txt_content

# File
#uploaded_file = st.sidebar.file_uploader('Upload a .txt file', type=["txt"])
#if uploaded_file:
#    txt_content = uploaded_file.read().decode("utf-8")
#    st.session_state.txt_content = txt_content
#    prompt = txt_content
    
template_dir = 'Fiches pédagogiques'
try:
    file_names = sorted([file[:-4] for file in os.listdir(template_dir) if file.endswith('.txt')])
except FileNotFoundError:
    st.sidebar.write(f"Folder {template_dir} not found.")
    file_names = []
file_names.insert(0, "Chargez votre fichier")
selected_file = st.sidebar.selectbox('Choisissez un fichier modèle ou chargez le vôtre', file_names)
if selected_file == "Chargez votre fichier":
    uploaded_file = st.sidebar.file_uploader('Chargez votre fichier .txt', type=["txt"])
    if uploaded_file:
        txt_content = uploaded_file.read().decode("utf-8")
        st.session_state.txt_content = txt_content
        prompt = txt_content
else:
    try:
        with open(os.path.join(template_dir, selected_file + '.txt'), 'r', encoding='utf-8') as file:
            txt_content = file.read()
            st.session_state.txt_content = txt_content
            prompt = txt_content
    except FileNotFoundError:
        st.sidebar.write(f"Fichier {selected_file}.txt non trouvé dans {template_dir}.")


# Params
personal = None

job = st.sidebar.selectbox('Choississez votre voie', ['Life coach', 'Business coach'])
job_description = JOB_DESCRIPTIONS.get(job, job)
difficulty = st.sidebar.selectbox('Choississez la difficulté', ['Débutant', 'Avancé'])
rua = st.sidebar.selectbox('Choississez le type de carte', ['Remember','Understand','Apply'],index=1)
st.sidebar.header("Optionnel (WIP)")
personal = st.sidebar.text_input('Quelle est ta situation personnelle ?')
go_button = st.sidebar.button("Let's go!")
if go_button:
    with st.spinner('Génération en cours...'):
        if prompt:
            st.session_state.front_content = questionGenerator(prompt, job, difficulty, personal)
            st.session_state.back_content = bulletPointAnswer(st.session_state.front_content, prompt)
            st.session_state.flashcards.append({
                'front': st.session_state.front_content,
                'back': st.session_state.back_content,
                'job': job,
                'difficulty': difficulty,
                'taxonomy': rua
            })
            st.session_state.side = 'front'
            st.session_state.current_flashcard_index = len(st.session_state.flashcards) - 1
            

# Display the front and back content of the flashcard
if st.session_state.get('front_content') and st.session_state.side == 'front':
    display_front(st.session_state.front_content)
    col_flip1, col_flip2 = st.columns(2)
    with col_flip1:
        if st.button('Flip to Answer'):
            st.session_state.side = 'back'
elif st.session_state.get('front_content') and st.session_state.side == 'back':
    display_back(st.session_state.front_content, st.session_state.back_content, st.session_state.user_input)
else:
    if not go_button:
        st.write('Veuillez indiquer vos paramètres et cliquer "Let\'s go!".')

# Select a flashcard from the list
flashcard_options = [f"Flashcard {i+1} ({card['job']}_{card['difficulty']}_{card['taxonomy']})" for i, card in enumerate(st.session_state.flashcards)]
if not flashcard_options:
    st.sidebar.write("Lorsque vous aurez généré des cartes, elles apparaîtront ici.")
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
if flashcard_options:
    if st.sidebar.download_button(
            label="Télecharger les Flashcards",
            data=export_flashcards_to_csv(st.session_state.flashcards, title='Flashcards'),
            file_name='flashcards.csv',
            mime='text/csv'
        ):
        st.sidebar.write(f'Flashcards téléchargées: flashcards.csv!')