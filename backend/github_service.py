import requests
import base64
import json
import time
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

    return r.status_code in [200, 201]


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

    if index is None:
        print("⚠ index.json no existe, creando automáticamente...")
        create_index_file(repo)
        return []

    return index


def update_index(repo, vertice):
    index = get_index(repo)

    if vertice not in index:
        index.append(vertice)

    content = json.dumps(index, indent=2).encode("utf-8")

    return update_file(repo, "index.json", content, "update index")


def create_index_file(repo):
    content = "[]".encode("utf-8")

    for i in range(5):
        success = upload_file(repo, "index.json", content, "init index")

        if success:
            print("✅ index.json creado")
            return True

        print(f"Reintentando crear index... {i+1}")
        time.sleep(2)

    print("❌ No se pudo crear index.json")
    return False


# =========================
# 📦 CREAR REPO
# =========================

def create_repo(repo_name):
    url = f"{BASE_API}/user/repos"

    data = {
        "name": repo_name,
        "private": False
    }

    r = requests.post(url, headers=headers, json=data)

    print("CREATE REPO:", r.status_code, r.text)

    if r.status_code == 201:
        # Crear index automáticamente

    def list_repos():
    url = f"{BASE_API}/user/repos"

    r = requests.get(url, headers=headers)

    print("LIST REPOS:", r.status_code, r.text)

    if r.status_code != 200:
        return []

    repos = r.json()

    # Solo nombres
    return [repo["name"] for repo in repos]
        create_index_file(repo_name)
        return True

    return False
