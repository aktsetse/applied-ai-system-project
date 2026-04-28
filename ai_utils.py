import os
import logging
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from dotenv import load_load

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Knowledge base for number facts
NUMBER_FACTS = [
    "1 is the multiplicative identity.",
    "2 is the only even prime number.",
    "3 is the first odd prime number.",
    "4 is a perfect square (2^2).",
    "5 is the number of Platonic solids.",
    "6 is a perfect number (sum of divisors 1+2+3=6).",
    "7 is considered a lucky number in many cultures.",
    "8 is the number of bits in a byte.",
    "9 is a perfect square (3^2).",
    "10 is the base of the decimal system.",
    "11 is the smallest two-digit prime.",
    "12 is the number of months in a year.",
    "13 is considered unlucky in some cultures.",
    "14 is Valentine's Day date.",
    "15 is the number of days in a fortnight.",
    "16 is a perfect square (4^2).",
    "17 is a prime number.",
    "18 is the age of adulthood in many countries.",
    "19 is a prime number.",
    "20 is the number of fingers and toes.",
    "21 is the legal drinking age in the US.",
    "22 is the number of letters in the Hebrew alphabet.",
    "23 is a prime number.",
    "24 is the number of hours in a day.",
    "25 is a perfect square (5^2).",
    "50 is half of 100.",
    "100 is a perfect square (10^2).",
    "Numbers can be even or odd.",
    "Prime numbers have only two divisors: 1 and themselves.",
    "Perfect squares are squares of integers.",
    "Even numbers are divisible by 2.",
    "Odd numbers are not divisible by 2.",
]

def create_knowledge_base() -> FAISS:
    """Create a FAISS vector store from number facts."""
    try:
        embeddings = OpenAIEmbeddings()
        documents = [Document(page_content=fact) for fact in NUMBER_FACTS]
        vectorstore = FAISS.from_documents(documents, embeddings)
        logger.info("Knowledge base created successfully.")
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to create knowledge base: {e}")
        raise

# Initialize the knowledge base
try:
    vectorstore = create_knowledge_base()
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(temperature=0.7),
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    )
except Exception as e:
    logger.error(f"Failed to initialize QA chain: {e}")
    qa_chain = None

def get_ai_insight(guess: int, secret: int, outcome: str) -> str:
    """
    Use RAG to provide an AI-generated insight about the guess or number.

    Args:
        guess: The player's guess
        secret: The secret number
        outcome: The outcome of the guess ("Win", "Too High", "Too Low")

    Returns:
        A string with AI-generated insight
    """
    if qa_chain is None:
        return "AI insights unavailable due to configuration error."

    try:
        if outcome == "Win":
            query = f"Provide an interesting fact about the number {secret}."
        else:
            query = f"Give a fun fact about the number {guess} or explain why guessing {guess} might be a good strategy."

        response = qa_chain.run(query)
        logger.info(f"AI insight generated for guess {guess}, outcome {outcome}")
        return response
    except Exception as e:
        logger.error(f"Failed to get AI insight: {e}")
        return "Sorry, I couldn't generate an insight right now."

def evaluate_ai_reliability() -> Dict[str, float]:
    """Simple reliability check for AI responses."""
    test_queries = [
        "Tell me about the number 2.",
        "What is special about 7?",
        "Explain prime numbers.",
    ]
    scores = []
    for query in test_queries:
        try:
            response = qa_chain.run(query) if qa_chain else ""
            # Simple check: response should be non-empty and contain relevant words
            if response and len(response) > 10:
                scores.append(1.0)
            else:
                scores.append(0.0)
        except:
            scores.append(0.0)

    return {
        "average_score": sum(scores) / len(scores) if scores else 0.0,
        "total_tests": len(scores),
        "passed_tests": sum(1 for s in scores if s > 0),
    }