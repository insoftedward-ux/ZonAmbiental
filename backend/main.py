from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import json

from github_service import (
    get_raw_json,
    upload_file,
    update_index,
    build_raw_url,
    get_index,
    create_repo
)

app = FastAPI()

# =========================
# 📦 CREAR REPO
# =========================

@app.post("/create_repo")
def create_repository(repo_name: str):
    success = create_repo(repo_name)

    if not success:
        return {"error": "No se pudo crear repo"}

    return {
        "status": "ok",
        "repo": repo_name
    }


# =========================
# 🌳 GET TREE
# =========================

@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):
    data = get_raw_json(project, f"{vertice}/data.json")

    if not data:
        return {"error": "No encontrado"}

    return data


# =========================
# 🌳 GET TREES
# =========================

@app.get("/trees/{project}")
def get_trees(project: str):
    index = get_index(project)

    trees = []

    for vertice in index:
        data = get_raw_json(project, f"{vertice}/data.json")
        if data:
            trees.append(data)

    return trees


# =========================
# 🌳 CREATE TREE + IMÁGENES
# =========================

@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    data: str = Form(...),
    files: List[UploadFile] = File(...)
):
    tree = json.loads(data)
    vertice = tree["vertice"]

    image_urls = []

    for i, file in enumerate(files):
        content = await file.read()
        filename = f"{vertice}/img{i}.jpg"

        success = upload_file(project, filename, content, "upload image")

        if success:
            url = build_raw_url(project, filename)
            image_urls.append(url)

    tree["images"] = image_urls

    json_bytes = json.dumps(tree, indent=2).encode("utf-8")

    upload_file(project, f"{vertice}/data.json", json_bytes, "create tree")

    update_index(project, vertice)

    return {
        "status": "ok",
        "images": image_urls
    }


# =========================
# 🧪 TEST
# =========================

@app.get("/")
def root():
    return {"msg": "API funcionando"}
