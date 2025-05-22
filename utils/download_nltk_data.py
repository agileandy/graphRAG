#!/usr/bin/env python3
"""Script to download required NLTK data."""

import nltk


def main() -> None:
    """Download required NLTK data."""
    print("Downloading NLTK data...")

    # Download required data
    nltk.download("punkt")
    nltk.download("averaged_perceptron_tagger")
    nltk.download("maxent_ne_chunker")
    nltk.download("words")

    print("NLTK data download complete!")


if __name__ == "__main__":
    main()
