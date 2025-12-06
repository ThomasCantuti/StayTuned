# StayTuned

StayTuned is a web application that allows users to create podcasts about their favorite topics. Users can choose from a variety of themes and customize the podcast size.

## How it Works
1. Users select a topic and theme for their podcast.
1. At first launch an  AI agent search 10 web pages related to the topic.
1. The content from these pages is taken by a web scraper.
1. The AI creates a podcast script based on the scraped content and the length specified by the user.
1. The script is converted to speech using a text-to-speech engine.

## How to Use
1. Clone the repository to your local machine.
1. Navigate to the project directory.
1. Install the required dependencies using `pip install -r requirements.txt`.
1. Install the models from the `models` directory:
    ```bash
    python3 models/install_models.py
    ```
1. Run the OpenAI API server locally:
    - If on macOS, install llama.cpp using Homebrew:
      ```bash
      brew install llama.cpp
      ```
    - Start the server with:
      ```bash
        llama-server -m ./models/Example_model.gguf --port 8000
      ```