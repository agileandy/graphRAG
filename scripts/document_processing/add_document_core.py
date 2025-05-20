"""Script to add a document to the GraphRAG system."""

import argparse
import logging
import os
import re
import sys
import uuid
from typing import Any

import PyPDF2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.processing.concept_extractor import ConceptExtractor
from src.processing.duplicate_detector import DuplicateDetector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RELATIONSHIP_PATTERNS = {
    "DEFINES_CONCEPT": [" defines ", " is defined as ", " refers to ", " means "],
    "IS_A": [" is a ", " is an ", " is type of ", " is kind of "],
    "HAS_PART": [" has ", " contains ", " includes ", " consists of "],
    "USED_FOR": [" is used for ", " is used to ", " enables ", " allows "],
    "IMPLEMENTS_METHOD": [" implements ", " uses ", " employs ", " utilizes "],
    "HAS_ATTRIBUTE": [" has attribute ", " has property ", " is characterized by "],
    "EXAMPLE_OF": [" is example of ", " illustrates ", " demonstrates "],
    "REQUIRES_INPUT": [" requires ", " needs ", " depends on "],
    "STEP_IN_PROCESS": [" follows ", " precedes ", " comes after ", " comes before "],
    "COMPARES_WITH": [
        " compared to ",
        " versus ",
        " as opposed to ",
        " in contrast to ",
    ],
}

PROMPT_ENGINEERING_CONCEPTS = {
    "prompt engineering": "PE",
    "chain of thought": "COT",
    "few-shot learning": "FSL",
    "zero-shot learning": "ZSL",
    "in-context learning": "ICL",
    "retrieval augmented generation": "RAG",
    "prompt template": "PT",
    "system prompt": "SP",
    "user prompt": "UP",
    "assistant prompt": "AP",
    "prompt chaining": "PC",
    "prompt tuning": "PTU",
    "prompt optimization": "PO",
    "prompt injection": "PI",
    "prompt leaking": "PL",
    "prompt hacking": "PH",
    "jailbreaking": "JB",
    "role prompting": "RP",
    "persona prompting": "PP",
    "instruction prompting": "IP",
    "task-specific prompting": "TSP",
    "self-consistency": "SC",
    "tree of thought": "TOT",
    "reasoning": "RE",
    "step-by-step": "SBS",
    "fine-tuning": "FT",
    "parameter efficient fine-tuning": "PEFT",
    "low-rank adaptation": "LORA",
    "knowledge graph": "KG",
    "vector database": "VDB",
    "embedding": "EMB",
    "token": "TOK",
    "tokenization": "TKZ",
    "temperature": "TEMP",
    "top-p sampling": "TPS",
    "top-k sampling": "TKS",
    "beam search": "BS",
    "greedy decoding": "GD",
    "hallucination": "HAL",
    "context window": "CW",
    "attention mechanism": "AM",
    "transformer": "TR",
    "large language model": "LLM",
    "generative ai": "GAI",
    "natural language processing": "NLP",
    "natural language understanding": "NLU",
    "natural language generation": "NLG",
    "semantic search": "SS",
    "similarity search": "SIS",
    "cosine similarity": "CS",
    "vector embedding": "VE",
    "text embedding": "TE",
    "document embedding": "DE",
    "sentence embedding": "SE",
    "word embedding": "WE",
    "contextual embedding": "CE",
    "knowledge distillation": "KD",
    "knowledge extraction": "KE",
    "knowledge representation": "KR",
    "knowledge base": "KB",
    "ontology": "ONT",
    "taxonomy": "TAX",
    "semantic network": "SN",
    "semantic web": "SW",
    "semantic triple": "ST",
    "entity extraction": "EE",
    "named entity recognition": "NER",
    "relation extraction": "RE",
    "information extraction": "IE",
    "information retrieval": "IR",
    "question answering": "QA",
    "chatbot": "CB",
    "conversational ai": "CAI",
    "dialogue system": "DS",
    "dialogue management": "DM",
    "dialogue state tracking": "DST",
    "dialogue policy": "DP",
    "dialogue generation": "DG",
    "dialogue understanding": "DU",
    "dialogue context": "DC",
    "dialogue history": "DH",
    "dialogue turn": "DT",
    "dialogue act": "DA",
    "dialogue intent": "DI",
    "dialogue knowledge": "DK",
    "dialogue feedback": "DF",
    "dialogue optimization": "DO",
    "dialogue learning": "DL",
    "dialogue domain": "DD",
}


def extract_text_from_pdf(pdf_path: str) -> str:
    logger.info(f"Extracting text from {os.path.basename(pdf_path)}...")
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            logger.info(
                f"  Extracted {len(text.split())} words from {num_pages} pages."
            )
            return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current_chunk = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) + 1 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:]
            last_sentence_in_overlap_match = re.search(
                r"(?:[.!?]\s+|^)([^.!?]*)$", overlap_text
            )
            if (
                last_sentence_in_overlap_match
                and last_sentence_in_overlap_match.group(1).strip()
            ):
                current_chunk = last_sentence_in_overlap_match.group(1).strip() + " "
            else:
                current_chunk = overlap_text.strip() + " "
        current_chunk += sentence + " "
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    logger.info(
        f"  Created {len(chunks)} chunks from text (target size: {chunk_size}, overlap: {overlap})"
    )
    return chunks


def extract_entities_from_metadata(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    entities = []
    if "concepts" in metadata and metadata["concepts"]:
        concept_input = metadata["concepts"]
        concept_names = []
        if isinstance(concept_input, str):
            concept_names = [c.strip() for c in concept_input.split(",") if c.strip()]
        elif isinstance(concept_input, list):
            concept_names = [str(c).strip() for c in concept_input if str(c).strip()]
        else:
            logger.warning(
                f"Metadata 'concepts' field is of unexpected type: {type(concept_input)}"
            )
        for concept_name in concept_names:
            concept_id = f"concept-meta-{concept_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
            entities.append(
                {
                    "id": concept_id,
                    "name": concept_name,
                    "type": "Concept",
                    "source": "metadata",
                }
            )
    return entities


def extract_entities_from_text(
    text: str, domain: str | None = None
) -> list[dict[str, Any]]:
    entities = []
    common_keywords = {
        "machine learning": "ML",
        "neural network": "NN",
        "deep learning": "DL",
        "artificial intelligence": "AI",
        "natural language processing": "NLP",
        "computer vision": "CV",
        "reinforcement learning": "RL",
        "supervised learning": "SL",
        "unsupervised learning": "UL",
        "transformer": "TR",
        "attention mechanism": "AM",
        "convolutional neural network": "CNN",
        "recurrent neural network": "RNN",
        "long short-term memory": "LSTM",
        "gated recurrent unit": "GRU",
        "generative adversarial network": "GAN",
        "transfer learning": "TL",
        "fine-tuning": "FT",
        "backpropagation": "BP",
        "gradient descent": "GD",
        "retrieval-augmented generation": "RAG",
        "graphrag": "GRAG",
        "knowledge graph": "KG",
        "vector database": "VDB",
        "embedding": "EMB",
        "hybrid search": "HS",
        "deduplication": "DD",
        "large language model": "LLM",
        "neo4j": "NEO",
        "chromadb": "CHROMA",
    }
    domain_keywords = {
        "AI": {
            "prompt engineering": "PE",
            "chain of thought": "COT",
            "few-shot learning": "FSL",
            "zero-shot learning": "ZSL",
            "multimodal": "MM",
            "text-to-image": "T2I",
            "diffusion model": "DM",
            "stable diffusion": "SD",
            "dall-e": "DALLE",
            "midjourney": "MJ",
            "gpt": "GPT",
            "bert": "BERT",
            "t5": "T5",
            "llama": "LLAMA",
            "claude": "CLAUDE",
        },
        "Programming": {
            "python": "PY",
            "javascript": "JS",
            "typescript": "TS",
            "java": "JAVA",
            "c++": "CPP",
            "rust": "RUST",
            "go": "GO",
            "docker": "DOCKER",
            "kubernetes": "K8S",
            "microservices": "MS",
            "api": "API",
            "rest": "REST",
            "graphql": "GQL",
            "database": "DB",
            "sql": "SQL",
            "nosql": "NOSQL",
            "git": "GIT",
            "ci/cd": "CICD",
            "devops": "DEVOPS",
        },
    }
    keywords_to_use = common_keywords.copy()
    if domain and domain in domain_keywords:
        keywords_to_use.update(domain_keywords[domain])
    text_lower = text.lower()
    found_entity_names = set()
    for keyword, abbr in keywords_to_use.items():
        if keyword.lower() in text_lower:
            normalized_name = keyword.title()
            if normalized_name not in found_entity_names:
                entity_id = f"concept-kw-{abbr.lower()}-{uuid.uuid4().hex[:8]}"
                entities.append(
                    {
                        "id": entity_id,
                        "name": normalized_name,
                        "type": "Concept",
                        "abbreviation": abbr,
                        "domain": domain or "common",
                        "source": "keyword_text",
                    }
                )
                found_entity_names.add(normalized_name)
    return entities


def extract_entities(
    text: str,
    metadata: dict[str, Any] | None = None,
    extractor_instance: ConceptExtractor | None = None,
    domain: str | None = "general",
) -> list[dict[str, Any]]:
    all_entities_map: dict[str, dict[str, Any]] = {}
    if extractor_instance and extractor_instance.use_llm:
        try:
            logger.info("Attempting entity extraction using LLM...")
            llm_output = extractor_instance.extract_concepts_llm(text)
            llm_concepts = llm_output.get("concepts", [])
            if llm_concepts:
                logger.info(f"LLM extracted {len(llm_concepts)} concepts.")
                for concept in llm_concepts:
                    name_lower = concept.get("name", "").lower()
                    if name_lower:
                        if "id" not in concept or not concept["id"]:
                            concept["id"] = (
                                f"concept-llm-{name_lower.replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
                            )
                        concept["source"] = "llm"
                        all_entities_map[name_lower] = concept
            else:
                logger.info("LLM did not extract any concepts.")
        except Exception as e:
            logger.error(f"Error during LLM entity extraction: {e}", exc_info=True)
    pe_keywords_concepts = []
    for concept_name_pe, abbr_pe in PROMPT_ENGINEERING_CONCEPTS.items():
        name_pe_lower = concept_name_pe.lower()
        if name_pe_lower in text.lower() and name_pe_lower not in all_entities_map:
            pe_id = f"concept-pe-{abbr_pe.lower()}-{uuid.uuid4().hex[:8]}"
            entity_data = {
                "id": pe_id,
                "name": concept_name_pe.title(),
                "type": "PromptEngineeringConcept",
                "abbreviation": abbr_pe,
                "source": "keyword_pe",
            }
            all_entities_map[name_pe_lower] = entity_data
            pe_keywords_concepts.append(entity_data)
    if pe_keywords_concepts:
        logger.info(f"Extracted {len(pe_keywords_concepts)} PE concepts via keywords.")
    keyword_text_concepts = extract_entities_from_text(text, domain)
    newly_added_keyword_concepts = 0
    for concept in keyword_text_concepts:
        name_lower = concept["name"].lower()
        if name_lower not in all_entities_map:
            all_entities_map[name_lower] = concept
            newly_added_keyword_concepts += 1
    if newly_added_keyword_concepts > 0:
        logger.info(
            f"Extracted {newly_added_keyword_concepts} additional general/domain concepts via keywords."
        )
    if metadata:
        metadata_concepts = extract_entities_from_metadata(metadata)
        for concept in metadata_concepts:
            name_lower = concept["name"].lower()
            all_entities_map[name_lower] = concept
        if metadata_concepts:
            logger.info(f"Processed {len(metadata_concepts)} concepts from metadata.")
    final_entities = list(all_entities_map.values())
    logger.info(f"Total unique entities extracted: {len(final_entities)}")
    return final_entities


def _extract_relationships_pattern_based(
    entities: list[dict[str, Any]],
    text_lower: str,
    relationship_patterns: dict[str, list[str]],
    logger_instance: logging.Logger,
) -> list[dict[str, Any]]:
    pattern_relationships = []
    valid_entities = [e for e in entities if e.get("name") and e.get("id")]
    if len(valid_entities) < 2:
        return []
    logger_instance.info(
        f"Attempting pattern-based relationship extraction for {len(valid_entities)} entities."
    )
    for i, source_entity in enumerate(valid_entities):
        source_name_lower = source_entity["name"].lower()
        source_id = source_entity["id"]
        for j, target_entity in enumerate(valid_entities):
            if i == j:
                continue
            target_name_lower = target_entity["name"].lower()
            target_id = target_entity["id"]
            rel_type, strength, found_pattern = "RELATED_TO", 0.5, False
            for p_type, patterns in relationship_patterns.items():
                if found_pattern:
                    break
                for pattern in patterns:
                    if f"{source_name_lower}{pattern}{target_name_lower}" in text_lower:
                        rel_type, strength, found_pattern = p_type, 0.8, True
                        break
            if found_pattern:
                pattern_relationships.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "type": rel_type,
                        "description": f"{source_entity['name']} is {rel_type.lower().replace('_', ' ')} {target_entity['name']}",
                        "strength": strength,
                        "method": "pattern_based",
                    }
                )
    logger_instance.info(
        f"Pattern-based extraction found {len(pattern_relationships)} relationships."
    )
    return pattern_relationships


def _extract_relationships_basic(
    entities: list[dict[str, Any]], text_lower: str, logger_instance: logging.Logger
) -> list[dict[str, Any]]:
    basic_relationships = []
    valid_entities = [e for e in entities if e.get("name") and e.get("id")]
    if len(valid_entities) < 2:
        logger_instance.debug("Basic Rel: Not enough valid entities for co-occurrence.")
        return basic_relationships
    for i in range(len(valid_entities)):
        for j in range(i + 1, len(valid_entities)):
            e1, e2 = valid_entities[i], valid_entities[j]
            if e1["name"].lower() in text_lower and e2["name"].lower() in text_lower:
                basic_relationships.append(
                    {
                        "source_id": e1["id"],
                        "target_id": e2["id"],
                        "type": "RELATED_TO",
                        "description": f"{e1['name']} co-occurs with {e2['name']} in text (simplified)",
                        "strength": 0.3,
                        "method": "basic_cooccurrence",
                    }
                )
    logger_instance.info(
        f"Basic co-occurrence (simplified) found {len(basic_relationships)} relationships."
    )
    return basic_relationships


def extract_relationships(
    entities: list[dict[str, Any]], text: str, extractor: ConceptExtractor
) -> list[dict[str, Any]]:
    logger.info(f"Starting relationship extraction for {len(entities)} entities.")
    all_extracted_relationships = []
    valid_entities = [e for e in entities if e.get("name") and e.get("id")]
    if len(valid_entities) < 2:
        logger.info(
            f"Not enough valid entities (found {len(valid_entities)}), skipping relationship extraction."
        )
        return []
    llm_relationships = []
    if extractor.use_llm:
        try:
            logger.info(
                f"Attempting LLM relationship extraction for {len(valid_entities)} entities..."
            )
            llm_output = extractor.extract_concepts_llm(text)
            raw_llm_rels = llm_output.get("relationships", [])
            if raw_llm_rels:
                logger.info(f"LLM returned {len(raw_llm_rels)} raw relationships.")
                for rel_data in raw_llm_rels:
                    s_name, t_name = rel_data.get("source"), rel_data.get("target")
                    if not s_name or not t_name:
                        continue
                    rel_type = (
                        rel_data.get("type", "RELATED_TO").upper().replace(" ", "_")
                    )
                    desc = rel_data.get(
                        "description",
                        f"{s_name} is {rel_type.lower().replace('_', ' ')} {t_name}",
                    )
                    strength = float(rel_data.get("strength", 0.6))
                    s_entity = next(
                        (e for e in valid_entities if e["name"] == s_name), None
                    )
                    t_entity = next(
                        (e for e in valid_entities if e["name"] == t_name), None
                    )
                    if (
                        s_entity
                        and t_entity
                        and s_entity.get("id") != t_entity.get("id")
                    ):
                        llm_relationships.append(
                            {
                                "source_id": s_entity["id"],
                                "target_id": t_entity["id"],
                                "type": rel_type,
                                "description": desc,
                                "strength": strength,
                                "method": "llm",
                            }
                        )
                    elif s_name and t_name:
                        logger.warning(
                            f"LLM Rel: Could not map to entity IDs: '{s_name}' -> '{t_name}'."
                        )
                logger.info(f"Processed {len(llm_relationships)} LLM relationships.")
            else:
                logger.info("LLM did not return any relationships.")
        except Exception as e:
            logger.error(f"Error in LLM relationship extraction: {e}", exc_info=True)
    else:
        logger.info("LLM use disabled, skipping LLM relationship extraction.")
    all_extracted_relationships.extend(llm_relationships)
    text_lower = text.lower()
    pattern_rels = _extract_relationships_pattern_based(
        valid_entities, text_lower, RELATIONSHIP_PATTERNS, logger
    )
    all_extracted_relationships.extend(pattern_rels)
    should_fallback = (
        (not llm_relationships and not pattern_rels)
        if extractor.use_llm
        else (not pattern_rels)
    )
    if should_fallback:
        logger.info(
            "No relationships from LLM/patterns, falling back to basic co-occurrence."
        )
        basic_rels = _extract_relationships_basic(valid_entities, text_lower, logger)
        all_extracted_relationships.extend(basic_rels)
    final_rels, seen_map = [], {}
    priority = {"llm": 3, "pattern_based": 2, "basic_cooccurrence": 1}
    for rel in all_extracted_relationships:
        key = (rel["source_id"], rel["target_id"], rel["type"])
        cur_p = priority.get(rel.get("method", ""), 0)
        cur_s = float(rel.get("strength", 0.0))
        if (
            key not in seen_map
            or cur_p > priority.get(seen_map[key].get("method", ""), 0)
            or (
                cur_p == priority.get(seen_map[key].get("method", ""), 0)
                and cur_s > float(seen_map[key].get("strength", 0.0))
            )
        ):
            seen_map[key] = rel
    final_rels = list(seen_map.values())
    logger.info(
        f"Finished relationship extraction. Found {len(final_rels)} unique relationships."
    )
    return final_rels


def _create_neo4j_document_node(neo4j_db: Neo4jDatabase, properties: dict[str, Any]) -> None:
    query = """
    MERGE (d:Document {id: $id})
    ON CREATE SET d += $props, d.created_at = datetime(), d.updated_at = datetime()
    ON MATCH SET d += $props, d.updated_at = datetime()
    RETURN d.id AS id
    """
    props_to_set = {k: v for k, v in properties.items() if k != "id"}
    neo4j_db.run_query(query, {"id": properties["id"], "props": props_to_set})
    logger.info(f"Ensured Document node: {properties['id']}")


def _create_neo4j_chunk_node(neo4j_db: Neo4jDatabase, properties: dict[str, Any]) -> None:
    query = """
    MERGE (c:Chunk {id: $id})
    ON CREATE SET c += $props, c.created_at = datetime()
    ON MATCH SET c += $props
    RETURN c.id AS id
    """
    props_to_set = {k: v for k, v in properties.items() if k != "id"}
    neo4j_db.run_query(query, {"id": properties["id"], "props": props_to_set})
    logger.info(f"Ensured Chunk node: {properties['id']}")


def _link_document_to_chunk(neo4j_db: Neo4jDatabase, doc_id: str, chunk_id: str) -> None:
    query = """
    MATCH (d:Document {id: $doc_id})
    MATCH (c:Chunk {id: $chunk_id})
    MERGE (d)-[:HAS_CHUNK]->(c)
    """
    neo4j_db.run_query(query, {"doc_id": doc_id, "chunk_id": chunk_id})
    logger.info(f"Linked Document {doc_id} to Chunk {chunk_id}")


def _add_neo4j_entity_with_linking(
    neo4j_db: Neo4jDatabase,
    entity_data: dict[str, Any],
    target_node_id: str,
    target_node_label: str,
    link_type: str = "MENTIONS_CONCEPT",
) -> None:
    entity_id = entity_data.get("id", f"concept-{uuid.uuid4().hex}")
    entity_name = entity_data.get("name")
    entity_type_label = entity_data.get("type", "Concept")  # This is the Label
    normalized_name = entity_name.lower().strip() if entity_name else ""

    params_for_node = {
        "id": entity_id,
        "name": entity_name,
        "type": entity_type_label,
        "normalized_name": normalized_name,
        "description": entity_data.get("description", ""),
        "relevance": float(entity_data.get("relevance", 1.0)),  # Ensure float
        "source": entity_data.get("source", "unknown"),
    }
    # Add other properties from entity_data if they exist and are Neo4j-compatible
    for key, value in entity_data.items():
        if key not in params_for_node and isinstance(
            value, str | int | float | bool | list
        ):  # Neo4j compatible types
            params_for_node[key] = value

    # Use dynamic labels with caution or ensure entity_type_label is sanitized
    # For simplicity, assuming entity_type_label is a valid Neo4j Label like "Concept", "Person"
    # Parameterizing labels directly is not standard. We construct the query string.
    # Ensure entity_type_label is a safe string (e.g., alphanumeric)
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", entity_type_label):
        logger.error(
            f"Invalid entity type label for Neo4j: {entity_type_label}. Defaulting to 'Concept'."
        )
        entity_type_label = "Concept"
        params_for_node["type"] = "Concept"  # Update the type property as well

    merge_query = f"""
    MERGE (c:{entity_type_label} {{id: $id}})
    ON CREATE SET c = $params, c.created_at = datetime(), c.updated_at = datetime()
    ON MATCH SET c += $params, c.updated_at = datetime()
    """
    # For ON MATCH, we use c += $params to update existing properties and add new ones.
    # $params should not include 'id' for the SET c += $params part if id is immutable after creation.
    # However, MERGE uses id for matching.
    # A cleaner way for ON MATCH might be specific SET c.prop = $params.prop for updatable fields.
    # For now, c += $params will update all provided params.

    neo4j_db.run_query(merge_query, {"id": entity_id, "params": params_for_node})

    link_query = f"""
    MATCH (t:{target_node_label} {{id: $target_node_id}})
    MATCH (c:{entity_type_label} {{id: $entity_id}})
    MERGE (t)-[r:{link_type}]->(c)
    RETURN type(r)
    """
    neo4j_db.run_query(
        link_query, {"target_node_id": target_node_id, "entity_id": entity_id}
    )
    logger.debug(
        f"Linked {target_node_label} {target_node_id} to {entity_type_label} {entity_id} ({entity_name})"
    )


def _add_neo4j_relationships(
    neo4j_db: Neo4jDatabase, relationships: list[dict[str, Any]]
) -> None:
    for rel in relationships:
        rel_type = rel.get("type", "RELATED_TO")
        if not re.match(
            r"^[A-Z_]+$", rel_type
        ):  # Basic validation for relationship type
            logger.warning(
                f"Invalid relationship type '{rel_type}'. Skipping relationship: {rel}"
            )
            continue

        query = f"""
        MATCH (c1 {{id: $source_id}})
        MATCH (c2 {{id: $target_id}})
        MERGE (c1)-[r:{rel_type}]->(c2)
        ON CREATE SET r.strength = $strength, r.description = $description, r.method = $method, r.created_at = datetime()
        ON MATCH SET r.strength = CASE WHEN r.strength < $strength THEN $strength ELSE r.strength END,
                     r.description = $description, r.method = $method, r.updated_at = datetime()
        RETURN type(r)
        """
        params = {
            "source_id": rel["source_id"],
            "target_id": rel["target_id"],
            "strength": float(rel.get("strength", 0.5)),
            "description": rel.get("description", ""),
            "method": rel.get("method", "unknown"),
        }
        neo4j_db.run_query(query, params)
    logger.info(f"Processed {len(relationships)} entity relationships in Neo4j.")


def add_document_to_graphrag(
    text: str,
    metadata: dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    duplicate_detector: DuplicateDetector,
    use_chunking_for_pdf: bool = False,
    chunk_size: int = 4000,
    overlap: int = 400,
) -> dict[str, Any] | None:
    doc_title = metadata.get("title", metadata.get("filename", "Unknown Title"))
    doc_source = metadata.get("source", metadata.get("file_path", "Unknown Source"))
    document_type = metadata.get("document_type", "text")
    domain = metadata.get("domain", "general")
    logger.info(
        f"Attempting to add document: '{doc_title}' from '{doc_source}' (type: {document_type}, domain: {domain})"
    )

    local_extractor = ConceptExtractor(use_nlp=False, use_llm=True, domain=domain)
    logger.info(
        f"ConceptExtractor initialized for '{doc_title}' (LLM usage: {local_extractor.use_llm})"
    )

    try:
        full_text_hash = duplicate_detector.generate_document_hash(text)
        metadata["full_text_hash"] = full_text_hash
        is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(
            text, metadata
        )
        if is_dup:
            logger.info(
                f"Skipping duplicate document: '{doc_title}' (ID: {existing_doc_id}, Method: {method})"
            )
            return {
                "status": "duplicate",
                "document_id": existing_doc_id,
                "message": "Document is a duplicate.",
            }

        logger.info(f"Processing new document: '{doc_title}'")
        texts_to_process_with_meta = []
        is_pdf_and_chunking = document_type == "pdf" and use_chunking_for_pdf

        if is_pdf_and_chunking:
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            if not chunks:
                logger.warning(
                    f"Chunking of '{doc_title}' resulted in no processable chunks."
                )
                return {
                    "error": f"No processable chunks for '{doc_title}'.",
                    "status": "failure",
                }
            for i, chunk_content in enumerate(chunks):
                chunk_meta = metadata.copy()
                chunk_meta.update(
                    {
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_hash": duplicate_detector.generate_document_hash(
                            chunk_content
                        ),
                    }
                )
                texts_to_process_with_meta.append(
                    {
                        "text": chunk_content,
                        "metadata": chunk_meta,
                        "is_chunk": True,
                        "chunk_idx": i,
                    }
                )
        else:
            if "hash" not in metadata:
                metadata["hash"] = full_text_hash
            texts_to_process_with_meta.append(
                {"text": text, "metadata": metadata, "is_chunk": False, "chunk_idx": 0}
            )

        doc_id = f"doc-{uuid.uuid4()}"
        parent_doc_props = {
            "id": doc_id,
            "title": doc_title,
            "source": doc_source,
            "document_type": document_type,
            "hash": full_text_hash,
            "word_count": len(text.split()),
            "char_count": len(text),
        }
        for key in [
            "author",
            "category",
            "subcategory",
            "publication_date",
            "url",
        ]:  # Add more relevant fields
            if key in metadata:
                parent_doc_props[key] = metadata[key]
        _create_neo4j_document_node(neo4j_db, parent_doc_props)

        all_chunk_results, overall_entities_map, overall_relationships_list = [], {}, []

        for item in texts_to_process_with_meta:
            cur_text, cur_meta, is_chunk_item, chunk_idx_val = (
                item["text"],
                item["metadata"],
                item["is_chunk"],
                item["chunk_idx"],
            )
            log_prefix = (
                f"Chunk {chunk_idx_val + 1}/{len(texts_to_process_with_meta)}"
                if is_chunk_item
                else "Document"
            )
            try:
                entities = extract_entities(
                    cur_text,
                    cur_meta,
                    extractor_instance=local_extractor,
                    domain=domain,
                )
                logger.info(
                    f"{log_prefix}: Extracted {len(entities)} entities for '{doc_title}'."
                )
                for entity in entities:
                    name_l = entity["name"].lower()
                    if name_l not in overall_entities_map:
                        overall_entities_map[name_l] = entity
                    elif "id" not in overall_entities_map[name_l] and "id" in entity:
                        overall_entities_map[name_l]["id"] = entity["id"]

                relationships = extract_relationships(
                    entities, cur_text, extractor=local_extractor
                )
                logger.info(
                    f"{log_prefix}: Extracted {len(relationships)} relationships for '{doc_title}'."
                )
                overall_relationships_list.extend(relationships)

                current_target_node_id_str: str
                current_target_label: str

                if is_chunk_item:
                    chunk_node_id_val = (
                        f"chunk-{doc_id}-{chunk_idx_val}-{uuid.uuid4().hex[:8]}"
                    )
                    chunk_props = {
                        "id": chunk_node_id_val,
                        "document_id": doc_id,
                        "chunk_index": chunk_idx_val,
                        "text_hash": cur_meta.get("chunk_hash"),
                        "char_count": len(cur_text),
                        "word_count": len(cur_text.split()),
                    }
                    _create_neo4j_chunk_node(neo4j_db, chunk_props)
                    _link_document_to_chunk(neo4j_db, doc_id, chunk_node_id_val)
                    current_target_node_id_str = chunk_node_id_val
                    current_target_label = "Chunk"

                    vec_meta = {
                        k: v
                        for k, v in cur_meta.items()
                        if isinstance(v, str | int | float | bool)
                    }
                    vec_meta.update(
                        {
                            "document_id": doc_id,
                            "chunk_id": chunk_node_id_val,
                            "title": doc_title,
                        }
                    )  # Ensure title for vector
                    vector_db.add_documents(
                        ids=[chunk_node_id_val],
                        documents=[cur_text],
                        metadatas=[vec_meta],
                    )
                    logger.info(
                        f"{log_prefix}: Added chunk {chunk_node_id_val} to vector DB."
                    )
                else:
                    current_target_node_id_str = doc_id
                    current_target_label = "Document"

                for (
                    entity_data
                ) in entities:  # Link entities to the current target (doc or chunk)
                    _add_neo4j_entity_with_linking(
                        neo4j_db,
                        entity_data,
                        current_target_node_id_str,
                        current_target_label,
                    )

                all_chunk_results.append(
                    {"status": "success", "id": current_target_node_id_str}
                )
            except Exception as e:
                logger.error(
                    f"{log_prefix}: Error processing for '{doc_title}': {e}",
                    exc_info=True,
                )
                all_chunk_results.append(
                    {
                        "error": f"Processing failed for {log_prefix}",
                        "status": "failure",
                    }
                )
                continue

        if not is_pdf_and_chunking:
            vec_meta_full = {
                k: v
                for k, v in metadata.items()
                if isinstance(v, str | int | float | bool)
            }
            vec_meta_full.update(
                {"document_id": doc_id, "title": doc_title, "source": doc_source}
            )
            vector_db.add_documents(
                ids=[doc_id], documents=[text], metadatas=[vec_meta_full]
            )
            logger.info(f"Added full document {doc_id} to vector DB for '{doc_title}'.")

        if overall_relationships_list:
            _add_neo4j_relationships(neo4j_db, overall_relationships_list)

        successful_ops = [
            res for res in all_chunk_results if res.get("status") == "success"
        ]
        if len(successful_ops) == len(texts_to_process_with_meta):
            return {
                "status": "success",
                "document_id": doc_id,
                "message": f"Document '{doc_title}' added.",
                "entities_count": len(overall_entities_map),
                "relationships_count": len(
                    set(
                        (r["source_id"], r["target_id"], r["type"])
                        for r in overall_relationships_list
                    )
                ),
            }
        else:
            return {
                "status": "partial_failure",
                "document_id": doc_id,
                "message": f"Document '{doc_title}' processed with errors.",
                "details": all_chunk_results,
            }
    except Exception as e:
        logger.error(
            f"Unhandled error adding document '{doc_title}': {e}", exc_info=True
        )
        return {"error": f"Unhandled error: {e}", "status": "failure"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a document to the GraphRAG system."
    )
    parser.add_argument(
        "--text", type=str, help="Document text (if not providing a file path)."
    )
    parser.add_argument(
        "--file-path", type=str, help="Path to the document file (PDF or TXT)."
    )
    parser.add_argument("--title", type=str, help="Document title.")
    parser.add_argument("--author", type=str, help="Document author.")
    parser.add_argument("--category", type=str, help="Document category.")
    parser.add_argument(
        "--source", type=str, help="Document source (e.g., URL, filename)."
    )
    parser.add_argument(
        "--domain", type=str, default="general", help="Domain for entity extraction."
    )
    parser.add_argument(
        "--use-chunking-for-pdf",
        action="store_true",
        help="Enable chunking for PDF documents.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4000,
        help="Target chunk size for PDF chunking.",
    )
    parser.add_argument(
        "--overlap", type=int, default=400, help="Overlap size for PDF chunking."
    )
    args = parser.parse_args()

    if not args.text and not args.file_path:
        parser.error("Either --text or --file-path must be provided.")

    doc_text = args.text
    doc_metadata = {
        "title": args.title or "Untitled Document",
        "author": args.author or "Unknown",
        "category": args.category or "General",
        "source": args.source or args.file_path,
        "document_type": "text",
        "domain": args.domain,
    }

    if args.file_path:
        if not os.path.exists(args.file_path):
            logger.error(f"File not found: {args.file_path}")
            sys.exit(1)
        doc_metadata["source"] = args.source or args.file_path
        if args.title is None:
            doc_metadata["title"] = os.path.splitext(os.path.basename(args.file_path))[
                0
            ]
        if args.file_path.lower().endswith(".pdf"):
            doc_text = extract_text_from_pdf(args.file_path)
            doc_metadata["document_type"] = "pdf"
            if not doc_text:
                logger.error(f"Could not extract text from PDF: {args.file_path}")
                sys.exit(1)
        elif args.file_path.lower().endswith(".txt"):
            try:
                with open(args.file_path, encoding="utf-8") as f:
                    doc_text = f.read()
                doc_metadata["document_type"] = "txt"
            except Exception as e:
                logger.error(f"Error reading text file {args.file_path}: {e}")
                sys.exit(1)
        else:
            logger.error(f"Unsupported file type: {args.file_path}. PDF or TXT only.")
            sys.exit(1)

    if not doc_text:
        logger.error("No text content to process.")
        sys.exit(1)

    neo4j_db_instance = None
    try:
        neo4j_db_instance = Neo4jDatabase()
        vector_db_instance = VectorDatabase()
        duplicate_detector_instance = DuplicateDetector(vector_db_instance)  # Corrected

        logger.info(f"Processing document: {doc_metadata['title']}")
        result = add_document_to_graphrag(
            text=doc_text,
            metadata=doc_metadata,
            neo4j_db=neo4j_db_instance,
            vector_db=vector_db_instance,
            duplicate_detector=duplicate_detector_instance,
            use_chunking_for_pdf=(
                doc_metadata["document_type"] == "pdf" and args.use_chunking_for_pdf
            ),
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
        if result:
            logger.info(
                f"Result for '{doc_metadata['title']}': {result.get('status')}, Message: {result.get('message')}"
            )
            if result.get("status") == "success":
                logger.info(
                    f"Entities: {result.get('entities_count')}, Relationships: {result.get('relationships_count')}"
                )
        else:
            logger.error(
                f"Failed to add document '{doc_metadata['title']}'. No result object returned."
            )
    except Exception as e:
        logger.error(f"An error occurred in main: {e}", exc_info=True)
    finally:
        if neo4j_db_instance:
            neo4j_db_instance.close()


if __name__ == "__main__":
    main()
