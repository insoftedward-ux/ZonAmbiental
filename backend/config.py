import os

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")

BASE_API = "https://api.github.com"
BASE_RAW = "https://raw.githubusercontent.com"
