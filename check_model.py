#!/usr/bin/env python3
"""Try loading the umm-maybe/AI-image-detector model."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check what architecture this model uses
from huggingface_hub import HfApi, hf_hub_download
import json

api = HfApi()
try:
    # Get model info
    info = api.model_info("umm-maybe/AI-image-detector")
    print(f"Model: {info.modelId}")
    print(f"Pipeline: {info.pipeline_tag}")
    print(f"Library: {info.library_name}")
    print(f"Downloads: {info.downloads}")
    print(f"\nFiles:")
    for f in info.siblings:
        print(f"  {f.rfilename}")
    
    # Download config
    config_path = hf_hub_download("umm-maybe/AI-image-detector", "config.json")
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    print(f"\nConfig keys: {list(config.keys())}")
    print(f"Architectures: {config.get('architectures', 'N/A')}")
    print(f"Model type: {config.get('model_type', 'N/A')}")
    if 'id2label' in config:
        print(f"Labels: {config['id2label']}")
    
    # Download preprocessor config
    pp_path = hf_hub_download("umm-maybe/AI-image-detector", "preprocessor_config.json")
    with open(pp_path, encoding='utf-8') as f:
        pp = json.load(f)
    print(f"\nPreprocessor: {pp}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
