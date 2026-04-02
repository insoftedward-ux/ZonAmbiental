from fastapi import FastAPI, UploadFile, File, Form
from typing import List, Optional
import json

from github_service import (
    create_repo,
    upload_file,
    get_file,
    update_file,
    list_repos
)

app = FastAPI()


# 🌍 ROOT
@app.get("/")
def root():
    return {"msg": "API funcionando correctamente"}


# 📁 LISTAR REPOSITORIOS
@app.get("/repos")
def get_repos():
    return list_repos()


# 🆕 CREAR REPOSITORIO + index.json
@app.post("/create_repo")
def create_new_repo(repo_name: str):

    success = create_repo(repo_name)

    if not success:
        return {"error": "No se pudo crear repo"}

    # Crear index.json automáticamente
    index_content = json.dumps([])

if get_file(project, f"{vertice}/data.json"):
    update_file(
        project,
        f"{vertice}/data.json",
        json.dumps(tree_data, indent=2).encode(),
        "update tree"
    )
else:
    upload_file(
        project,
        f"{vertice}/data.json",
        json.dumps(tree_data, indent=2).encode(),
        "create tree"
    )
    return {"msg": f"Repo {repo_name} creado"}


# 🌳 CREAR ÁRBOL
@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    data: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):

    try:
        tree_data = json.loads(data)
    except:
        return {"error": "JSON inválido"}

    vertice = tree_data.get("vertice")

    if not vertice:
        return {"error": "Falta vertice"}

    # 📷 Subir imágenes
    image_urls = []

    if files:
        for i, file in enumerate(files):
            content = await file.read()
            filename = f"{vertice}/img{i}.jpg"

            success = upload_file(project, filename, content, "upload image")

            if success:
                url = f"https://raw.githubusercontent.com/{project_owner}/{project}/main/{filename}"
                image_urls.append(url)

    # 📦 Guardar data.json
    tree_data["images"] = image_urls

    upload_file(
        project,
        f"{vertice}/data.json",
        json.dumps(tree_data, indent=2).encode(),
        "tree data"
    )

    # 📄 ACTUALIZAR index.json
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

    return {"msg": "Tree creado correctamente"}


# 🌳 LISTAR ÁRBOLES
@app.get("/trees/{project}")
def get_trees(project: str):

    index = get_file(project, "index.json")

    if not index:
        return []

    result = []

    for vertice in index:
        data = get_file(project, f"{vertice}/data.json")
        if data:
            result.append(data)

    return result


# 🌲 OBTENER UN ÁRBOL
@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):

    data = get_file(project, f"{vertice}/data.json")

    if not data:
        return {"error": "No encontrado"}

    return data


# 🗑️ ELIMINAR ÁRBOL (BÁSICO)
@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):

    # ⚠️ Esto requiere implementar delete en github_service
    return {"msg": "Eliminar aún no implementado"}
