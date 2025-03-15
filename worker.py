import threading
from enum import Enum
from subprocess import Popen
from time import sleep
from tkinter import Tk, Label, Canvas, Button

from requests import post
from os import path
from datetime import date, time
from json import load, dump
from typing import Callable
from threading import Thread


script_dir = path.dirname(path.abspath(__file__))

date = date.today()
selected_path = None


class Env(str, Enum):
    ...


def update_secrets(configs: dict) -> None:
    config_path = path.join(script_dir, "config.json")
    with open(config_path, "w") as updated_secrets:
        dump(configs, updated_secrets, indent=4)


def send_database(file_path: str) -> None:
    file_path_abs = path.join(script_dir, file_path)

    with open(file_path_abs, "rb") as dbf:
        file_name = path.basename(file_path)
        response = post(f"http://82.180.132.46/api/load-database/?access={token}", files={
            "dbf_data": (file_name, dbf, "application/octet-stream"),
        })

        if response.status_code == 202:
            Thread(
                target=handle_response,
                args=("Success", f"Base de datos {file_name} "
                                 f"enviado correctamente. ✅")
            ).start()
        else:
            Thread(
                target=handle_response,
                args=("Failed", "Hubo un error en el envío, "
                                "se recomienda ejecutar y cerrar controlep.exe 🔄")
            ).start()


def handle_response(status: str, message: str) -> None:
    alert_path = path.join(script_dir, "alert.exe")
    Popen([alert_path, status, message], shell=True)


if __name__ == "__main__":
    try:
        config_path = path.join(script_dir, "config.json")

        with open(config_path) as config:
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
        send_database(path.join(selected_path, "Alumnos.dbf"))
        send_database(path.join(selected_path, "cargas.dbf"))
        send_database(path.join(root_folder, "ASIGNATURAS.DBF"))

    except Exception as e:
        Thread(
            target=handle_response,
            args=("Error", f"Hubo un error en el envío, {str(e)} ❌")
        ).start()


class Application(Tk):
    def __init__(self):
        super().__init__()

        self.title("Cobach217 Task")
        self.geometry("300x400")
        self.resizable(False, False)

        self.widgets()

        threading.Thread(target=self.update_icons, daemon=True).start()

    def widgets(self):
        font = ("Arial", 11)

        Label(self, text="Colegio de Bachilleres de Chiapas", font=font).pack()
        Label(self, text="Cobach 217", font=font).pack()
        Label(self, text="Periodo ᕙ( A )ᕗ", font=font).pack()
        Label(self, text=f"Server ➥ {'http://82.180.132.46'}", font=font).pack(pady=10)

        self.label_dbf_topics = Label(self, text="Asignaturas DBF", font=font)
        self.label_dbf_topics.pack(pady=3)
        self.label_dbf_topics_icon = Label(self, text="⏳", font=font)
        self.label_dbf_topics_icon.pack()

        self.label_dbf_students = Label(self, text="Alumnos DBF", font=font)
        self.label_dbf_students.pack(pady=3)
        self.label_dbf_students_icon = Label(self, text="⏳", font=font)
        self.label_dbf_students_icon.pack()

        self.label_dbf_loads = Label(self, text="Cargas DBF", font=font)
        self.label_dbf_loads.pack(pady=3)
        self.label_dbf_loads_icon = Label(self, text="⏳", font=font)
        self.label_dbf_loads_icon.pack()

        self.label_period =Label(self, text="Nuevo Periodo", font=font)
        self.label_period_icon = Label(self, text="ᕙ( A )ᕗ", font=font)

    def update_icons(self):
        sleep(2)

        self.label_dbf_topics_icon.config(text="✅")
        self.label_dbf_students_icon.config(text="✅")
        self.label_dbf_loads_icon.config(text="✅")
        self.label_period.pack()
        self.label_period_icon.pack(pady=3)


app = Application()
app.mainloop()