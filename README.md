# Paradox Flashcards

Welcome to the Paradox Flashcards project. 

These flashcards are generated from fiches pédagogiques on each Etape du protocole. Soon they will be generated from other sources of Paradox material.

## Table of Contents

- [Features](#features)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
- [Deployment](#deployment)

## Features

- This project Generates, Displays, Stores, and Exports Personalised Coaching Flashcards.
- Flexible Data Ingestion: Supports ingestion from any `.txt` placed in the Fiches Pédagogique folder, as well as by a custom prompt in the GUI.
- Multiple extra features: Example generation, Feedback feature, Difficulty levels, card types...
- It makes use of Langchain, OpenAI, and Streamlit for display.
- This project requires having an OpenAI API key with access to GPT4.

## Setup

### Prerequisites

1. Ensure you have Python installed.
2. Clone this repository:
   ```zshrc
   git clone https://github.com/davidlaroche/flashcards
   cd flashcards
   ```
3. Install the required packages.
   ```zshrc
   pip install -r requirements.txt
   ```
   
### Setting up your OpenAI key

1. Create a folder named `.streamlit`
2. Create a file named `secrets.toml`
3. Open the file with Notepad or Notepad+, and write the line:
   `OPENAI_API_KEY = 'Your OpenAI API key'`
4. Make sure to surround the key with either apostrophes or quotation marks, and save the file when you're done.

## Deployment

To deploy the Paradox Flashcards, run the streamlit script:
  ```zshrc
  cd Scripts
  streamlit run flashcards_streamlit_personal.py
  ```
Your Terminal should give you a localhost link, which you can paste into your browser directly.

Have fun !
