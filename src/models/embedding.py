import os
from pathlib import Path
from FlagEmbedding import FlagModel, FlagReranker
from src.config import Config, EMBED_MODEL_INFO, RERANKER_LIST
from src.common import setup_logger, hashstr
logger = setup_logger("EmbeddingModel")

def load_local_model(
    model_local_path: dict,
    model_name: str,
    default_path: str
):
    model_path = model_local_path.get(model_name, default_path)
    if os.getenv("MODEL_ROOT_DIR") and not os.path.isabs(model_path):
        model_path = Path(os.getenv("MODEL_ROOT_DIR")).joinpath(model_path)
    return model_path

class EmbeddingModel(FlagModel):
    
    def __init__(
        self,
        model_info: dict, 
        config: Config,
        **kwargs
    ):
        self.info = model_info
        model_name_or_path = load_local_model(
            model_local_path = config.model_local_paths,
            model_name = config.embedding,
            default_path = model_info.get("default_path", None)
        )

        logger.info(f"Loading embedding model {model_info['name']} from {model_name_or_path}")

        super().__init__(
            model_name_or_path,
            query_instruction_for_retrieval=model_info.get("query_instruction", None),
            use_fp16=False, 
            **kwargs
        )
        
        logger.info(f"Embedding model {model_info['name']} loaded")

class Reranker(FlagReranker):

    def __init__(
        self, 
        config: Config, 
        **kwargs
    ):
        
        assert config.reranker in RERANKER_LIST.keys(), f"Unsupported Reranker: {config.reranker}, only support {RERANKER_LIST.keys()}"

        model_name_or_path = load_local_model(
            model_local_path = config.model_local_paths,
            model_name = config.reranker,
            default_path = RERANKER_LIST[config.reranker]
        )

        logger.info(f"Loading Reranker model {config.reranker} from {model_name_or_path}")

        super().__init__(model_name_or_path, use_fp16=True, **kwargs)
        logger.info(f"Reranker model {config.reranker} loaded")

from zhipuai import ZhipuAI
GLOBAL_EMBED_STATE = {}
class ZhipuEmbedding:

    def __init__(
        self, 
        model_info: dict, 
        config: Config
    ) -> None:
        self.config = config
        self.model_info = model_info
        self.client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
        logger.info("Zhipu Embedding model loaded")
        self.query_instruction_for_retrieval = "为这个句子生成表示以用于检索相关文章："

    def predict(
        self, 
        message: str
    ):
        data = []
        batch_size = 20

        if len(message) > batch_size:
            global GLOBAL_EMBED_STATE
            task_id = hashstr(message)
            logger.info(f"Creating new state for process {task_id}")
            GLOBAL_EMBED_STATE[task_id] = {
                'status': 'in-progress',
                'total': len(message),
                'progress': 0
            }

        for i in range(0, len(message), batch_size):
            if len(message) > batch_size:
                logger.info(f"Encoding {i} to {i+batch_size} with {len(message)} messages")
                GLOBAL_EMBED_STATE[task_id]['progress'] = i

            group_msg = message[i:i+batch_size]
            response = self.client.embeddings.create(
                model=self.model_info.get("default_path", None),
                input=group_msg,
            )

            data.extend([a.embedding for a in response.data])

        if len(message) > batch_size:
            GLOBAL_EMBED_STATE[task_id]['progress'] = len(message)
            GLOBAL_EMBED_STATE[task_id]['status'] = 'completed'

        return data
def get_embedding_model(
    config: Config
):
    if not config.enable_knowledge_base:
        return None
    
    assert config.embed_model in EMBED_MODEL_INFO.keys(), f"Unsupported embed model: {config.embed_model}, only support {EMBED_MODEL_INFO.keys()}"
    if config.embed_model in ["bge-m3", "bge-large-zh-v1.5"]:
        model = EmbeddingModel(EMBED_MODEL_INFO[config.embed_model], config)

    if config.embed_model in ["zhipu-embedding-2", "zhipu-embedding-3"]:
        model = ZhipuEmbedding(EMBED_MODEL_INFO[config.embed_model], config)
    return model
    