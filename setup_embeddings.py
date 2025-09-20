#!/usr/bin/env python3
"""
Setup script to generate embeddings from PDF files.
Run this once to process all PDFs and create embeddings.pkl file.
"""

from ai.ai_lovabot.ai_lovabot import add_dating_content

if __name__ == "__main__":
    print("Setting up Lovabot embeddings...")
    result = add_dating_content()
    print(f"Result: {result}")
    print("Setup complete! Embeddings are now saved and ready to use.")
