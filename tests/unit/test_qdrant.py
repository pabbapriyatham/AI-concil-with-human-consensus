import httpx
from app.retrieval.vectors import QdrantVectors


def test_qdrant_rest_contract():
    requests = []
    def handler(request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(404)
        if request.url.path.endswith("/query"):
            return httpx.Response(200, json={"result": {"points": [{"id": "id", "score": .9, "payload": {}}]}})
        return httpx.Response(200, json={"result": True})
    client = httpx.Client(base_url="http://fixture/", transport=httpx.MockTransport(handler))
    vectors = QdrantVectors("http://fixture", 3, client=client)
    vectors.upsert("evidence", [{"id": "id", "vector": [1, 0, 0], "payload": {}}])
    assert vectors.search("evidence", [1, 0, 0])[0]["score"] == .9
    assert len(requests) == 4
