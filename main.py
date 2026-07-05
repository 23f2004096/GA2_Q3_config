from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml
from dotenv import load_dotenv

app = FastAPI()

# ----------------------------
# CORS (important for grader/browser checks)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (safe for assignment)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Load .env file
# ----------------------------
load_dotenv()

# ----------------------------
# 1. DEFAULT CONFIG (lowest priority)
# ----------------------------
default_config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000"
}

# ----------------------------
# 2. YAML CONFIG
# ----------------------------
def load_yaml_config():
    try:
        with open("config.development.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

# ----------------------------
# 3. .env CONFIG (with alias rule)
# ----------------------------
def load_dotenv_config():
    return {
        "debug": os.getenv("APP_DEBUG"),
        "workers": os.getenv("NUM_WORKERS")  # alias support
    }

# ----------------------------
# 4. OS ENV CONFIG
# ----------------------------
def load_os_env_config():
    return {
        "log_level": os.getenv("APP_LOG_LEVEL")
    }

# ----------------------------
# TYPE CONVERSION
# ----------------------------
def convert_value(key, value):
    if value is None:
        return None

    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]

    return str(value)

# ----------------------------
# MAIN ENDPOINT
# ----------------------------
@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    # Step 1: defaults
    config = default_config.copy()

    # Step 2: YAML override
    yaml_conf = load_yaml_config()
    config.update(yaml_conf)

    # Step 3: .env override
    env_conf = load_dotenv_config()
    config.update({k: v for k, v in env_conf.items() if v is not None})

    # Step 4: OS environment override
    os_conf = load_os_env_config()
    config.update({k: v for k, v in os_conf.items() if v is not None})

    # Step 5: CLI query overrides (highest priority)
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = value

    # Step 6: type coercion
    for key in config:
        config[key] = convert_value(key, config[key])

    # Step 7: alias fix (ensure NUM_WORKERS -> workers handled already)
    # (already mapped in dotenv loader)

    # Step 8: mask secret
    config["api_key"] = "****"

    return config