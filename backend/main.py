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

    data = get_tree(project, vertice)
    images = data.get("images", [])

    # 🖼️ GALERÍA
    html_images = "".join([
        f'<img src="{img}" style="width:100%;margin-top:10px;border-radius:8px;">'
        for img in images
    ])

    # 📍 MAPA (SIN API)
    lat = data.get("latitud", 0)
    lng = data.get("longitud", 0)

    mapa = f"""
    <iframe
        src="https://maps.google.com/maps?q={lat},{lng}&z=18&output=embed"
        width="100%" height="300" style="border:0;margin-top:10px;">
    </iframe>
    """

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Ficha Técnica de Arbolado</title>

<style>
body {{
    font-family: Arial, sans-serif;
    margin: 0;
    background: #f0f0f0;
}}

.container {{
    background: white;
    max-width: 900px;
    margin: 20px auto;
    padding: 20px;
    border: 3px solid #2e7d32;
}}

/* HEADER */
.header {{
    display: flex;
    align-items: center;
    border-bottom: 3px solid #2e7d32;
    padding-bottom: 10px;
}}

.header img {{
    height: 70px;
    margin-right: 15px;
}}

.title {{
    font-size: 22px;
    font-weight: bold;
    color: #2e7d32;
}}

/* SECCIONES */
.section {{
    margin-top: 20px;
}}

.label {{
    font-weight: bold;
}}

.data p {{
    margin: 5px 0;
}}

.gallery img {{
    width: 100%;
    margin-top: 10px;
    border-radius: 6px;
}}

.btn {{
    margin-top: 25px;
    padding: 12px;
    background: #2e7d32;
    color: white;
    text-align: center;
    cursor: pointer;
    font-weight: bold;
}}

/* PRINT */
@media print {{
    .btn {{ display: none; }}
    body {{ background: white; }}
    .container {{ border: none; margin: 0; }}
}}
</style>

</head>
<body>

<div class="container">

    <!-- HEADER -->
    <div class="header">
        <img src="https://github.com/insoftedward-ux/ZonAmbiental/blob/main/backend/logo.jpg">
        <div class="title">FICHA TÉCNICA DE ARBOLADO</div>
    </div>

    <!-- DATOS -->
    <div class="section data">
        <p><span class="label">Proyecto:</span> {project}</p>
        <p><span class="label">Vértice:</span> {vertice}</p>
        <p><span class="label">Nombre común:</span> {data.get("nombreComun","")}</p>
        <p><span class="label">Nombre científico:</span> <i>{data.get("nombreCientifico","")}</i></p>
        <p><span class="label">Altura:</span> {data.get("altura","")} m</p>
        <p><span class="label">DAP:</span> {data.get("dap","")} cm</p>
        <p><span class="label">Copa:</span> {data.get("copa","")} m</p>
    </div>

    <!-- MAPA -->
    <div class="section">
        <div class="label">Ubicación:</div>
        {mapa}
    </div>

    <!-- GALERÍA -->
    <div class="section">
        <div class="label">Galería fotográfica:</div>
        {html_images}
    </div>

    <!-- PDF -->
    <div class="btn" onclick="window.print()">
        Descargar / Imprimir PDF
    </div>

</div>

</body>
</html>
"""
