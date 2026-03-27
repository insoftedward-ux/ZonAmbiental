import os
import base64
import json
import requests

from fastapi import FastAPI, UploadFile, File, Form
from typing import List

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


# 🔥 LIMPIEZA GENERAL
def clean(text):
    return str(text).replace('"', '').strip()


# =========================================
# 📁 REPOS
# =========================================

@app.get("/repos")
def get_repos():
    url = f"https://api.github.com/user/repos"
    r = requests.get(url, headers=HEADERS)

    repos = [repo["name"] for repo in r.json()]
    return repos


@app.post("/create_repo")
def create_repo(data: dict):
    name = data.get("name")

    url = "https://api.github.com/user/repos"

    r = requests.post(url, headers=HEADERS, json={
        "name": name,
        "private": False
    })

    return r.json()


# =========================================
# 🌳 CREAR / ACTUALIZAR ÁRBOL
# =========================================

@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    vertice: str = Form(...),
    nombreComun: str = Form(...),
    nombreCientifico: str = Form(...),
    altura: str = Form(...),
    copa: str = Form(...),
    dap: str = Form(...),
    latitud: str = Form("0"),
    longitud: str = Form("0"),
    images: List[UploadFile] = File(...)
):

    project = clean(project)
    vertice = clean(vertice)

    base_path = f"{vertice}"

    # 📄 JSON DEL ÁRBOL
    data = {
        "vertice": clean(vertice),
        "nombreComun": clean(nombreComun),
        "nombreCientifico": clean(nombreCientifico),
        "altura": clean(altura),
        "copa": clean(copa),
        "dap": clean(dap),
        "latitud": clean(latitud),
        "longitud": clean(longitud)
    }

    json_content = base64.b64encode(
        json.dumps(data, indent=2).encode()
    ).decode()

    json_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/data.json"

    # 🔥 verificar si ya existe (modo update)
    r = requests.get(json_url, headers=HEADERS)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    requests.put(json_url, headers=HEADERS, json={
        "message": f"Save tree {vertice}",
        "content": json_content,
        "sha": sha
    })

    # 📸 IMÁGENES
    for img in images:
        content = await img.read()
        encoded = base64.b64encode(content).decode()

        file_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/{img.filename}"

        r = requests.get(file_url, headers=HEADERS)
        sha = None
        if r.status_code == 200:
            sha = r.json()["sha"]

        requests.put(file_url, headers=HEADERS, json={
            "message": f"Add image {img.filename}",
            "content": encoded,
            "sha": sha
        })

    return {"status": "ok"}


# =========================================
# 🌳 LISTAR ÁRBOLES
# =========================================

@app.get("/trees/{project}")
def get_trees(project: str):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents"

    r = requests.get(url, headers=HEADERS)

    trees = []

    for item in r.json():
        if item["type"] == "dir":
            trees.append(item["name"])

    return trees


# =========================================
# 🌳 DETALLE ÁRBOL
# =========================================

@app.get("/tree/{project}/{vertice}")
def get_tree(project, vertice):

    url = f"https://api.github.com/repos/TU_USUARIO/{project}/contents/{vertice}/data.json"

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "No encontrado"}

    file = response.json()

    # 🔥 VALIDACIÓN CLAVE
    if "content" not in file:
        return {"error": "Archivo sin contenido", "raw": file}

    content = base64.b64decode(file["content"]).decode()

    return json.loads(content)


# =========================================
# ❌ ELIMINAR ÁRBOL
# =========================================

@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):

    base_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{vertice}"

    r = requests.get(base_url, headers=HEADERS)

    for file in r.json():

        requests.delete(file["url"], headers=HEADERS, json={
            "message": f"Delete {file['name']}",
            "sha": file["sha"]
        })

    return {"status": "deleted"}


# =========================================
# 🤖 IA DETECTAR ESPECIE
# =========================================

@app.post("/detect")
async def detect_tree(image: UploadFile = File(...)):

    filename = image.filename.lower()

    if "encino" in filename:
        result = "Encino"
    elif "pino" in filename:
        result = "Pino"
    else:
        result = "Árbol desconocido"

    return {"result": result}
