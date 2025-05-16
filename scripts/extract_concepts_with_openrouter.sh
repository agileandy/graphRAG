#!/bin/bash
# Script to extract concepts using OpenRouter with Google Gemini 2.0 Flash and Meta Llama 4 Maverick fallback

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv-py312/bin/activate

# Set default values
COLLECTION="documents"
LIMIT=10
BATCH_SIZE=5
MIN_TEXT_LENGTH=100
CHUNK_SIZE=3000
CHUNK_OVERLAP=500
CONFIG_PATH="config/openrouter_config.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --collection)
      COLLECTION="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --batch-size)
      BATCH_SIZE="$2"
      shift 2
      ;;
    --min-text-length)
      MIN_TEXT_LENGTH="$2"
      shift 2
      ;;
    --chunk-size)
      CHUNK_SIZE="$2"
      shift 2
      ;;
    --chunk-overlap)
      CHUNK_OVERLAP="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Running concept extraction with OpenRouter (Google Gemini 2.0 Flash with Meta Llama 4 Maverick fallback)"
echo "Collection: $COLLECTION"
echo "Limit: $LIMIT"
echo "Batch size: $BATCH_SIZE"
echo "Config: $CONFIG_PATH"
echo "Chunk size: $CHUNK_SIZE"
echo "Chunk overlap: $CHUNK_OVERLAP"

# Run the extraction script
python scripts/document_processing/extract_concepts_with_llm.py \
  --collection "$COLLECTION" \
  --limit "$LIMIT" \
  --batch-size "$BATCH_SIZE" \
  --config "$CONFIG_PATH" \
  --min-text-length "$MIN_TEXT_LENGTH" \
  --chunk-size "$CHUNK_SIZE" \
  --chunk-overlap "$CHUNK_OVERLAP"

echo "Concept extraction complete"
