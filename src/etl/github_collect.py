"""
github_collect.py 

Author: PeiYing
Purpose:
Download multiple GitHub repositories as knowledge sources
for RAG + Multi-Agent Code Generation.
Supports public repos via GitHub API.
"""

import os
import requests
import zipfile


def download_repo_zip(owner: str, repo: str, branch: str, target_folder: str):
    """
    Download a GitHub repo as a zip file and extract it.
    """
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    zip_path = os.path.join(target_folder, f"{repo}.zip")

    os.makedirs(target_folder, exist_ok=True)

    print(f"\n➡️ Downloading: {zip_url}")
    r = requests.get(zip_url)

    if r.status_code != 200:
        raise Exception(f"❌ Failed to download repo ({r.status_code}) - URL: {zip_url}")

    with open(zip_path, "wb") as f:
        f.write(r.content)

    print(f"✔ Saved zip → {zip_path}")

    # Extract zip file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_folder)

    print(f"✔ Extracted → {target_folder}")

    extracted_folder = os.path.join(target_folder, f"{repo}-{branch}")
    return extracted_folder


def collect_repo(owner: str, repo: str, branch: str = "main", out_dir: str = "data/raw"):
    """
    High-level wrapper: ensures folder + downloads repo.
    """
    repo_path = download_repo_zip(owner, repo, branch, out_dir)

    # Some repos use "master", some use "main"
    if not os.path.exists(repo_path):
        # Try fallback branch name
        alt_path = repo_path.replace("-main", "-master")
        if os.path.exists(alt_path):
            return alt_path
        raise Exception(f"❌ Extracted repo folder not found: {repo_path}")

    print(f"✔ Repo available at: {repo_path}")
    return repo_path


if __name__ == "__main__":
    print("🔥 Downloading 6 knowledge-source repositories...\n")

    repos = [
       # ("huggingface", "transformers", "main"),   # ML/NLP
        ("psf", "requests", "main"),               # HTTP Library
        ("pallets", "flask", "main"),              # Web Framework
        ("tiangolo", "fastapi", "master"),         # API Framework
        ("pandas-dev", "pandas", "main"),          # Data Science
    ]

    paths = []
    for owner, repo, branch in repos:
        print(f"\n📦 Downloading {repo} ...")
        try:
            path = collect_repo(owner, repo, branch)
            paths.append(path)
        except Exception as e:
            print(f"❌ Failed: {repo} — {e}")

    print("\n🎉 Done! Repositories saved to:", paths)
