from llama_index.core import SimpleDirectoryReader, Settings, Document
from llama_index.core.node_parser import SentenceSplitter

from app.services.rag_provider_factory import get_llm
from app.services.nexus_resume_vector_store import get_nexus_resume_vector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _prepare_llm():
    llm = get_llm()
    Settings.llm = llm
    return llm


def _build_nodes(documents, namespace_id, doc_type):
    # Use smaller chunks for models with limited context
    text_splitter = SentenceSplitter(chunk_size=400, chunk_overlap=40)
    nodes = text_splitter.get_nodes_from_documents(documents)
    for idx, node in enumerate(nodes):
        node.metadata["resume_id"] = namespace_id
        node.metadata["doc_type"] = doc_type
        node.id_ = f"{namespace_id}_{doc_type}_{idx}"
    return nodes


def generate_query_engine(file_paths, namespace_id, read_from_text=False, jd=False):
    try:
        documents = None
        # --- Document Loading (Still needed to get text) ---
        if not file_paths:
            logger.warning("No file paths provided.")
            return None, None  # Return None for both expected values
        if not read_from_text:
            # Used for Resumes (jd=False)
            reader = SimpleDirectoryReader(input_files=[file_paths])
            documents = reader.load_data()
        else:
            # Used for JDs (jd=True, read_from_text=True)
            # We still create the Document object to hold the text
            documents = [Document(text=file_paths)]

        _prepare_llm()
        vector_store = get_nexus_resume_vector_store()
        Settings.embed_model = vector_store.embed_model

        doc_type = "jd" if jd else "resume"
        
        # Check if nodes already exist to avoid re-embedding
        if vector_store.has_nodes(namespace_id, doc_type):
            logger.info(f"Nodes already exist for {doc_type} {namespace_id}, skipping embedding")
        else:
            # Only create and add nodes if they don't exist
            nodes = _build_nodes(documents, namespace_id, doc_type)
            logger.info(f"Adding {len(nodes)} new nodes for {doc_type} {namespace_id}")
            vector_store.add_nodes(nodes)
        
        query_engine = vector_store.get_query_engine(namespace_id, doc_type)

        logger.info("Nexus RAG retriever ready for %s", doc_type)
        return query_engine, documents  # query_engine is actually a retriever now

    except Exception:
        logger.exception("Error generating Nexus query engine")
        return None, None