import os
import json
import base64
import requests
from fastapi import FastAPI, UploadFile, File, Form
from typing import List

app = FastAPI()

# 🔐 VARIABLES DE ENTORNO (Render)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 🔥 1. LISTAR REPOSITORIOS
@app.get("/repos")
def get_repos():
    url = f"https://api.github.com/user/repos"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        return []

    repos = [repo["name"] for repo in resp.json()]
    return repos


# 🔥 2. CREAR REPOSITORIO
@app.post("/create_repo")
def create_repo(body: dict):
    repo_name = body.get("name")

    url = "https://api.github.com/user/repos"

    resp = requests.post(url, headers=headers, json={
        "name": repo_name,
        "private": False
    })

    return {"status": resp.status_code, "response": resp.json()}


# 🔥 3. CREAR / ACTUALIZAR ÁRBOL
@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    vertice: str = Form(...),
    nombreComun: str = Form(...),
    nombreCientifico: str = Form(...),
    altura: str = Form(...),
    copa: str = Form(...),
    dap: str = Form(...),
    images: List[UploadFile] = File([])
):
    base_path = f"{vertice}"

    # 📄 JSON del árbol
    data = {
        "vertice": vertice,
        "nombreComun": nombreComun,
        "nombreCientifico": nombreCientifico,
        "altura": altura,
        "copa": copa,
        "dap": dap
    }

    json_content = base64.b64encode(
        json.dumps(data, indent=2).encode()
    ).decode()

    json_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/data.json"

    # 🔍 verificar si existe (para update)
    sha = None
    check = requests.get(json_url, headers=headers)
    if check.status_code == 200:
        sha = check.json().get("sha")

    requests.put(json_url, headers=headers, json={
        "message": f"Add/Update data {vertice}",
        "content": json_content,
        "sha": sha
    })

    # 📸 SUBIR IMÁGENES
    for img in images:
        content = await img.read()
        encoded = base64.b64encode(content).decode()

        file_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/{img.filename}"

        sha_img = None
        check_img = requests.get(file_url, headers=headers)
        if check_img.status_code == 200:
            sha_img = check_img.json().get("sha")

        requests.put(file_url, headers=headers, json={
            "message": f"Add image {img.filename}",
            "content": encoded,
            "sha": sha_img
        })

    return {"status": "ok"}


# 🔥 4. LISTAR ÁRBOLES
@app.get("/trees/{project}")
def get_trees(project: str):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        return []

    trees = [item["name"] for item in resp.json() if item["type"] == "dir"]
    return trees


# 🔥 5. OBTENER DETALLE DE ÁRBOL + IMÁGENES
@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):
    base_path = f"{vertice}"

    # 📄 JSON
    json_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/data.json"
    resp = requests.get(json_url, headers=headers)

    if resp.status_code != 200:
        return {"error": "No encontrado"}

    content = resp.json()["content"]
    decoded = base64.b64decode(content).decode()
    data = json.loads(decoded)

    # 📸 LISTAR IMÁGENES
    files_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}"
    files_resp = requests.get(files_url, headers=headers)

    images = []

    if files_resp.status_code == 200:
        for file in files_resp.json():
            if file["name"].lower().endswith((".jpg", ".jpeg", ".png")):
                images.append(file["download_url"])

    return {
        **data,
        "images": images
    }


# 🔥 6. ELIMINAR ÁRBOL
@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):
    base_path = f"{vertice}"

    files_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}"
    resp = requests.get(files_url, headers=headers)

    if resp.status_code != 200:
        return {"error": "No encontrado"}

    for file in resp.json():
        delete_url = file["url"]
        sha = file["sha"]

        requests.delete(delete_url, headers=headers, json={
            "message": f"Delete {file['name']}",
            "sha": sha
        })

    return {"status": "deleted"}
