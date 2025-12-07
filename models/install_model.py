from huggingface_hub import hf_hub_download, snapshot_download

hf_hub_download(
    repo_id="unsloth/Qwen3-4B-Thinking-2507-GGUF",
    filename="Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf",
    local_dir="models/",
)

snapshot_download(
    repo_id="microsoft/VibeVoice-Realtime-0.5B",
    local_dir="models/VibeVoice-Realtime-0.5B",
)