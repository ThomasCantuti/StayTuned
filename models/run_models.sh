#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# MODEL="$DIR/Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf"
MODEL="$DIR/Qwen3-1.7B-BF16.gguf"

# Check if model exists
if [ ! -f "$MODEL" ]; then
    echo "Error: Model file $MODEL not found."
    echo "Please run 'python install_model.py' first to download the model."
    exit 1
fi

echo "Starting local LLM server with $MODEL..."

# Option 1: Native llama-server binary 
# (if installed via brew install llama.cpp or compiled locally)
if command -v llama-server &> /dev/null; then
    echo "Found native llama-server binary. Starting server..."
    llama-server \
        --model "$MODEL" \
        --ctx-size 8192 \
        --n-gpu-layers 30 \
        --port 8080 \
        --host 127.0.0.1

# Option 2: Python server using llama-cpp-python
# (if installed via pip install 'llama-cpp-python[server]')
elif python3 -c "import llama_cpp.server" &> /dev/null; then
    echo "Found llama-cpp-python Python module. Starting server..."
    python3 -m llama_cpp.server \
        --model "$MODEL" \
        --n_ctx 8192 \
        --n_gpu_layers 30 \
        --port 8080 \
        --host 127.0.0.1

else
    echo "No llama-server binary or llama_cpp.server python module found."
    echo "Please install llama.cpp using one of the following methods:"
    echo "1. Homebrew (macOS): brew install llama.cpp"
    echo "2. Python: pip install 'llama-cpp-python[server]'"
    echo "3. Compile from source: git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && make"
    exit 1
fi
