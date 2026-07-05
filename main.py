import os
from dotenv import load_dotenv
import yaml

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# -----------------------
# Defaults
# -----------------------

config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# -----------------------
# YAML
# -----------------------

with open("config.development.yaml") as f:
    yaml_cfg = yaml.safe_load(f) or {}

config.update(yaml_cfg)

# -----------------------
# .env
# -----------------------

env_mapping = {
    "APP_PORT": "port",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
    "NUM_WORKERS": "workers",
}

for env_key, cfg_key in env_mapping.items():
    value = os.getenv(env_key)
    if value is not None:
        config[cfg_key] = value

# -----------------------
# OS ENV (higher priority)
# -----------------------

# (Render environment variables automatically override .env)

for env_key, cfg_key in env_mapping.items():
    if env_key in os.environ:
        config[cfg_key] = os.environ[env_key]


def convert_bool(v):
    return str(v).lower() in ("true", "1", "yes", "on")


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    final = dict(config)

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        k, v = item.split("=", 1)
        final[k] = v

    # Type coercion
    final["port"] = int(final["port"])
    final["workers"] = int(final["workers"])
    final["debug"] = convert_bool(final["debug"])
    final["log_level"] = str(final["log_level"])

    # Mask secret
    final["api_key"] = "****"

    return final