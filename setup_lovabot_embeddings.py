#!/usr/bin/env python3
"""
Setup script for Lovabot RAG embeddings.
Run this once to process all PDF files and create embeddings.pkl file for the Lovabot chat system.
"""

from ai.ai_lovabot.ai_lovabot import add_dating_content

if __name__ == "__main__":
    print("🤖 Setting up Lovabot RAG embeddings...")
    print("This will process PDF files and create embeddings for the chat system.")
    
    result = add_dating_content()
    print(f"Result: {result}")
    print("✅ Lovabot embeddings setup complete! The chat system is now ready to use.")
