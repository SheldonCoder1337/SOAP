import os
import json
import torch

from neo4j import GraphDatabase
from typing import List, Dict, Tuple, Any
from transformers import AutoTokenizer, AutoModel
from FlagEmbedding import FlagModel, FlagReranker

from src.config import Config
from src.models.embedding import EmbeddingModel 
from src.common import setup_logger
from src.plugins import pdf2txt, OneKE

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = setup_logger("Graph Database")

UIE_MODEL = None

class GraphDB:

    def __init__(
        self, 
        config: Config, 
        embed_model = None, 
        kgdb_name: str="neo4j"
    ):
        self.config = config
        self.embed_model = embed_model
        self.kgdb_name = kgdb_name
        self.driver = None
        self.status = "closed"
        self.files = []

        assert embed_model, "embed_model=None"

    ####################
    #      basic       #
    ####################

    """
    Start the connection to the knowledge graph
    """
    def start(self):
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "neo4j@soap")
        logger.info(f"Connecting to Neo4j {uri}/{self.kgdb_name}")
        try:
            self.driver = GraphDatabase.driver(
                f"{uri}/{self.kgdb_name}",
                auth=(username, password)
            )
            self.status = "open"
            logger.info(f"Connected to Neo4j at {uri}/{self.kgdb_name}, {self.get_database_info()}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}, {uri}, {self.kgdb_name}, {username}, {password}")
            self.config.enable_knowledge_graph = False

    """
    Close the connection to the knowledge graph
    """
    def close(self):
        self.driver.close()
        self.status = "closed"
        logger.info(f"Disconnected from Neo4j at {self.kgdb_name}")

    """
    Create a new graph database
    """
    def create_graph_database(self, kgdb_name):
        with self.driver.session() as session:
            existing_databases = session.run("SHOW DATABASES")
            existing_db_names = [db['name'] for db in existing_databases]

            if existing_db_names:
                print(f"Existing DB: {existing_db_names[0]}")
                return existing_db_names[0]  # return the name of the existing database

            session.run(f"CREATE DATABASE {kgdb_name}")
            print(f"Create database '{kgdb_name}' successfully.")
            return kgdb_name  # return the name of the created database

    """
    Retrieve n sample nodes from the knowledge graph
    """ 
    def get_sample_nodes(
        self, 
        kgdb_name='neo4j', 
        num=50
    ):
        self.use_database(kgdb_name)
        def query(tx, num):
            result = tx.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT $num", num=int(num))
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, num)

    """
    Get the database information
    """
    def get_database_info(self, db_name="neo4j"):
        self.use_database(db_name)
        def query(tx):
            entity_count = tx.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            relationship_count = tx.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            triples_count = tx.run("MATCH (n)-[r]->(m) RETURN count(n) AS count").single()["count"]

            # access all labels
            labels = tx.run("CALL db.labels() YIELD label RETURN collect(label) AS labels").single()["labels"]

            return {
                "database_name": db_name,
                "entity_count": entity_count,
                "relationship_count": relationship_count,
                "triples_count": triples_count,
                "labels": labels,
                "status": self.status
            }

        with self.driver.session() as session:
            return session.execute_read(query)

    """
    Switch to a specific database 
    """   
    def use_database(self, kgdb_name="neo4j"):
        assert kgdb_name == self.kgdb_name, f"the given db name '{kgdb_name}' is inconsistent with the current instance '{self.kgdb_name}'"
        # assert kgdb_name == self.kgdb_name, f"传入的数据库名称 '{kgdb_name}' 与当前实例的数据库名称 '{self.kgdb_name}' 不一致"
        if self.status == "closed":
            self.start()

    """
    Embedding the text
    """
    def get_embedding(
        self, 
        text:str
    ):
        inputs = [text]
        with torch.no_grad():
            outputs = self.embed_model.encode(inputs)
        embeddings = outputs[0] # Assuming the average is taken as the embedding vector for the text.
        return embeddings

    def set_embedding(
        self, 
        tx, # a transaction object of neo4j
        entity_name:str, 
        embedding
        ):
        tx.run("""
        MATCH (e:Entity {name: $name})
        CALL db.create.setNodeVectorProperty(e, 'embedding', $embedding)
        """, name=entity_name, embedding=embedding)


    ####################
    #       add        #
    ####################

    """
    Add triples to the knowledge graph 
    """   
    def txt_add_entity(self, triples, kgdb_name='neo4j'):
        self.use_database(kgdb_name)
        def create(tx, triples):
            for triple in triples:
                h = triple['h']
                t = triple['t']
                r = triple['r']
                query = (
                    "MERGE (a:Entity {name: $h}) "
                    "MERGE (b:Entity {name: $t}) "
                    "MERGE (a)-[:" + r.replace(" ", "_") + "]->(b)"
                )
                tx.run(query, h=h, t=t)

        with self.driver.session() as session:
            session.execute_write(create, triples)
    
    """
    Auto add triples to the knowledge graph from pdf using OneKE
    Note: the perfomance of OneKE is poor, so we still recommend you to use jsonl file artificially instead
    """
    def pdf_file_add_entity(self, 
                            file_path, 
                            output_path, 
                            kgdb_name='neo4j'
                            ):
        from src.plugins import pdf2txt, OneKE
        self.use_database(kgdb_name)
        text_path = pdf2txt(file_path)
        global UIE_MODEL
        if UIE_MODEL is None:
            UIE_MODEL = OneKE()
        triples_path = UIE_MODEL.processing_text_to_kg(text_path, output_path)
        self.jsonl_file_add_entity(triples_path)
        return kgdb_name

    """
    Add triple data to the knowledge graph database 
    and create vector indexes for entities.
    """
    def txt_add_vector_entity(
        self, 
        triples: List[Dict[str, str]], # [{'h':'head entity','t':'tail entity','r':'relation'}]
        kgdb_name='neo4j'
        ):
        
        self.use_database(kgdb_name)
        def _index_exists(
            tx,  # a transaction object of neo4j
            index_name
            ) -> bool:
            result = tx.run("SHOW INDEXES")
            for record in result:
                if record["name"] == index_name:
                    return True
            return False
        
        def _create_graph(
            tx,
            data: List[Dict[str, str]]
            ):
            for entry in data:
                tx.run("""
                MERGE (h:Entity {name: $h})
                MERGE (t:Entity {name: $t})
                MERGE (h)-[r:RELATION {type: $r}]->(t)
                """, h=entry['h'], t=entry['t'], r=entry['r'])

        def _create_vector_index(
            tx, 
            dim):
            index_name = "entityEmbeddings"
            if not _index_exists(tx, index_name):
                tx.run(f"""
                CREATE VECTOR INDEX {index_name}
                FOR (n: Entity) ON (n.embedding)
                OPTIONS {{indexConfig: {{
                `vector.dimensions`: {dim},
                `vector.similarity_function`: 'cosine'
                }} }};
                """)

        from src.config import EMBED_MODEL_INFO
        embed_info = EMBED_MODEL_INFO[self.config.embed_model]
        with self.driver.session() as session:
            session.execute_write(_create_graph, triples)
            session.execute_write(_create_vector_index, embed_info.get('dimension'))
            for i, entry in enumerate(triples):
                logger.info(f"Adding entity {i+1}/{len(triples)}")
                embedding_h = self.get_embedding(entry['h'])
                session.execute_write(self.set_embedding, entry['h'], embedding_h)

                embedding_t = self.get_embedding(entry['t'])
                session.execute_write(self.set_embedding, entry['t'], embedding_t)

    """
    Add triples to the knowledge graph from a jsonl file (recommanded)
    """
    def jsonl_file_add_entity(self, file_path, kgdb_name='neo4j'):
        self.status = "processing"
        kgdb_name = kgdb_name or 'neo4j'
        self.use_database(kgdb_name)  # switch to the specified database

        def read_triples(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    yield json.loads(line.strip())

        triples = list(read_triples(file_path))

        self.txt_add_vector_entity(triples, kgdb_name)

        self.status = "open"
        return kgdb_name

    ####################
    #      delete      #
    ####################

    """
    Delete entities from the knowledge graph
    if entity_name is None, delete all entities
    """
    def delete_entity(self, entity_name=None, kgdb_name="neo4j"):
        self.use_database(kgdb_name)
        with self.driver.session() as session:
            if entity_name:
                session.execute_write(self._delete_specific_entity, entity_name)
            else:
                session.execute_write(self._delete_all_entities)

    def _delete_specific_entity(self, tx, entity_name):
        query = """
        MATCH (n {name: $entity_name})
        DETACH DELETE n
        """
        tx.run(query, entity_name=entity_name)

    def _delete_all_entities(self, tx):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        tx.run(query)


    ####################
    #      query       #
    ####################
    
    
    """
    A vector-based similarity query to find entities similar to the given entity.

    This function uses the vector embedding of the given entity to query the knowledge graph 
    database and returns a list of similar entities along with their similarity scores.
    """
    def query_by_vector_tep(
        self, 
        entity_name: str, 
        kgdb_name: str = 'neo4j'
        ) -> List[Tuple[str, float]]:
        """
        Parameters:
            entity_name (str): The name of the entity to query.
            kgdb_name (str): The name of the knowledge graph database. Defaults to 'neo4j'.

        Returns:
            List[Tuple[str, float]]: A list of tuples containing the names of similar entities 
            and their corresponding similarity scores.
        """
        self.use_database(kgdb_name) # # Switch to the specified knowledge graph database
        def query(
            tx, # a transaction object of neo4j 
            text: str
            ):
            embedding = self.get_embedding(text)
            result = tx.run("""
            CALL db.index.vector.queryNodes('entityEmbeddings', 10, $embedding)
            YIELD node AS similarEntity, score
            RETURN similarEntity.name AS name, score
            """, embedding=embedding)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, entity_name)

    """
    Filter entities based on vector similarity and retrieve their subgraphs within a specified number of hops.
    """
    def query_by_vector(
        self, 
        entity_name: str, 
        threshold: float = 0.9, 
        kgdb_name: str = 'neo4j', 
        hops: int = 2, 
        num_of_res: int = 5
        ) -> List[Any]:
        """
        Parameters:
            entity_name (str): The name of the entity to query.
            threshold (float): The similarity threshold for filtering entities. Defaults to 0.9.
            kgdb_name (str): The name of the knowledge graph database. Defaults to 'neo4j'.
            hops (int): The number of hops to traverse from each qualified entity. Defaults to 2.
            num_of_res (int): The maximum number of top-ranked entities to consider. Defaults to 5.

        Returns:
            List[Any]: A list of query results, containing subgraphs of qualified entities.
        """
        results = self.query_by_vector_tep(entity_name=entity_name)

        # Filter entities with similarity scores above the threshold
        qualified_entities = [result[0] for result in results[:num_of_res] if result[1] > threshold]

        # Query subgraphs for each qualified entity
        all_query_results = []
        for entity in qualified_entities:
            query_result = self.query_specific_entity(entity_name=entity, hops=hops, kgdb_name=kgdb_name)
            all_query_results.extend(query_result)

        return all_query_results
    
    # TODO
    def query_node(self, entity_name, hops=2, **kwargs):
        # Add a check to stop the search if the number of nodes is 0.
        if kwargs.get("exact_match"):
            raise NotImplemented("not implement `exact_match`")
        else:
            return self.query_by_vector(entity_name=entity_name, **kwargs)
        
    def query_specific_entity(
        self, 
        entity_name, 
        kgdb_name='neo4j', 
        hops=2
        ):

        self.use_database(kgdb_name)
        def query(tx, entity_name, hops):
            result = tx.run(f"""
            MATCH (n {{name: $entity_name}})-[r*1..{hops}]->(m)
            RETURN n.name AS node_name, r, m.name AS neighbor_name
            """, entity_name=entity_name)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, entity_name, hops)
        
    def query_all_nodes_and_relationships(
        self, 
        kgdb_name='neo4j', 
        hops = 2
        ):

        self.use_database(kgdb_name)
        def query(tx, hops):
            result = tx.run(f"""
            MATCH (n)-[r*1..{hops}]->(m)
            RETURN n, r, m
            """)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, hops)
    
    def query_by_relationship_type(
        self, 
        relationship_type, 
        kgdb_name='neo4j', 
        hops = 2
        ):

        self.use_database(kgdb_name)
        def query(tx, relationship_type, hops):
            result = tx.run(f"""
            MATCH (n)-[r:`{relationship_type}`*1..{hops}]->(m)
            RETURN n, r, m
            """)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, relationship_type, hops)
        
    def query_entity_like(
        self, 
        keyword, 
        kgdb_name='neo4j', 
        hops = 2
        ):
        self.use_database(kgdb_name)
        def query(tx, keyword, hops):
            result = tx.run(f"""
            MATCH (n:Entity)
            WHERE n.name CONTAINS $keyword
            MATCH (n)-[r*1..{hops}]->(m)
            RETURN n, r, m
            """, keyword=keyword)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, keyword, hops)
    
    def query_node_info(
        self, 
        node_name, 
        kgdb_name='neo4j', 
        hops = 2
        ):
        self.use_database(kgdb_name)
        def query(tx, node_name, hops):
            result = tx.run(f"""
            MATCH (n {{name: $node_name}})
            OPTIONAL MATCH (n)-[r*1..{hops}]->(m)
            RETURN n, r, m
            """, node_name=node_name)
            return result.values()

        with self.driver.session() as session:
            return session.execute_read(query, node_name, hops)
