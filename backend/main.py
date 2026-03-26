import os
import requests
import base64
import json

from fastapi import FastAPI, UploadFile, File, Form
from typing import List

app = FastAPI()

# 🔐 VARIABLES DE ENTORNO
GITHUB_TOKEN = os.getenv("TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 🌐 ROOT
@app.get("/")
def root():
    return {"status": "Backend activo"}

# 📁 LISTAR REPOS
@app.get("/repos")
def get_repos():
    url = "https://api.github.com/user/repos"
    response = requests.get(url, headers=HEADERS)

    repos = []
    if response.status_code == 200:
        for repo in response.json():
            repos.append(repo["name"])

    return repos

# 🆕 CREAR REPO
@app.post("/create_repo")
def create_repo(data: dict):
    name = data.get("name")

    url = "https://api.github.com/user/repos"

    response = requests.post(url, headers=HEADERS, json={
        "name": name,
        "private": False
    })

    return response.json()

# 🌳 LISTAR ÁRBOLES (CARPETAS)
@app.get("/trees/{project}")
def get_trees(project: str):

    project = project.replace('"', '').strip()

    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/"

    response = requests.get(url, headers=HEADERS)

    trees = []

    if response.status_code == 200:
        for item in response.json():
            if item.get("type") == "dir":
                trees.append(item.get("name"))

    return trees

# 🌲 OBTENER FICHA DE ÁRBOL
@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):

    project = project.replace('"', '').strip()
    vertice = vertice.replace('"', '').strip()

    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{vertice}/data.json"

    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "No encontrado"}

    content = response.json().get("content", "")
    decoded = base64.b64decode(content).decode("utf-8")

    data = json.loads(decoded)

    # 🔥 LIMPIAR COMILLAS EXTRA
    clean_data = {}
    for key, value in data.items():
        clean_data[key] = str(value).replace('"', '').strip()

    return clean_data

# 📸 CREAR ÁRBOL + SUBIR IMÁGENES
@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    vertice: str = Form(...),
    nombreComun: str = Form(...),
    nombreCientifico: str = Form(...),
    altura: str = Form(...),
    copa: str = Form(...),
    dap: str = Form(...),
    images: List[UploadFile] = File(...)
):

    project = project.replace('"', '').strip()
    vertice = vertice.replace('"', '').strip()

    base_path = f"{vertice}"

    # 📄 JSON limpio
    data = {
        "vertice": vertice,
        "nombreComun": nombreComun.replace('"', ''),
        "nombreCientifico": nombreCientifico.replace('"', ''),
        "altura": altura.replace('"', ''),
        "copa": copa.replace('"', ''),
        "dap": dap.replace('"', '')
    }

    json_content = base64.b64encode(
        json.dumps(data, indent=2).encode()
    ).decode()

    json_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/data.json"

    requests.put(json_url, headers=HEADERS, json={
        "message": f"Add data {vertice}",
        "content": json_content
    })

    # 📸 SUBIR IMÁGENES
    for img in images:
        content = await img.read()
        encoded = base64.b64encode(content).decode()

        file_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/{img.filename}"

        requests.put(file_url, headers=HEADERS, json={
            "message": f"Add image {img.filename}",
            "content": encoded
        })

    return {"status": "ok"}

# 🗑️ ELIMINAR ÁRBOL COMPLETO
@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):

    project = project.replace('"', '').strip()
    vertice = vertice.replace('"', '').strip()

    base_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{vertice}"

    # 1️⃣ Obtener contenido de la carpeta
    response = requests.get(base_url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "No encontrado"}

    files = response.json()

    # 2️⃣ Eliminar cada archivo
    for file in files:
        delete_url = file["url"]

        requests.delete(delete_url, headers=HEADERS, json={
            "message": f"Delete {file['name']}",
            "sha": file["sha"]
        })

    return {"status": "deleted"}
