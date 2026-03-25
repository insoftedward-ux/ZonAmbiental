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
    repos = []
    if response.status_code == 200:
        for repo in response.json():
            repos.append(repo["name"])
    return repos

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

    print("==== NUEVO ÁRBOL ====")
    print("USER:", GITHUB_USER)
    print("PROJECT:", project)
    print("VERTICE:", vertice)

    project = project.replace('"', '').strip()
    vertice = vertice.replace('"', '').strip()
    base_path = vertice

    # 🔥 1. CREAR JSON (ESTO CREA LA CARPETA)
    data = {
        "vertice": vertice,
        "nombreComun": nombreComun,
        "nombreCientifico": nombreCientifico,
        "altura": altura,
        "copa": copa,
        "dap": dap
    }

    json_bytes = json.dumps(data, indent=2).encode("utf-8")
    json_base64 = base64.b64encode(json_bytes).decode("utf-8")

    json_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/data.json"

    res_json = requests.put(json_url, headers=HEADERS, json={
        "message": f"create tree {vertice}",
        "content": json_base64
    })

    print("JSON STATUS:", res_json.status_code)
    print("JSON RESP:", res_json.text)

    if res_json.status_code not in [200, 201]:
        return {
            "error": "Error creando JSON",
            "detail": res_json.text
        }

    # 🔥 2. SUBIR IMÁGENES
    for i, img in enumerate(images):
        try:
            content = await img.read()

            if not content:
                print("Imagen vacía:", img.filename)
                continue

            filename = f"img_{i+1}.jpg"

            file_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{base_path}/{filename}"

            encoded = base64.b64encode(content).decode("utf-8")

            res_img = requests.put(file_url, headers=HEADERS, json={
                "message": f"upload {filename}",
                "content": encoded
            })

            print(f"IMG {filename}:", res_img.status_code)
            print(res_img.text)

        except Exception as e:
            print("ERROR IMAGEN:", str(e))

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
