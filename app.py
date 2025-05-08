from flask import Flask, request, jsonify, Response
from prometheus_client import generate_latest, REGISTRY, Summary, Counter
import time

app = Flask(__name__)

# Prometheus metrics
REQUEST_LATENCY = Summary('request_latency_seconds', 'Request latency', ['endpoint'])
HTTP_REQUESTS_TOTAL = Counter('http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint', 'status'])


# In-memory book data
books = {
    "1": {"id": 1, "title": "1984", "author": "George Orwell", "price": 15.99},
    "2": {"id": 2, "title": "Brave New World", "author": "Aldous Huxley", "price": 13.49}
}

@app.route('/metrics')
def metrics():
    return Response(generate_latest(REGISTRY), mimetype='text/plain; version=0.0.4')

@app.route("/books", methods=["GET"])
def get_books():
    start = time.time()
    result = jsonify(books)
    HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/books", status="200").inc()
    REQUEST_LATENCY.labels(endpoint="/books").observe(time.time() - start)
    return result

@app.route("/books/<id>", methods=["GET"])
def get_book(id):
    start = time.time()
    book = books.get(id)
    status = "200" if book else "404"

    HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/books/<id>", status=status).inc()
    REQUEST_LATENCY.labels(endpoint="/books/<id>").observe(time.time() - start)
    return jsonify(book if book else {"error": "Book not found"}), 200 if book else 404

@app.route("/books", methods=["POST"])
def add_book():
    start = time.time()
    data = request.get_json()
    # check if all required fields are present
    if not data or not all(k in data for k in ("id", "title", "author", "price")):
        HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/books", status="400").inc()
        REQUEST_LATENCY.labels(endpoint="/books (POST)").observe(time.time() - start)
        return jsonify({"error": "Missing book fields"}), 400
    
    books[str(data["id"])] = data
    HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/books", status="201").inc()
    REQUEST_LATENCY.labels(endpoint="/books (POST)").observe(time.time() - start)
    return jsonify({"message": "Book added"}), 201

@app.route("/books/<id>", methods=["PUT"])
def update_book(id):
    start = time.time()
    if id in books:
        data = request.get_json()
        books[id] = data
        HTTP_REQUESTS_TOTAL.labels(method="PUT", endpoint="/books/<id>", status="200").inc()
        REQUEST_LATENCY.labels(endpoint="/books/<id> (PUT)").observe(time.time() - start)
        return jsonify({"message": "Book updated"}), 200
    
    HTTP_REQUESTS_TOTAL.labels(method="PUT", endpoint="/books/<id>", status="404").inc()
    REQUEST_LATENCY.labels(endpoint="/books/<id> (PUT)").observe(time.time() - start)
    return jsonify({"error": "Book not found"}), 404

@app.route("/books/<id>", methods=["DELETE"])
def delete_book(id):
    start = time.time()
    if id in books:
        del books[id]
        HTTP_REQUESTS_TOTAL.labels(method="DELETE", endpoint="/books/<id>", status="200").inc()
        REQUEST_LATENCY.labels(endpoint="/books/<id> (DELETE)").observe(time.time() - start)
        return jsonify({"message": "Book deleted"}), 200
    
    HTTP_REQUESTS_TOTAL.labels(method="DELETE", endpoint="/books/<id>", status="404").inc()
    REQUEST_LATENCY.labels(endpoint="/books/<id> (DELETE)").observe(time.time() - start)
    return jsonify({"error": "Book not found"}), 404

@app.route("/books/search", methods=["GET"])
def search_books():
    start = time.time()
    
    query = request.args.get("query")
    
    # Track the request count
    if query:
        HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/books/search", status="200").inc()
        result = {id: book for id, book in books.items() if query.lower() in book["title"].lower() or query.lower() in book["author"].lower()}
        REQUEST_LATENCY.labels(endpoint="/books/search").observe(time.time() - start)
        return jsonify(result)
    
    # Track the error count if the query parameter is missing
    HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/books/search", status="400").inc()
    REQUEST_LATENCY.labels(endpoint="/books/search").observe(time.time() - start)
    return jsonify({"error": "Query parameter is required"}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

