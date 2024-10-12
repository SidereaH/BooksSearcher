from flask import Flask, request, jsonify
from urllib.parse import quote as url_quote
from elasticsearch import Elasticsearch, exceptions as es_exceptions
import os

app = Flask(__name__)

# Инициализация клиента Elasticsearch
es = Elasticsearch(['http://elasticsearch:9200'])

# Индекс для хранения книг
INDEX_NAME = 'books'

def create_index():
    # Check if Elasticsearch is available
    try:
        if not es.ping():
            raise ValueError("Elasticsearch connection failed")
    except es_exceptions.ConnectionError as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return

    # Create index if it doesn't exist
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "author": {"type": "text"},
                    "year": {"type": "integer"}
                }
            }
        })
        print(f"Index '{INDEX_NAME}' created.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

@app.route('/book', methods=['POST'])
def add_book():
    try:
        book = request.json
        result = es.index(index=INDEX_NAME, body=book)
        return jsonify({"message": "Book added", "id": result['_id']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/book/<id>', methods=['GET'])
def get_book(id):
    try:
        result = es.get(index=INDEX_NAME, id=id)
        return jsonify(result['_source'])
    except es_exceptions.NotFoundError:
        return jsonify({"error": "Book not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/book/<id>', methods=['DELETE'])
def delete_book(id):
    try:
        es.delete(index=INDEX_NAME, id=id)
        return jsonify({"message": "Book deleted"}), 200
    except es_exceptions.NotFoundError:
        return jsonify({"error": "Book not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/books', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "author"]
            }
        }
    }
    try:
        result = es.search(index=INDEX_NAME, body=body)
        return jsonify(result['hits']['hits'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    create_index()
    app.run(host='0.0.0.0', port=5000)
