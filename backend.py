# backend.py
import requests
import re
import os
from concurrent.futures import ThreadPoolExecutor
import time

API= os.getenv("API")  # Set this in your environment
LLAMA_MODEL = "meta-llama/llama-3-8b-instruct"


def set_api_key(key: str):
    global API
    API= key


def llama_completion_via_openrouter(prompt: str, timeout: int = 60) -> str:
    """
    Call OpenRouter's chat completions endpoint.
    Returns the assistant content or an error string.
    """
    if not API:
        return "❌ Missing OpenRouter API Key"

    # Always define headers safely
    headers = {
        "Authorization": f"Bearer {API}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",   # change to your domain if deployed
        "X-Title": "Library Research Assistant"
    }

    payload = {
        "model": LLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    # Debug print
    print("DEBUG >> Sending request to OpenRouter")
    print("DEBUG >> Headers:", {k: (v[:10] + "..." if k == "Authorization" else v) for k, v in headers.items()})
    print("DEBUG >> Payload:", payload)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return "❌ OpenRouter returned empty choices"
        message = choices[0].get("message", {}) or {}
        content = message.get("content") or message.get("text") or ""
        return content.strip()
    except Exception as e:
        return f"❌ OpenRouter LLaMA error: {e}"


def extract_keywords(prompt: str) -> str:
    """
    Extract 2-5 academic keywords from the user's prompt using the LLM.
    Returns a comma-separated string (cleaned) or empty string on failure.
    """
    instruction = "Extract 2–5 academic search keywords from this research question. Respond ONLY with a comma-separated list:"
    raw_output = llama_completion_via_openrouter(f"{instruction}\n\n{prompt}", timeout=25)
    if not raw_output:
        return ""
    keywords_line = raw_output.splitlines()[0]
    # remove unusual characters, keep letters, numbers, comma, hyphen, spaces
    return re.sub(r"[^a-zA-Z0-9,\- ]+", "", keywords_line).strip()


def search_openalex(query: str, per_page: int = 5, timeout: int = 10) -> list:
    """
    Search OpenAlex works by passing 'query' to the 'search' parameter.
    Returns a list of works (could be empty). Raises exception on network error.
    """
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": per_page,
    }
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json().get("results", []) or []
    except Exception as e:
        # propagate a descriptive exception
        raise Exception(f"OpenAlex API error: {e}")


def convert_abstract(abstract_inverted_index: dict, word_limit: int = 50) -> str:
    """
    Convert OpenAlex's abstract_inverted_index into a readable truncated abstract.
    """
    if not abstract_inverted_index:
        return ""
    pos_word_pairs = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            pos_word_pairs.append((pos, word))
    pos_word_pairs.sort()
    words = [word for _, word in pos_word_pairs]
    truncated = " ".join(words[:word_limit])
    return truncated + "..." if len(words) > word_limit else truncated


def get_work_type(type_str: str) -> str:
    if type_str:
        return type_str.replace("https://openalex.org/", "").replace("-", " ").capitalize()
    return "Unknown"


def summarize_with_llm(user_query: str, docs: list, top_n: int = 5) -> str:
    """
    Build a compact context from top_n docs and ask the LLM to generate a structured summary.
    Returns the summary text or a failure message.
    """
    if not docs:
        return "No papers provided for summarization."

    context = ""
    for idx, doc in enumerate(docs[:top_n], 1):
        title = doc.get("display_name", "No Title")
        authors = ", ".join(
            [a.get("author", {}).get("display_name", "") for a in doc.get("authorships", [])]
        )
        abstract = convert_abstract(doc.get("abstract_inverted_index"), word_limit=40)
        year = doc.get("publication_year") or ""
        context += f"{idx}. Title: {title}\nAuthors: {authors} ({year})\nAbstract: {abstract}\n\n"

    prompt = f"""You are an expert academic assistant. Summarize the impact of the topic in a professional, structured way using the information provided in academic paper abstracts and metadata.

Instructions:
1. Start with a brief overview paragraph summarizing the answer.
2. Follow with 2–4 clearly titled sections that explain specific mechanisms or effects related to the topic.
3. For each section, provide concrete evidence from the abstracts, including short author name(s) and publication years in parentheses where possible.
4. End with a short conclusion about the significance or implication of the findings.
5. Keep your tone academic, concise, and easy to read for a research audience.

User Research Question:
"{user_query}"

Relevant Papers:
{context}

Answer:"""

    return llama_completion_via_openrouter(prompt, timeout=60)


def get_papers_and_keywords(query: str, per_page: int = 10,
                            keyword_timeout: int = 20, search_timeout: int = 10) -> tuple:
    """
    Run OpenAlex search and LLM keyword extraction in parallel to reduce latency.
    Returns (keywords_str, papers_list). Either may be empty if that step fails or times out.
    If keywords were extracted but initial search returned nothing, attempt a second search using the keywords.
    """
    keywords = ""
    papers = []

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_search = ex.submit(search_openalex, query, per_page, search_timeout)
        f_keywords = ex.submit(extract_keywords, query)

        # Collect keywords (with timeout)
        try:
            keywords = f_keywords.result(timeout=keyword_timeout)
        except Exception:
            keywords = ""

        # Collect papers (with timeout)
        try:
            papers = f_search.result(timeout=search_timeout)
        except Exception:
            papers = []

    # If we got keywords but no papers, try searching with keywords
    if keywords and not papers:
        try:
            papers = search_openalex(keywords, per_page=per_page, timeout=search_timeout)
        except Exception:
            # if still failing, keep papers as empty list
            papers = []

    return keywords, papers
