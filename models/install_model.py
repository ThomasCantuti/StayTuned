from huggingface_hub import hf_hub_download, snapshot_download
import os
from dotenv import load_dotenv
load_dotenv()

hf_hub_download(
    repo_id="unsloth/Qwen3-4B-Thinking-2507-GGUF",
    filename="Qwen3-4B-Thinking-2507-UD-Q4_K_XL.gguf",
    local_dir="models/",
)

snapshot_download(
    repo_id="suno/bark-small",
    local_dir="models/bark-small",
    token=os.getenv("HUGGINGFACE_HUB_TOKEN")
)