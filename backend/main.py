from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import requests
import base64
import json
import os

app = FastAPI()

# 🔐 VARIABLES DE ENTORNO
GITHUB_TOKEN = os.getenv("TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ============================
# 🔵 TEST
# ============================

@app.get("/")
def home():
    return {"status": "backend activo"}

# ============================
# 📁 LISTAR REPOSITORIOS
# ============================

@app.get("/repos")
def get_repos():
    url = "https://api.github.com/user/repos"

    response = requests.get(url, headers=HEADERS)

    return response.json()

# ============================
# ➕ CREAR REPOSITORIO
# ============================

@app.post("/create_repo")
def create_repo(data: dict):
    repo_name = data.get("name")

    url = "https://api.github.com/user/repos"

    payload = {
        "name": repo_name,
        "private": False,
        "auto_init": True
    }

    response = requests.post(url, headers=HEADERS, json=payload)

    return {
        "status": response.status_code,
        "data": response.json()
    }

# ============================
# 🌳 CREAR ÁRBOL (IMÁGENES + JSON)
# ============================

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

    base_path = f"{vertice}"

    # 📄 JSON DEL ÁRBOL
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

    res_json = requests.put(json_url, headers=HEADERS, json={
        "message": f"Add data {vertice}",
        "content": json_content
    })

    print("JSON STATUS:", res_json.status_code, res_json.text)

    # 📸 SUBIR IMÁGENES
    for i, img in enumerate(images):

        content = await img.read()

        encoded = base64.b64encode(content).decode()

        filename = f"img_{i+1}.jpg"  # 🔥 evita nombres repetidos

        file_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/{filename}"

        res_img = requests.put(file_url, headers=HEADERS, json={
            "message": f"Add image {filename}",
            "content": encoded
        })

        print("IMG STATUS:", res_img.status_code, res_img.text)

    return {"status": "ok"}

# ============================
# 🌲 LISTAR ÁRBOLES
# ============================

@app.get("/trees/{project}")
def get_trees(project: str):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/"

    response = requests.get(url, headers=HEADERS)

    trees = []

    if response.status_code == 200:
        for item in response.json():
            if item["type"] == "dir":
                trees.append(item["name"])

    return trees
