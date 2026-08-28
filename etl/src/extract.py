import os
import zipfile

from tqdm import tqdm

from config import RAW_DIR, EXTRACTED_DIR


def extract_zip_files():

    os.makedirs(EXTRACTED_DIR, exist_ok=True)

    zip_files = [
        file
        for file in os.listdir(RAW_DIR)
        if file.lower().endswith(".zip")
    ]

    if not zip_files:
        print("Nenhum arquivo ZIP encontrado.")
        return

    print(f"{len(zip_files)} arquivos ZIP encontrados.")

    for filename in tqdm(zip_files, desc="Extraindo arquivos"):

        zip_path = os.path.join(RAW_DIR, filename)

        destination = os.path.join(
            EXTRACTED_DIR,
            os.path.splitext(filename)[0]
        )

        os.makedirs(destination, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(destination)

        print(f"Extraído: {filename}")


if __name__ == "__main__":
    extract_zip_files()