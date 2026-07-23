from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

def project_dir(project: str):
    return DATA_DIR / project.lower()

def load_scurve(project):
    path = project_dir(project) / "scurve.xlsx"
    return pd.read_excel(path)

def load_document(project):
    path = project_dir(project) / "archive.xlsx"
    return pd.read_excel(path)

def load_manpower(project):
    path = project_dir(project) / "manpower.xlsx"
    return pd.read_excel(path)
