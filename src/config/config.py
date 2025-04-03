import os
import json
import yaml
from pathlib import Path

from typing import List, Tuple, Dict

from src.common import setup_logger
logger = setup_logger("Config")

with open(Path("src/config/models.yaml"), "r") as f:
    _models = yaml.safe_load(f)

MODEL_NAMES = _models["MODEL_NAMES"]
EMBED_MODEL_INFO = _models["EMBED_MODEL_INFO"]
RERANKER_LIST = _models["RERANKER_LIST"]

class SimpleConfig(dict):
    
    def __key(self, key): # private func to lower key
        return "" if key is None else key.lower()
    
    def __str__(self):
        return json.dumps(self)
    
    def __setattr__(self, key, value):
        self[self.__key(key)] = value

    def __getattr__(self, key):
        return self.get(self.__key(key))
    
    def __getitem__(self, key):
        return super().get(self.__key(key))
    
    def __setitem__(self, key, value):
        return super().__setitem__(self.__key(key), value)
    
    def __dict__(self):
        return {k: v for k, v in self.items()}
    
class Config(SimpleConfig):

    def __init__(self, filename=None):
        super().__init__()
        self._config_items = {}

        self.add_item("stream", default=True, des="Enable Streaming Response")
        self.add_item("save_dir", default="saves", des="Save Directory")

        self.add_item("enable_reranker", default=False, des="Enable Re-Ranker")
        self.add_item("enable_knowledge_base", default=False, des="Enable Knowledge Base")
        self.add_item("enable_knowledge_graph", default=False, des="Enable Knowledge Graph")
        self.add_item("enable_search_engine", default=False, des="Enable Search Engine")

        self.add_item("model_provider", default="zhipu", des="Model Provider", choices=list(MODEL_NAMES.keys()))
        self.add_item("model_name", default=None, des="Model Name")
        self.add_item("embedding", default="bge-m3", des="Embedding Model", choices=list(EMBED_MODEL_INFO.keys()))
        self.add_item("reranker", default="bge-reranker-v2-m3", des="Re-Ranker Model", choices=list(RERANKER_LIST.keys()))
        self.add_item("model_local_paths", default={}, des="Local Model Paths")

        self.filename = filename or os.path.join(self.save_dir, "config", "config.yaml")
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        self.load() # override the default config
        self.handle_self()
    def add_item(
        self,
        key: str,
        default: str,
        des: str = None,
        choices: List = None 
    ):
        self.__setattr__(key, default)
        self._config_items[key] = {
            "default": default,
            "des": des,
            "choices": choices
        }

    def load(self):
        logger.info(f"Loading config from {self.filename}")
        if self.filename is not None and os.path.exists(self.filename):
            if self.filename.endswith(".json"):
                with open(self.filename, 'r') as f:
                    content = f.read()
                    if content:
                        local_config = json.loads(content)
                        self.update(local_config)
                    else:
                        print(f"{self.filename} is empty.")
            elif self.filename.endswith(".yaml"):
                with open(self.filename, 'r') as f:
                    content = f.read()
                    if content:
                        local_config = yaml.safe_load(content)
                        self.update(local_config)
                    else:
                        print(f"{self.filename} is empty.")
            else:
                logger.warning(f"Unknown config file type {self.filename}")
        else:
            logger.warning(f"\n\n{'='*70}\n{'Config file not found':^70}\n{'You can custum your config in `' + self.filename + '`':^70}\n{'='*70}\n\n")

    def handle_self(self):
        self.model_names = MODEL_NAMES
        model_provider_info = self.model_names.get(self.model_provider, {})

        if self.model_provider != "custom":
            if self.model_name not in model_provider_info["models"]:
                logger.warning(f"Model name {self.model_name} not in {self.model_provider}, using default model name")
                self.model_name = model_provider_info["default"]

            default_model_name = model_provider_info["default"]
            self.model_name = self.get("model_name") or default_model_name

        else:
            self.model_name = self.get("model_name")
            if self.model_name not in [item["custom_id"] for item in self.custom_models]:
                logger.warning(f"Model name {self.model_name} not in custom models, using default model name")
                self.model_name = self.custom_models[0]["custom_id"]

        conds = {}
        self.model_provider_status = {}
        for provider in self.model_names:
            conds[provider] = self.model_names[provider]["env"]
            conds_bool = [bool(os.getenv(_k)) for _k in conds[provider]]
            self.model_provider_status[provider] = all(conds_bool)

        self.valuable_model_provider = [k for k, v in self.model_provider_status.items() if v]
        assert len(self.valuable_model_provider) > 0, f"No model provider available, please check your `.env` file. API_KEY_LIST: {conds}"

    def save(self):
        logger.info(f"Saving config to {self.filename}")
        if self.filename is None:
            logger.warning("Config file is not specified, save to default config/base.yaml")
            self.filename = os.path.join(self.save_dir, "config", "config.yaml")
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        if self.filename.endswith(".json"):
            with open(self.filename, 'w+') as f:
                json.dump(self.__dict__(), f, indent=4, ensure_ascii=False)
        elif self.filename.endswith(".yaml"):
            with open(self.filename, 'w+') as f:
                yaml.dump(self.__dict__(), f, indent=2, allow_unicode=True)
        else:
            logger.warning(f"Unknown config file type {self.filename}, save as json")
            with open(self.filename, 'w+') as f:
                json.dump(self, f, indent=4)
        logger.info(f"Config file {self.filename} saved")

    def __dict__(self):
        blocklist = [
            "_config_items",
            "model_names",
            "model_provider_status",
        ]
        return {k: v for k, v in self.items() if k not in blocklist}
