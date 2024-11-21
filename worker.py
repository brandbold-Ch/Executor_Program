from subprocess import Popen
from requests import post
from os import path
from datetime import date
from json import load, dump
from typing import Callable

date = date.today()
selected_path = None


def update_secrets(configs: dict) -> None:
    with open("config.json", "w") as updated_secrets:
        dump(configs, updated_secrets, indent=4)


def send_database(file_path: str) -> None:
    with open(path.abspath(file_path), "rb") as dbf:
        file_name = path.basename(file_path)
        response = post(f"http://82.180.132.46:8000/load-database/?access={token}", files={
            "dbf_data": (file_name, dbf, "application/octet-stream"),
        })

        if response.status_code == 202:
            Popen([path.abspath("alert.exe"), "Success",
                   f"Base de datos {file_name} enviado correctamente.✅"], shell=True)
        else:
            Popen([path.abspath("alert.exe"), "Failed",
                   "Hubo un error en el envío, se recomienda ejecutar y cerrar controlep.exe 🔄"], shell=True)


if __name__ == "__main__":
    try:
        with open("config.json") as config:
            secrets: dict = load(config)
            paths = secrets["paths"]
            root_folder = paths["root_folder"]
            current_period = secrets["period"]
            token = secrets["access_token"]
            sem_a_path = lambda year: str(paths["period_a"]).replace("<>", str(year))
            sem_b_path = lambda year: str(paths["period_b"]).replace("<>", str(year))

        program_path = Popen([paths["program"]], shell=True)
        program_path.wait()

        def check_period_a() -> str | Callable:
            if secrets["period"] == "A":
                if path.isdir(sem_a_path(date.year)) and path.isdir(sem_b_path(date.year)):
                    return sem_a_path(date.year)

                elif path.isdir(sem_b_path(date.year)) and path.isdir(sem_a_path(date.year)) is False:
                    secrets["period"] = "B"
                    update_secrets(secrets)
                    return check_period_b()

                elif path.isdir(sem_a_path(date.year - 1)) and path.isdir(sem_b_path(date.year - 1)):
                    return sem_a_path(date.year - 1)

        def check_period_b() -> str | Callable:
            if secrets["period"] == "B":
                if path.isdir(sem_b_path(date.year)) and path.isdir(sem_a_path(date.year) is False):
                    return sem_b_path(date.year)

                elif path.isdir(sem_b_path(date.year)) and path.isdir(sem_a_path(date.year)):
                    secrets["period"] = "A"
                    update_secrets(secrets)
                    return check_period_a()

        selected_path = check_period_a() if current_period == "A" else check_period_b()
        send_database(selected_path + "Alumnos.dbf")
        send_database(selected_path + "cargas.dbf")
        send_database(root_folder + "ASIGNATURAS.DBF")

    except Exception as e:
        Popen([path.abspath("alert.exe"), "Error",
               "Hubo un error en el envío. ❌", str(e)], shell=True)
