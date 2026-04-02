import requests
import base64
import json
from config import GITHUB_USER, GITHUB_TOKEN, BRANCH, BASE_API, BASE_RAW

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =========================
# 🔽 RAW (LECTURA)
# =========================

def build_raw_url(repo, path):
    return f"{BASE_RAW}/{GITHUB_USER}/{repo}/{BRANCH}/{path}"

def get_raw_json(repo, path):
    url = build_raw_url(repo, path)
    print("GET RAW:", url)

    r = requests.get(url)

    if r.status_code != 200:
        print("ERROR RAW:", r.status_code, r.text)
        return None

    return r.json()

def get_raw_file(repo, path):
    url = build_raw_url(repo, path)
    print("GET FILE:", url)

    r = requests.get(url)

    if r.status_code != 200:
        return None

    return r.content


# =========================
# 🔼 GITHUB API (ESCRITURA)
# =========================

def upload_file(repo, path, content_bytes, message="upload file"):
    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"

    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

    data = {
        "message": message,
        "content": content_base64,
        "branch": BRANCH
    }

    r = requests.put(url, headers=headers, json=data)

    print("UPLOAD:", r.status_code, r.text)

    return r.status_code == 201 or r.status_code == 200


def get_file_sha(repo, path):
    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"
    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()["sha"]

    return None


def update_file(repo, path, content_bytes, message="update file"):
    sha = get_file_sha(repo, path)

    if not sha:
        return upload_file(repo, path, content_bytes, message)

    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"

    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

    data = {
        "message": message,
        "content": content_base64,
        "branch": BRANCH,
        "sha": sha
    }

    r = requests.put(url, headers=headers, json=data)

    print("UPDATE:", r.status_code, r.text)

    return r.status_code == 200


# =========================
# 📂 INDEX
# =========================

def get_index(repo):
    index = get_raw_json(repo, "index.json")
    return index if index else []


def update_index(repo, vertice):
    index = get_index(repo)

    if vertice not in index:
        index.append(vertice)

    content = json.dumps(index, indent=2).encode("utf-8")

    return update_file(repo, "index.json", content, "update index")
