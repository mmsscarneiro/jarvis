"""Run with: python3 -m jarvis.web"""
from pathlib import Path

import uvicorn
import yaml

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "config.yaml"

with _CONFIG_PATH.open() as _f:
    _cfg = yaml.safe_load(_f)

port: int = _cfg.get("web", {}).get("port", 7777)
uvicorn.run("jarvis.web.api:app", host="0.0.0.0", port=port, reload=False)
