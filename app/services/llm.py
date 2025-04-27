# app/services/llm.py
import groq
from typing import Dict, Any, List
import time
from app.config import GROQ_API_KEY


class LLMService:
    def __init__(self):
        self.client = groq.Client(api_key=GROQ_API_KEY)
        self.model = "llama3-8b-8192"  # You can change this to any model Groq supports

    async def enhance_query(self, query: str) -> str:
        """
        Enhance the search query using the LLM to better understand user intent
        """
        try:
            prompt = f"""
            You are a search query enhancement system. Your task is to analyze the user's search query 
            and enhance it to improve search results. Add relevant keywords and context while 
            preserving the original intent.

            Original query: "{query}"

            Enhanced query:
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful search query enhancement assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )

            enhanced_query = response.choices[0].message.content.strip()
            return enhanced_query

        except Exception as e:
            print(f"Error enhancing query: {str(e)}")
            return query  # Return original query if enhancement fails

    async def generate_semantic_understanding(self, query: str) -> str:
        """
        Generate a semantic understanding of the query
        """
        try:
            prompt = f"""
            Analyze the following search query and provide a brief explanation of what the user is looking for.
            Include key concepts, potential topics, and the likely intent behind the query.

            Query: "{query}"

            Semantic understanding:
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful search query analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )

            understanding = response.choices[0].message.content.strip()
            return understanding

        except Exception as e:
            print(f"Error generating semantic understanding: {str(e)}")
            return "Unable to generate semantic understanding."

    async def summarize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of search results
        """
        if not results:
            return "No results found for your query."

        try:
            # Prepare context from top results
            context = "\n\n".join([
                f"Document {i + 1}: {result['document'][:500]}..."
                for i, result in enumerate(results[:3])
            ])

            prompt = f"""
            Based on the following search results for the query "{query}", provide a concise summary 
            that answers the query. Focus on the most relevant information.

            {context}

            Summary:
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful search results summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            print(f"Error summarizing results: {str(e)}")
            return "Unable to generate summary of results."