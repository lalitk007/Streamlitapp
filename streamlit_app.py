# streamlit_app.py
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit UI
st.title("AI-Augmented Semantic Search Engine")
st.subheader("Powered by Vector Search & Multi-Source Integration")

# Sidebar for settings
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Enter your Groq AI API Key:", value=os.getenv("GROQ_API_KEY", ""), type="password")
os.environ["GROQ_API_KEY"] = api_key  # Set API key for langchain

# Search preferences
st.sidebar.subheader("Search Preferences")
search_mode = st.sidebar.radio(
    "Search Mode:",
    options=["Combined Search", "Vector Search Only", "Web Search Only"]
)

# Vector search settings
if search_mode in ["Combined Search", "Vector Search Only"]:
    st.sidebar.subheader("Vector Search Settings")
    vector_search_url = st.sidebar.text_input(
        "Vector Search API URL:",
        value=f"{API_BASE_URL}/api/search"

    )
    top_k_vector = st.sidebar.slider("Number of vector results:", min_value=1, max_value=20, value=5)

# Web crawler settings
if st.sidebar.checkbox("Show Crawler Settings"):
    st.sidebar.subheader("Web Crawler")
    crawl_url = st.sidebar.text_input("Website URL to crawl:")
    max_pages = st.sidebar.slider("Max Pages:", min_value=1, max_value=50, value=10)
    max_depth = st.sidebar.slider("Max Depth:", min_value=1, max_value=5, value=2)

    if st.sidebar.button("Crawl & Index Website"):
        if crawl_url:
            try:
                with st.sidebar:
                    with st.spinner("Crawling website..."):
                        response = httpx.post(
                            f"{API_BASE_URL}/api/crawl",
                            json={"url": crawl_url, "max_pages": max_pages, "max_depth": max_depth},
                            timeout=300.0  # Longer timeout for crawling
                        )
                        if response.status_code == 200:
                            st.sidebar.success(
                                f"Successfully crawled and indexed {len(response.json()['pages'])} pages!")
                        else:
                            st.sidebar.error(f"Error: {response.json()['detail']}")
            except Exception as e:
                st.sidebar.error(f"Error: {str(e)}")
        else:
            st.sidebar.warning("Please enter a URL to crawl")

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
         "content": "Hello! How can I help you?"}
    ]

# Display previous chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Validate API Key before using Groq
if api_key:
    try:
        llm = ChatGroq(groq_api_key=api_key, model_name="llama3-8b-8192")
    except Exception as e:
        st.error(f"Invalid Groq API Key: {e}")
        api_key = None

# Initialize search tools
api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv)

api_wrapper_wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wiki)

# DuckDuckGo search tool
search = DuckDuckGoSearchRun(name="Search")


# Custom tool for vector search
class VectorSearchTool:
    def __init__(self, api_url, top_k=5):
        self.api_url = api_url
        self.top_k = top_k

    def run(self, query):
        try:
            response = httpx.post(
                self.api_url,
                json={"query": query, "top_k": self.top_k},
                timeout=10.0
            )

            if response.status_code == 200:
                results = response.json()
                if results.get("results", []):
                    output = "### Vector Search Results:\n\n"
                    for i, result in enumerate(results["results"], 1):
                        output += f"**Result {i}**: {result['title']}\n"
                        output += f"**Source**: {result['url']}\n"
                        output += f"**Snippet**: {result['snippet']}\n\n"
                    return output
                else:
                    return "No vector search results found."
            else:
                return f"Error accessing vector search: {response.text}"
        except Exception as e:
            return f"Vector search error: {str(e)}"


# User input handling
if prompt := st.chat_input(placeholder="Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        with st.chat_message("assistant"):
            # Different modes of search
            if search_mode == "Vector Search Only":
                # Only use vector search
                with st.spinner("Searching indexed documents..."):
                    vector_search = VectorSearchTool(vector_search_url, top_k_vector)
                    vector_results = vector_search.run(prompt)

                    if "No vector search results found" in vector_results:
                        if api_key:
                            response = llm.invoke(prompt)
                            st.write(response.content)
                            st.session_state.messages.append({"role": "assistant", "content": response.content})
                        else:
                            st.write("No results found and no API key provided for fallback.")
                            st.session_state.messages.append(
                                {"role": "assistant", "content": "No results found in indexed documents."})
                    else:
                        st.write(vector_results)
                        st.session_state.messages.append({"role": "assistant", "content": vector_results})

            elif search_mode == "Web Search Only":
                # Use LangChain agent with web tools
                if api_key:
                    tools = [search, arxiv, wiki]
                    agent = initialize_agent(
                        tools, llm,
                        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        handle_parsing_errors=True,
                        verbose=True
                    )

                    st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
                    response = agent.run(prompt, callbacks=[st_cb])
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("Please provide a Groq API key for web search.")

            else:  # Combined Search
                if api_key:
                    # First try vector search
                    vector_search = VectorSearchTool(vector_search_url, top_k_vector)
                    vector_results = vector_search.run(prompt)

                    # Set up tools including our vector search
                    tools = [search, arxiv, wiki]
                    agent = initialize_agent(
                        tools, llm,
                        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        handle_parsing_errors=True,
                        verbose=True
                    )

                    # Combined approach
                    st.write("Searching multiple sources...")
                    st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)

                    # First show vector results if available
                    if "No vector search results found" not in vector_results:
                        st.write(vector_results)

                    # Then get agent results
                    agent_response = agent.run(
                        f"The user asked: {prompt}\n\nPlease provide a comprehensive answer. If you need more information, use the available search tools.",
                        callbacks=[st_cb]
                    )

                    st.write("\n\n### Final Summary:\n")
                    st.write(agent_response)

                    # Combine both for history
                    combined_response = ""
                    if "No vector search results found" not in vector_results:
                        combined_response += vector_results + "\n\n"
                    combined_response += "### Web Search Results:\n\n" + agent_response

                    st.session_state.messages.append({"role": "assistant", "content": combined_response})
                else:
                    # Fallback to vector search only if no API key
                    vector_search = VectorSearchTool(vector_search_url, top_k_vector)
                    vector_results = vector_search.run(prompt)
                    st.write(vector_results)
                    st.session_state.messages.append({"role": "assistant", "content": vector_results})

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    if not api_key and search_mode in ["Web Search Only", "Combined Search"]:
        st.warning("Please enter your Groq API key in the sidebar for web search capabilities.")

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys

    port = int(os.getenv("PORT", 8501))
    sys.argv = ["streamlit", "run", __file__, "--server.port", str(port), "--server.address", "0.0.0.0"]
    sys.exit(stcli.main())
