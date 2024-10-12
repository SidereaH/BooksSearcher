from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)

# Инициализация клиента Elasticsearch с указанием пользователя и пароля
es = Elasticsearch(
    ['http://elasticsearch:9200'],
    http_auth=('elastic', 'changeme')
)

# Индекс для хранения данных
INDEX_NAME = 'books'

# Создание индекса при запуске
@app.before_first_request
def create_index():
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

# Добавить книгу
@app.route('/book', methods=['POST'])
def add_book():
    book = request.json
    result = es.index(index=INDEX_NAME, body=book)
    return jsonify({"message": "Book added", "id": result['_id']}), 201

# Получить книгу по ID
@app.route('/book/<id>', methods=['GET'])
def get_book(id):
    try:
        result = es.get(index=INDEX_NAME, id=id)
        return jsonify(result['_source'])
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# Удалить книгу по ID
@app.route('/book/<id>', methods=['DELETE'])
def delete_book(id):
    try:
        es.delete(index=INDEX_NAME, id=id)
        return jsonify({"message": "Book deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# Поиск книг по запросу
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
    result = es.search(index=INDEX_NAME, body=body)
    return jsonify(result['hits']['hits'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
