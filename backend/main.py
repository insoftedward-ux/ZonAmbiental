from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
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
    import requests
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        if response.status_code != 200:
            return []
        data = response.json()
        # 🔥 VALIDACIÓN IMPORTANTE
        if not isinstance(data, list):
            return []
        # 🔥 SOLO CARPETAS
        trees = [
            item["name"]
            for item in data
            if item.get("type") == "dir"
        ]
        print("TREES:", trees)
        return trees

    except Exception as e:
        print("ERROR /trees:", str(e))
        return []


# 🌲 OBTENER UN ÁRBOL
@app.get("/tree/{project}/{vertice}")
def get_tree(project: str, vertice: str):
    import requests
    raw_base = f"https://raw.githubusercontent.com/{GITHUB_USER}/{project}/main/{vertice}/"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    # 🔥 1. LEER JSON
    json_url = raw_base + "data.json"
    res = requests.get(json_url)
    if res.status_code != 200:
        return {}
    data = res.json()
    # 🔥 2. LISTAR ARCHIVOS (IMÁGENES)
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{project}/contents/{vertice}"
    files_res = requests.get(api_url, headers=headers)
    images = []
    if files_res.status_code == 200:
        files = files_res.json()

        for file in files:
            name = file["name"].lower()

            if name.endswith(".jpg") or name.endswith(".png"):
                images.append(raw_base + file["name"])

    data["images"] = images

    return data

# 🗑️ ELIMINAR (pendiente)
@app.delete("/tree/{project}/{vertice}")
def delete_tree(project: str, vertice: str):
    return {"msg": "Eliminar aún no implementado"}

# Crear Ficha
@app.get("/ficha/{project}/{vertice}", response_class=HTMLResponse)
async def ficha(project: str, vertice: str):

    data = get_tree_data(project, vertice) 
    images = data.get("images", [])

    html_images = "".join([
        f'<img src="{img}" style="width:100%;margin-bottom:10px;border-radius:10px;">'
        for img in images
    ])

    return f"""
    <html>
    <head>
        <title>Ficha Árbol {vertice}</title>
        <style>
            body {{
                font-family: Arial;
                padding: 20px;
                background: #f5f5f5;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #2e7d32; }}
        </style>
    </head>
    <body>

        <div class="card">
            <h1>{data.get("nombreComun")}</h1>
            <h3><i>{data.get("nombreCientifico")}</i></h3>

            <p><b>Altura:</b> {data.get("altura")} m</p>
            <p><b>Copa:</b> {data.get("copa")} m</p>
            <p><b>DAP:</b> {data.get("dap")} cm</p>

            <p><b>Ubicación:</b><br>
            {data.get("latitud")}, {data.get("longitud")}</p>

            <hr>

            {html_images}

        </div>

    </body>
    </html>
    """
