<h1 align="center">SOAP: Semantic-Oriented Alignment for Prescription Generation</h1>
<div align="center">

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=ffffff)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![MIT-license](https://img.shields.io/github/license/bitcookies/winrar-keygen.svg?logo=github)

</div>

> [!NOTICE]
> The current project is still in the early stages of development and there are still some bugs. Please feel free to raise issues if you encounter any problems.

## Overview

This a medical Q&A platform based on the LLM + RAG with knowledge base and knowledge graph. Compatible with OpenAI and mainstream Chinese language model, as well as local vllm deployment. Simply configure the `API_KEY` of the corresponding service platform to start using it.

## Quick Start

Before launching, provide the `API_KEY` of your API service provider and place it in the `src/.env` file. By default, the project uses Deepseek AI, so it is essential to configure `DEEPSEEK_API_KEY=<DEEPSEEK_API_KEY>`. For configurations of other models, refer to the `env` settings in `src/config/models.yaml`.

```env
DEEPSEEK_API_KEY=sk-ac9e8***********************cebf
OPENAI_API_KEY=sk-*********[Optional]
ZHIPUAI_API_KEY=f2ce4***********************K2SW[Optional]
```

The basic conversational service of this project can run on devices without a GPU, utilizing the online API interfaces of large models. However, for a complete knowledge base conversational experience, at least 8GB of GPU memory is required, as it involves running embedding and reranking models locally.

**Note**: The following script will start the development version, where code modifications will be automatically updated (both frontend and backend). For production deployment, please use `docker/docker-compose`.yml to launch.

```bash
docker-compose -f docker/docker-compose.dev.yml up --build
```

*You can also add the `-d` parameter to run it in the background.*

The following containers will be started:

```bash
[+] Running 6/6
 ✔ Container api-dev                Started
 ✔ Container web-dev                Started
 ✔ Container graph-dev              Started
 ✔ Container milvus-etcd-dev        Started
 ✔ Container milvus-minio-dev       Started
 ✔ Container milvus-standalone-dev  Started
```

Then, access [http://localhost:5173/](http://localhost:5173/) to see the result. *Enjoy SOAP !*

To shut down the Docker service:

```bash
docker-compose -f docker/docker-compose.dev.yml down
```

To view logs:

```bash
docker logs <CONTAINER_NAME>  # For example: docker logs api-dev
```

### Enable Local Models

If you need to use local models (not recommended to specify manually), such as embedding models or reranking models, you need to map the `MODEL_ROOT_DIR` set in the environment variables. Uncomment the following line in `backend.dockerfile`:

```dockerfile
# ENV MODEL_ROOT_DIR=/models <= uncomment this line and modify the path 
```

For example, if your local models are stored in `../models`, you need to add the following to both `docker-compose.yml` and `docker-compose.dev.yml`:

```yml
services:
  api:
    build:
      context: ..
      dockerfile: docker/api.Dockerfile
    container_name: api-dev
    working_dir: /app
    volumes:
      - ../src:/app/src
      - ../saves:/app/saves
      - ../models:/hdd/models  # <= modify this line
```

**Production Deployment**: This project also supports deploying in a production environment using Docker. Simply switch to the `docker-compose` file for production.

```bash
docker-compose -f docker/docker-compose.yml up --build
```

## Build-up TCM-KG



## Model Support

### Support for language models

The models supported are those that can be called via API. If you need to use local models, it is recommended to convert them into API services using vllm. Before using, configure the API key in the `.env` file. For configuration details, refer to [src/config/models.yaml](src/config/models.yaml).

|Provider|Default|Config Item|
|:---|:---| :---|
|`openai`|`gpt-4o`|`OPENAI_API_KEY`|
| `deepseek`(Default)|`deepseek-chat`| `DEEPSEEK_API_KEY`|
| `siliconflow` |`meta-llama/Meta-Llama-3.1-8B-Instruct`| `SILICONFLOW_API_KEY`|
|`zhipu`| `glm-4-flash`(free)|`ZHIPUAI_API_KEY`|
| `qianfan`（Baidu） |`ernie_speed` |`QIANFAN_ACCESS_KEY`, `QIANFAN_SECRET_KEY` |
| `dashscope`（Alibaba）|`qwen-max-latest`| `DASHSCOPE_API_KEY`|

The system also supports running models compatible with OpenAI. These can be added directly in the web settings, for example, when using `vllm` and `Ollama` to run local models.

### Support for Embedding Models

> [!Warning]
> Note that both the knowledge base and graph database construction rely on embedding models. Changing the embedding model midway will render the knowledge base unusable. Additionally, the vector index for the knowledge graph is built using `bge-m3` by default, so retrieval must use `bge-m3`

|Model Name(`config.embed_model`)|Default Path/Model|Config(`config.model_local_paths`)|
|:---| :---| :---|
|`bge-large-zh-v1.5`|`BAAI/bge-large-zh-v1.5`, `BAAI/bge-m3`|`bge-large-zh-v1.5`,`bge-m3`|
|`zhipu`|`embedding-2`, `embedding-3`|`ZHIPUAI_API_KEY` (`.env`)|

### Support for Reranking Models

Currently, only `BAAI/bge-reranker-v2-m3` is supported.

### Support for Local Models

- For **language models**, running local language models directly is not supported. Use `vllm` or `Ollama` to convert them into API services.
- For **embedding models** and **reranking models**, the system will automatically download the models without modification. If there are issues during the download process, refer to [HF-Mirror](https://hf-mirror.com/). If the link does not work, please check the validity of the URL and try again. Alternatively, if you have already downloaded the models locally (not recommended), you can configure them in `saves/config/config.yaml`. Note that you need to map the paths in Docker, as described in the `docker/docker-compose.yml` file in the README.

For example:

```yaml
model_local_paths:
  bge-m3: /models/bge-m3
```

## Knowledge Base Support

This project supports multiple formats of knowledge bases. Currently, the supported formats include: `pdf`, `txt`, and `md`. After uploading the files, they will first be converted to plain text. Then, the text will be transformed into vectors using a vector model and stored in a vector database. This process may take a considerable amount of time.

## Knowledge Graph Support

> [!NOTE]
> The automatic knowledge graph creation using `OneKE` in the current stage of the project is not satisfactory. It has been temporarily removed. It is recommended to create the knowledge graph outside of the project.

This project supports Neo4j as the storage for the knowledge graph. The graph needs to be organized in the jsonl format, with each line in the format of `{"h": "Beijing", "t": "China", "r": "capital"}`. You can then add this file through the graph management interface on the web page.

After the project is launched, the Neo4j service will start automatically. You can directly access and manage the graph database using [http://localhost:7474/](http://localhost:7474/). The initial default username and password are `neo4j` and `neo4j@soap`, respectively. These can be modified in both `docker/docker-compose.yml` and `docker/docker-compose.dev.yml` (Note: Both `api.environment` and `graph.environment` need to be updated).

Currently, the project does not support querying multiple knowledge graphs simultaneously, and there are no plans to support this in the near future. However, you can switch knowledge graphs by configuring different `NEO4J_URI` services. If you already have a knowledge graph based on Neo4j, you can remove the `graph` configuration item from `docker-compose.yml` and update the `NEO4J_URI` item in `api.environment` to the address of your Neo4j service.

## Update Log

- February 17, 2025: The backend was modified to use FastAPI and added standalone deployment for [Milvus-Standalone](https://github.com/milvus-io).

## Related Issues

### Docker Image Download Issues

If you are unable to download the relevant images directly, refer to [DaoCloud/public-image-mirror](https://github.com/DaoCloud/public-image-mirror?tab=readme-ov-file#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B) and try replacing the prefix as follows:

```bash
# For example, using neo4j, the same applies to others
docker pull m.daocloud.io/docker.io/library/neo4j:latest

# Then rename the image
docker tag m.daocloud.io/docker.io/library/neo4j:latest neo4j:latest
```

### Backend Service Fails to Start

If you encounter the following issue:

```bash
# ImportError: libGL.so.1: cannot open shared object file: No such file or directory
# ImportError: libgthread-2.0.so.0: cannot open shared object file: No such file or directory
```

Please uncomment the following line in `backend.Dockerfile` and reconstruct the image

```dockerfile
# RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
```
