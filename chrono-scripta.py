#!/usr/bin/python3

import os
import json
import hashlib
import shutil
import time
import zipfile
import subprocess
from pathlib import Path

DROPIT_DIR = "dropit"
STORAGE_DIR = "storage"
DB_FILE = "database.json"


def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


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
    subprocess.run(["xdg-open", str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_file_format(file_path):
    return file_path.suffix.lstrip(".").lower()


def move_file_to_storage(file_path, doc_date):
    year, month, day = doc_date.split("-")
    ext = file_path.suffix
    target_dir = Path(STORAGE_DIR) / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{day}{ext}"
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
        stored_path = move_file_to_storage(file_path, doc_date)
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


def list_files():
    db = load_database()
    for entry in db:
        print(f"{entry['index']}. {entry['date']} - {entry['refnum']} - {entry['description']}")
    file_index = int(input("Podaj numer pliku do otwarcia: "))
    for entry in db:
        if entry["index"] == file_index:
            open_doc(entry["path"])


def search_files():
    db = load_database()
    query = input("Wprowadź wyszukiwane hasło: ").lower()
    results = [entry for entry in db if any(query in str(v).lower() for v in entry.values())]
    for entry in results:
        print(f"{entry['index']}. {entry['path']} - {entry['description']}")
    file_index = int(input("Podaj numer pliku do otwarcia: "))
    for entry in results:
        if entry["index"] == file_index:
            open_doc(entry["path"])

def edit_file():
    pass

def main_menu():
    while True:
        print("""
        1. Przeskanuj folder "dropit"
        2. Obserwuj folder "dropit" w sposób ciągły
        3. Pokaż statystyki
        4. Spakuj cały folder "storage" wraz z bazą danych do ZIP
        5. Pokaż listę plików w "storage"
        6. Szukaj pliku w "storage"
        7. Edycja metadanych pliku
        8. Koniec
        """)
        choice = input("Wybierz opcję: ")
        if choice == "1":
            process_new_files()
        elif choice == "2":
            watch_dropit()
        elif choice == "3":
            show_statistics()
        elif choice == "4":
            create_backup()
        elif choice == "5":
            list_files()
        elif choice == "6":
            search_files()
        elif choice == "7":
            edit_file()
        elif choice == "8":
            break

if __name__ == "__main__":
    os.makedirs(DROPIT_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)
    main_menu()
