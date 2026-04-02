import requests
import base64
import os

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")

BASE_API = "https://api.github.com"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


# 🆕 CREAR REPO
def create_repo(repo_name):
    url = f"{BASE_API}/user/repos"

    data = {
        "name": repo_name,
        "private": False
    }

    r = requests.post(url, json=data, headers=headers)

    print("CREATE REPO:", r.status_code, r.text)

    return r.status_code == 201


# 📁 LISTAR REPOS
def list_repos():
    url = f"{BASE_API}/user/repos?per_page=100"

    r = requests.get(url, headers=headers)

    print("LIST REPOS:", r.status_code)

    if r.status_code != 200:
        return []

    return [repo["name"] for repo in r.json()]


# 📤 SUBIR ARCHIVO
def upload_file(repo, path, content, message):
    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"

    content_base64 = base64.b64encode(content).decode()

    data = {
        "message": message,
        "content": content_base64,
        "branch": BRANCH
    }

    r = requests.put(url, json=data, headers=headers)

    print("UPLOAD:", path, r.status_code)

    return r.status_code in [200, 201]


# 📥 OBTENER ARCHIVO (RAW decode)
def get_file(repo, path):
    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"

    r = requests.get(url, headers=headers)

    print("GET FILE:", path, r.status_code)

    if r.status_code != 200:
        return None

    data = r.json()

    content = base64.b64decode(data["content"]).decode()

    try:
        return json.loads(content)
    except:
        return content


# 🔄 ACTUALIZAR ARCHIVO
def update_file(repo, path, content, message):
    url = f"{BASE_API}/repos/{GITHUB_USER}/{repo}/contents/{path}"

    # Obtener SHA
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return False

    sha = r.json()["sha"]

    content_base64 = base64.b64encode(content).decode()

    data = {
        "message": message,
        "content": content_base64,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(url, json=data, headers=headers)

    print("UPDATE:", path, r.status_code)

    return r.status_code == 200
