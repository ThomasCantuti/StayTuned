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
          llama-server -m ./models/Example_model.gguf --port 8080
        ```
    - If on Windows or Linux with Blackwell architecture (RTX 50xx):
    ```bash
      # Get llama.cpp (if you don’t already have it)
      git clone https://github.com/ggml-org/llama.cpp.git
      cd llama.cpp

      rm -rf build

      cmake -B build \
        -DGGML_CUDA=ON \
        -DLLAMA_BUILD_TOOLS=ON \
        -DLLAMA_BUILD_EXAMPLES=ON \
        -DLLAMA_BUILD_SERVER=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES=90 \
        -DGGML_CUDA_ARCHITECTURES=90

      cmake --build build --config Release -j"$(nproc)"

      echo 'export PATH="$HOME/llama.cpp/build/bin:$PATH"' >> ~/.bashrc
      source ~/.bashrc

      sudo ln -s "$HOME/llama.cpp/build/bin/llama-cli" /usr/local/bin/llama-cli
      sudo ln -s "$HOME/llama.cpp/build/bin/llama-server" /usr/local/bin/llama-server
      ```
    - If on Windows or Linux with older architectures:
    ```bash
      # Change just the build, the rest is the same as the Blackwell architecture
      cmake -B build \
        -DGGML_CUDA=ON \
        -DLLAMA_BUILD_TOOLS=ON \
        -DLLAMA_BUILD_EXAMPLES=ON \
        -DLLAMA_BUILD_SERVER=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES=native
      ```
    - Then make it run with:
      ```bash
      llama-server -m ./models/Example_model.gguf --port 8080
      ```