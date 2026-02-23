from huggingface_hub import hf_hub_download, snapshot_download
import os
from dotenv import load_dotenv
load_dotenv()

# hf_hub_download(
#     repo_id="unsloth/Qwen3-4B-Thinking-2507-GGUF",
#     filename="Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf",
#     local_dir="models/",
#     token=os.getenv("HUGGINGFACE_HUB_TOKEN")
# )

hf_hub_download(
    repo_id="unsloth/Qwen3-1.7B-GGUF",
    filename="Qwen3-1.7B-BF16.gguf",
    local_dir="models/",
    token=os.getenv("HUGGINGFACE_HUB_TOKEN")
)

# snapshot_download(
#     repo_id="microsoft/VibeVoice-1.5B",
#     local_dir="models/VibeVoice-1.5B",
#     token=os.getenv("HUGGINGFACE_HUB_TOKEN")
# )