import json
import requests


def load_dossier(file_path):
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            if 'text' in data:
                items.append(data['text'])
    return items


def create_intelligence_index(items, target_name, index_id=None):
    API_BASE = "http://localhost:8000"

    create_payload = {
        "items": items,
        "target_name": target_name,
        "target_info": {"name": target_name},
        "index_id": index_id
    }

    response = requests.post(f"{API_BASE}/api/v1/indices", json=create_payload)
    response.raise_for_status()
    return response.json()


def query_documents(index_id, query, k=10):
    API_BASE = "http://localhost:8000"

    query_payload = {
        "index_id": index_id,
        "query": query,
        "k": k
    }

    response = requests.post(f"{API_BASE}/api/v1/query", json=query_payload)
    response.raise_for_status()
    return response.json()


def generate_report(index_id):
    API_BASE = "http://localhost:8000"

    report_payload = {"index_id": index_id}

    response = requests.post(f"{API_BASE}/api/v1/report", json=report_payload)
    response.raise_for_status()
    return response.json()


def main():
    dossier_path = "/Users/giladmorad/PycharmProjects/report_creator/enhanced_dossier.jsonl"
    items = load_dossier(dossier_path)
    print(f"Loaded {len(items)} intelligence items")

    result = create_intelligence_index(items, "אחמד א-שאמי", "my_intel_index")
    print(f"Index created: {result['index_id']}, Facts: {result['facts_extracted']}")

    query_result = query_documents("my_intel_index", "מה התפקיד של המטרה?", 10)
    print(f"Found {len(query_result.get('documents', []))} documents")
    if query_result.get('documents'):
        print(f"First result: {query_result['documents'][0][:200]}...")

    report_result = generate_report("my_intel_index")
    with open("intelligence_report.md", "w", encoding="utf-8") as f:
        f.write(report_result['report'])
    print(f"Report saved! Target: {report_result['target_name']}")
    print(f"Processing time: {report_result['processing_time_ms']:.0f}ms")


if __name__ == "__main__":
    main()