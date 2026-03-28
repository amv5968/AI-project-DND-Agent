"""
Prompt/template utilities inspired by lab04 and util.llm_utils.
"""

import json
from pathlib import Path

try:
    from util.llm_utils import insert_params
except Exception:
    def insert_params(string: str, **kwargs):
        for key, value in kwargs.items():
            string = string.replace("{{" + key + "}}", str(value))
        return string


def load_system_prompt(template_file: str, **kwargs) -> str:
    """
    Load JSON template file and fill variable placeholders.

    Inputs:
        template_file (str): Path to template json.
    Outputs:
        str: Rendered system prompt.
    """
    with open(Path(template_file), "r", encoding="utf-8") as f:
        payload = json.load(f)

    system_prompt = payload["system_prompt"]
    return insert_params(system_prompt, **kwargs)
