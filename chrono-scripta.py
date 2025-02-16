#!/usr/bin/python3

import os
import json
import hashlib
import shutil
import time
import zipfile
import subprocess
import ollama
import PyPDF2
import requests
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

DROPIT_DIR = "dropit"
STORAGE_DIR = "storage"
DB_FILE = "database.json"
AI_MODEL = "SpeakLeash/bielik-11b-v2.3-instruct-imatrix:Q8_0"
TABLE_FMT = "rounded_outline"
CONFIG = {
    "dropit": "./dropit",
    "storage": "./storage",
    "database": "./database.json",
    "allowed_extensions": {".pdf", ".doc", ".odt"}
}


def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Błąd: {e}")
    return wrapper


def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_database_2():
    if os.path.exists(CONFIG["database"]):
        with open(CONFIG["database"], "r", encoding="utf-8") as db_file:
            return json.load(db_file)
    return {}


def save_database_2(db):
    with open(CONFIG["database"], "w", encoding="utf-8") as db_file:
        json.dump(db, db_file, indent=4)


def search_and_copy_files(search_path):
    db = load_database()
    for root, _, files in os.walk(search_path):
        if CONFIG["dropit"] in root or CONFIG["storage"] in root:
            continue
        
        for file in files:
            if os.path.splitext(file)[1].lower() in CONFIG["allowed_extensions"]:
                src_path = os.path.join(root, file)
                dest_path = os.path.join(CONFIG["storage"], file)
                if file not in db:
                    shutil.copy2(src_path, dest_path)
                    db[file] = {"original_path": src_path, "stored_path": dest_path}
    
    save_database(db)


def save_database(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)


def compute_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def open_doc(file_path):
    if os.name == "nt":
        print("Dodać otwieranie plików dla Windows!")
    else:
        subprocess.run(["xdg-open", str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def con_cls():
    if os.name == "nt":
        os.system('cls')
    else:
        os.system('clear')


def get_file_format(file_path):
    return file_path.suffix.lstrip(".").lower()


def move_file_to_storage(file_path, doc_date, md5):
    year, month, day = doc_date.split("-")
    ext = file_path.suffix
    target_dir = Path(STORAGE_DIR) / year / month / day
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{md5}{ext}"
    shutil.move(file_path, target_path)
    return target_path


def process_new_files():
    db = load_database()
    files = list(Path(DROPIT_DIR).glob("*"))
    for file_path in files:
        if not file_path.is_file():
            continue
        md5 = compute_md5(file_path)
        if any(entry["md5"] == md5 for entry in db):
            print(f"Duplikat: {file_path.name}, pominięto.")
            file_path.unlink()
            continue
        open_doc(str(file_path))
        doc_desc = input("Opis dokumentu: ")
        doc_date = input("Data dokumentu (YYYY-MM-DD): ")
        doc_author = input("Autor dokumentu: ")
        doc_recipient = input("Adresat dokumentu: ")
        doc_refnum = input("Sygnatura akt: ")
        stored_path = move_file_to_storage(file_path, doc_date, md5)
        db.append({
            "index": len(db) + 1,
            "description": doc_desc,
            "date": doc_date,
            "author": doc_author,
            "recipient": doc_recipient,
            "refnum": doc_refnum,
            "md5": md5,
            "format": get_file_format(file_path),
            "path": str(stored_path),
        })
    save_database(db)


def watch_dropit():
    print("Obserwowanie folderu dropit... (przerwij Ctrl+C)")
    try:
        while True:
            process_new_files()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Zatrzymano obserwowanie.")


def show_statistics():
    db = load_database()
    print(f"Liczba plików: {len(db)}")
    total_size = sum(Path(entry["path"]).stat().st_size for entry in db)
    print(f"Łączna objętość: {total_size / 1024 / 1024:.2f} MB")
    biggest_files = sorted(db, key=lambda x: Path(x["path"]).stat().st_size, reverse=True)[:5]
    print("Największe pliki:")
    for entry in biggest_files:
        print(f"{entry['path']} - {Path(entry['path']).stat().st_size / 1024:.2f} KB")


def create_backup():
    with zipfile.ZipFile("backup.zip", "w") as z:
        for folder_name, subfolders, filenames in os.walk(STORAGE_DIR):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                z.write(file_path, os.path.relpath(file_path, STORAGE_DIR))
        z.write(DB_FILE)
    print("Backup zapisany jako backup.zip")


@handle_errors
def open_file(index=None):
    db = load_database()
    if index is None:
        file_index = int(input("Podaj numer pliku do otwarcia: "))
    else:
        file_index = index
    for entry in db:
        if entry["index"] == file_index:
            open_doc(entry["path"])
    return file_index


@handle_errors
def list_files():
    db = load_database()
    db.sort(key=lambda x: x["date"], reverse=False)  # Sortowanie po dacie
    for entry in db:
        print(f"{entry['index']}. {entry['date']} - {entry['description']} {entry['refnum']}")
    file_index = int(input("Podaj numer pliku do otwarcia: "))
    for entry in db:
        if entry["index"] == file_index:
            open_doc(entry["path"])
    return file_index


@handle_errors
def list_files_tab():
    db = load_database()
    db.sort(key=lambda x: x["date"], reverse=False)  # Sortowanie po dacie
    headers = ["ID", "Opis", "Data", "Autor", "Syg. akt", "Format"]
    table = [[entry["index"], entry["description"], entry["date"], entry["author"], entry["refnum"], entry["format"]] for entry in db]
    print(tabulate(table, headers=headers, tablefmt=TABLE_FMT))
    return db


@handle_errors
def search_files():
    db = load_database()
    query = input("Wprowadź wyszukiwane hasło: ").lower()
    results = [entry for entry in db if any(query in str(v).lower() for v in entry.values())]
    headers = ["ID", "Opis", "Data", "Autor", "Syg. akt", "Format"]
    table = [[entry["index"], entry["description"], entry["date"], entry["author"], entry["refnum"], entry["format"]] for entry in results]
    print(tabulate(table, headers=headers, tablefmt=TABLE_FMT))
    file_index = int(input("Podaj numer pliku do otwarcia: "))
    for entry in results:
        if entry["index"] == file_index:
            open_doc(entry["path"])


def edit_metadata():
    choice = list_files() - 1
    db = load_database()
    entry = db[choice]
    print("Edytuj metadane (pozostaw puste, aby nie zmieniać):")
    entry["description"] = input(f"Opis ({entry['description']}): ") or entry["description"]
    entry["date"] = input(f"Data ({entry['date']}): ") or entry["date"]
    entry["author"] = input(f"Autor ({entry['author']}): ") or entry["author"]
    entry["recipient"] = input(f"Adresat ({entry['recipient']}): ") or entry["recipient"]
    entry["refnum"] = input(f"Sygnatura akt ({entry['refnum']}): ") or entry["refnum"]
    save_database(db)
    print("Metadane zaktualizowane.")


@handle_errors
def list_ollama_models():
    global AI_MODEL
    url = "http://localhost:11434/api/tags"
    response = requests.get(url)
    
    if response.status_code == 200:
        models = response.json().get("models", [])
#        print(json.dumps(models, indent=4))

        table_data = []
        for idx, model in enumerate(models, start=1):
            table_data.append([
                                idx, 
                                model['name'],
                                f"{(model['size']/1073741824):.1f} GB",
                                model['details']['family'],
                                model['details']['parameter_size'],
                                model['details']['quantization_level']
                              ])

        headers = ["#", "Model", "Size", "Family", "Parameter size", "Quantization level"]
        colalign = ("right", "left", "right", "center", "right", "center")
        print(tabulate(table_data, headers=headers, tablefmt=TABLE_FMT, colalign=colalign))

        choice = int(input("Wybierz model: "))
        model_name = next((row[1] for row in table_data if row[0] == choice), None)
#        print("Wybrałeś:", model_name)
        AI_MODEL = model_name
        
    else:
        print("Błąd podczas pobierania listy modeli.")


def extract_text_from_pdf(pdf_path):
    """Odczytuje tekst z pierwszych kilku stron pliku PDF."""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages[:3] if page.extract_text())
    return text


def generate_title(text):
    """Wysyła tekst do modelu Ollama i prosi o wygenerowanie tytułu."""
    prompt = f"Na podstawie poniższego tekstu wygeneruj zwięzły, trafny tytuł. Użyj języka polskiego. Tytuł maksymalnie może mieć ok. 200 znaków i nie więcej niż 300. Trzymaj się ściśle długości jaką zadałem:\n\n{text}"
    response = ollama.chat(model=AI_MODEL, messages=[{"role": "user", "content": prompt}])
    return response['message']['content']


def gen_title():
    choice = list_files() - 1
    db = load_database()
    entry = db[choice]
    print("Opis wygenerowany przez AI:")
    txt = generate_title(extract_text_from_pdf(entry['path']))
    print(txt)
    #entry["description"] = generate_title(entry['description'])
    #save_database(db)
    print("Metadane zaktualizowane.")


def main_menu():
    con_cls()
    while True:
        print("""
        1. Przeskanuj folder "dropit"
        2. Obserwuj folder "dropit" w sposób ciągły
        3. Pokaż statystyki
        4. Spakuj cały folder "storage" wraz z bazą danych do ZIP
        5. Pokaż listę plików w "storage"
        6. Szukaj pliku w "storage"
        7. Edycja metadanych pliku
        8. Funkcji AI
        0. Koniec
        """)
        choice = input("Wybierz opcję: ")
        con_cls()
        if choice == "1":
            process_new_files()
        elif choice == "2":
            watch_dropit()
        elif choice == "3":
            show_statistics()
        elif choice == "4":
            create_backup()
        elif choice == "5":
            list_files_tab()
            open_file()
        elif choice == "6":
            search_files()
        elif choice == "7":
            edit_metadata()
        elif choice == "8":
            ai_menu()    
        elif choice == "0":
            break


def ai_menu():
    global AI_MODEL
    while True:
        print("Ustalony model:", AI_MODEL)
        print("""
        1. Wygeneruj opis dla wybranego dokumentu
        2. Zmiana modelu
        0. Menu głowne
        """)
        choice = input("Wybierz opcję: ")
        con_cls()
        if choice == "1":
            gen_title()
        elif choice == "2":
            list_ollama_models()
        elif choice == "0":
            break


if __name__ == "__main__":
    os.makedirs(DROPIT_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)
    main_menu()


def search_files():
    search_path = input("Podaj ścieżkę do przeszukania: ")
    if os.path.exists(search_path):
        search_and_copy_files(search_path)
        print("Wyszukiwanie i kopiowanie zakończone.")
    else:
        print("Podana ścieżka nie istnieje.")
