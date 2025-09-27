# flask_api_server.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from backend import (
    set_api_key,
    get_papers_and_keywords,
    convert_abstract,
    get_work_type,
    summarize_with_llm
)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Enable CORS for frontend requests

# Set your API key on startup if present
API = os.getenv("API")
if API:
    set_api_key(API)


# ------------------- API ROUTES -------------------

@app.route('/api/research', methods=['POST'])
def research_query():
    try:
        data = request.get_json() or {}
        query = (data.get('query') or '').strip()

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        if len(query) < 5:
            return jsonify({'error': 'Query too short. Please provide more details.'}), 400

        # Run search + keyword extraction in parallel
        keywords, papers = get_papers_and_keywords(query, per_page=10)

        if not papers:
            return jsonify({
                'query': query,
                'keywords': keywords or "",
                'papers': [],
                'summary': 'No relevant papers found for your query. Try different keywords.',
                'total_results': 0
            })

        # Process papers for frontend (defensive access)
        processed_papers = []
        for paper in papers:
            primary_location = (paper.get('primary_location') or {}) if isinstance(paper, dict) else {}
            authors_list = []
            for a in paper.get('authorships', []) or []:
                author_name = a.get('author', {}).get('display_name') if isinstance(a, dict) else None
                if author_name:
                    authors_list.append(author_name)
            processed_paper = {
                'title': paper.get('display_name', 'No Title'),
                'authors': authors_list,
                'publication_year': paper.get('publication_year'),
                'type': get_work_type(paper.get('type')),
                'abstract': convert_abstract(paper.get('abstract_inverted_index'), word_limit=100),
                'doi': paper.get('doi'),
                'url': primary_location.get('landing_page_url'),
                'pdf_url': primary_location.get('pdf_url'),
                'openalex_url': paper.get('id'),
                'citation_count': paper.get('cited_by_count', 0)
            }
            processed_papers.append(processed_paper)

        # Generate AI summary but guard with a timeout so API returns papers even if summary is slow
        summary = ""
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(summarize_with_llm, query, papers[:5])
                summary = future.result(timeout=60)  # adjust timeout as needed
        except Exception as e:
            summary = f"Summary unavailable (timed out or failed): {str(e)}"

        return jsonify({
            'query': query,
            'keywords': keywords,
            'papers': processed_papers,
            'summary': summary,
            'total_results': len(processed_papers)
        })

    except Exception as e:
        return jsonify({'error': f'Research failed: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(API)
    })


# ------------------- FRONTEND ROUTE -------------------

@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    if not API:
        print("⚠️  Warning: OPENROUTER_API_KEY not set!")
        print("Set it with: export API='your-key-here'")
    app.run(host="0.0.0.0", port=5000, debug=False)
