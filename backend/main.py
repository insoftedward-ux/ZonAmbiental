from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import requests
import base64
import os

app = FastAPI()
GITHUB_TOKEN = os.getenv("TOKEN")
GITHUB_USER = os.getenv("USER")
print("TOKEN:", TOKEN)

# -------------------------------
# 📦 CREAR REPOSITORIO
# -------------------------------
@app.post("/project")
def create_project(data: dict):
    name = data.get("name")
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    payload = {
        "name": name,
        "auto_init": True
    }
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code != 201:
        return {"error": r.json()}
    return {"repo": name}

# -------------------------------
# ☁️ SUBIR ARCHIVO A GITHUB
# -------------------------------
def subir_archivo(repo, path, content):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    data = {
        "message": f"add {path}",
        "content": base64.b64encode(content.encode()).decode()
    }
    requests.put(url, json=data, headers=headers)

# -------------------------------
# ☁️ SUBIR IMAGEN
# -------------------------------
def subir_imagen(repo, path, content):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    data = {
        "message": f"add {path}",
        "content": base64.b64encode(content).decode()
    }
    requests.put(url, json=data, headers=headers)

# -------------------------------
# 🌐 GENERAR HTML PROFESIONAL
# -------------------------------
def generar_html(data, image_urls):
    images_html = ""

    for url in image_urls:
        images_html += f"""
        <div class="img-card">
            <img src="{url}" />
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Ficha Árbol {data['vertice']}</title>
        <style>
            body {{
                font-family: Arial;
                background: #f4f4f4;
                padding: 20px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                max-width: 800px;
                margin: auto;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2e7d32;
            }}
            .info {{
                margin-bottom: 20px;
            }}
            .info p {{
                margin: 5px 0;
                font-size: 16px;
            }}
            .gallery {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
            }}
            .img-card img {{
                width: 100%;
                border-radius: 8px;
                cursor: pointer;
                transition: 0.3s;
            }}
            .img-card img:hover {{
                transform: scale(1.05);
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🌳 {data['nombreComun']}</h1>
            <div class="info">
                <p><b>Nombre científico:</b> {data['nombreCientifico']}</p>
                <p><b>Vértice:</b> {data['vertice']}</p>
                <p><b>Altura:</b> {data['altura']} m</p>
                <p><b>Copa:</b> {data['copa']} m</p>
                <p><b>DAP:</b> {data['dap']} cm</p>
            </div>
            <h2>📸 Galería</h2>
            <div class="gallery">
                {images_html}
            </div>
        </div>
    </body>
    </html>
    """
    return html

# -------------------------------
# 🌳 CREAR ÁRBOL (MULTI IMAGEN)
# -------------------------------
@app.post("/tree")
async def create_tree(
    project: str = Form(...),
    vertice: str = Form(...),
    nombreComun: str = Form(...),
    nombreCientifico: str = Form(...),
    altura: float = Form(...),
    copa: float = Form(...),
    dap: float = Form(...),
    images: List[UploadFile] = File(...)
):
    repo = project
    image_urls = []

    # 📸 Subir múltiples imágenes
    for i, img in enumerate(images):
        content = await img.read()
        path = f"images/{vertice}_{i}.jpg"
        subir_imagen(repo, path, content)
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{repo}/main/{path}"
        image_urls.append(url)

    # 🌐 Generar HTML
    html = generar_html({
        "vertice": vertice,
        "nombreComun": nombreComun,
        "nombreCientifico": nombreCientifico,
        "altura": altura,
        "copa": copa,
        "dap": dap
    }, image_urls)

    filename = f"{vertice}.html"
    subir_archivo(repo, filename, html)
    url = f"https://{GITHUB_USER}.github.io/{repo}/{filename}"
    return {"url": url}
