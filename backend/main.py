from fastapi import FastAPI, UploadFile, File, Form
from typing import List, Optional
import json
import os

from github_service import (
    create_repo,
    upload_file,
    get_file,
    update_file,
    list_repos
)

app = FastAPI()

# 🔧 CONFIG
GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")


# 🌍 ROOT
@app.get("/")
def root():
    return {"msg": "API funcionando correctamente"}


# 📁 LISTAR REPOS
@app.get("/repos")
def get_repos():
    return list_repos()


# 🆕 CREAR REPO + index.json
@app.post("/create_repo")
def create_new_repo(repo_name: str):

    success = create_repo(repo_name)

    if not success:
        return {"error": "No se pudo crear repo"}

    # Crear index.json vacío
    index_content = json.dumps([])

    upload_file(
        repo_name,
        "index.json",
        index_content.encode(),
        "init index"
    )

    return {"msg": f"Repo {repo_name} creado"}


# 🌳 CREAR / ACTUALIZAR ÁRBOL
@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    data: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):

    # 🔐 Parse JSON
    try:
        tree_data = json.loads(data)
    except Exception as e:
        return {"error": "JSON inválido", "detail": str(e)}

    vertice = tree_data.get("vertice")

    if not vertice:
        return {"error": "Falta vertice"}

    # 📷 SUBIR IMÁGENES
    image_urls = []

    if files:
        for i, file in enumerate(files):
            content = await file.read()
            filename = f"{vertice}/img{i}.jpg"

            success = upload_file(project, filename, content, "upload image")

            if success:
                url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{project}/{BRANCH}/{filename}"
                image_urls.append(url)

    # 📦 GUARDAR DATA.JSON
    tree_data["images"] = image_urls

    path_data = f"{vertice}/data.json"

    existing = get_file(project, path_data)

    if existing:
        update_file(
            project,
            path_data,
            json.dumps(tree_data, indent=2).encode(),
            "update tree"
        )
    else:
        upload_file(
            project,
            path_data,
            json.dumps(tree_data, indent=2).encode(),
            "create tree"
        )

    # 📄 ACTUALIZAR INDEX.JSON
    index = get_file(project, "index.json")

    if index is None:
        index = []

    if vertice not in index:
        index.append(vertice)

        update_file(
            project,
            "index.json",
            json.dumps(index, indent=2).encode(),
            "update index"
        )

    return {
        "msg": "Tree guardado correctamente",
        "images": image_urls
    }


# 🌳 LISTAR ÁRBOLES
@app.get("/trees/{project}")
def get_trees(project: str):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("ERROR LISTANDO:", r.text)
        return []
    data = r.json()
    # 🔥 SOLO CARPETAS = ÁRBOLES
    trees = [item["name"] for item in data if item["type"] == "dir"]
    print("TREES:", trees)
    return trees


# 🌲 OBTENER UN ÁRBOL
@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):

    data = get_file(project, f"{vertice}/data.json")

    if not data:
        return {"error": "No encontrado"}

    return data


# 🗑️ ELIMINAR (pendiente)
@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):
    return {"msg": "Eliminar aún no implementado"}
