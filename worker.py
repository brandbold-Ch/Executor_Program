import os
import threading
from subprocess import Popen
from tkinter import Tk, Label, Button, messagebox
from requests import post
from os import path
from datetime import date
from json import load, dump


script_dir = path.dirname(path.abspath(__file__))
config_path = path.join(script_dir, "config.json")
current_year = date.today().year


class C:
    DATA = None
    PERIOD = None
    TOKEN = None
    ROOT_DIR = None
    CAMPUS = None
    PATHS = None
    URL = None


class Application(Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Cobach217 Task")
        self.geometry("300x330")
        self.resizable(False, False)

        self.label_period_icon = None
        self.label_period = None
        self.label_dbf_loads_icon = None
        self.label_dbf_loads = None
        self.label_dbf_students_icon = None
        self.label_dbf_students = None
        self.label_dbf_topics_icon = None
        self.label_dbf_topics = None
        self.button = None
        self.text = None

        self.widgets()
        self.task()

    def task(self, mode=None) -> None:
        threading.Thread(target=self.update_icons, args=(mode,), daemon=True).start()

    def widgets(self) -> None:
        font = ("Arial", 11)

        Label(self, text="Colegio de Bachilleres de Chiapas", font=font).pack()
        Label(self, text="Cobach 217", font=font).pack()
        Label(self, text=f"Periodo ➥ {C.PERIOD}", font=font).pack()
        Label(self, text=f"Server ➥ {'http://144.172.96.237'}", font=font).pack(pady=10)

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

        self.label_period = Label(self, text="Nuevo Periodo", font=font)
        self.label_period_icon = Label(self, font=font)

        self.button = Button(self, text="Reenviar", command=lambda: self.task("back"))

    def update_icons(self, mode=None) -> None:
        if mode == "back":
            self.label_dbf_students_icon.config(text="⏳")
            self.label_dbf_loads_icon.config(text="⏳")
            self.label_dbf_topics_icon.config(text="⏳")
            self.button.pack_forget()

        current = check_period()
        res = [
            send(path.join(current, choice(current, "s"))),
            send(path.join(current, choice(current, "l"))),
            send(path.join(C.ROOT_DIR, choice(C.ROOT_DIR, "t")))
        ]

        self.label_dbf_students_icon.config(text=check_res(res[0]))
        self.label_dbf_loads_icon.config(text=check_res(res[1]))
        self.label_dbf_topics_icon.config(text=check_res(res[2]))

        if any(map(lambda e: isinstance(e, Exception), res)):
            self.button.pack(pady=10)

        if C.PERIOD != C.DATA["period"]:
            self.label_period.pack()
            self.label_period_icon.config(text=C.PERIOD)
            self.label_period_icon.pack(pady=3)


def update_conf(configs: dict) -> None:
    with open(config_path, "w") as new_data:
        dump(configs, new_data, indent=4)


def check_res(res: tuple | Exception) -> str:
    if isinstance(res, tuple):
        if res[1] != 202:
            messagebox.showerror("Crashed", str(res[0]))
            return "⚠️"
        return "✅"
    return "❌"


def check_file(_path: str, choices: list) -> str:
    return [p for p in os.listdir(_path) if p in choices][0]


def check_period() -> str:
    period_a = period(current_year, "a")
    period_b = period(current_year, "b")

    if exists(period_a) and exists(period_b):
        return select(period_a)

    elif exists(period_b) and not exists(period_a):
        return select(period_b)

    elif exists(period_a) and not exists(period_b):
        return select(period_a)

    else:
        return select(period(current_year - 1, "a"))


def choice(_path: str, _for: str) -> str:
    for_s = ["alumnos.dbf", "alumnos.DBF", "Alumnos.dbf", "ALUMNOS.dbf", "Alumnos.DBF",
             "ALUMNOS.DBF", "ALUMNOS.dbf"]
    for_l = ["cargas.dbf", "cargas.DBF", "Cargas.dbf", "CARGAS.dbf", "Cargas.DBF",
             "CARGAS.DBF", "CARGAS.dbf"]
    for_t = ["asignaturas.dbf", "asignaturas.DBF", "Asignaturas.DBF", "Asignaturas.dbf",
             "ASIGNATURAS.dbf", "Asignaturas.DBF", "ASIGNATURAS.DBF", "ASIGNATURAS.dbf"]

    match _for:
        case "s":
            return check_file(_path, for_s)
        case "l":
            return check_file(_path, for_l)
        case "t":
            return check_file(_path, for_t)


def send(file_path: str) -> tuple | Exception:
    try:
        abspath = path.join(script_dir, file_path)

        with open(abspath, "rb") as dbf:
            file_name = path.basename(file_path)
            response = post(f"{C.URL}load-database/?access={C.TOKEN}", files={
                "dbf_data": (file_name, dbf, "application/octet-stream"),
            })

        return response.json(), response.status_code

    except Exception as ex:
        messagebox.showerror("Crashed", str(ex))
        return ex


def period(year: int, _period: str) -> str:
    return C.PATHS[f"period_{_period}"].replace("%", str(year))


def exists(_path) -> bool:
    return path.exists(_path)


def select(_path) -> str:
    C.DATA["period"] = _path[-9:-1]
    update_conf(C.DATA)
    return _path


if __name__ == "__main__":
    with open(config_path) as data:
        C.DATA = load(data)
        C.PATHS = C.DATA["paths"]
        C.ROOT_DIR = C.PATHS["root_folder"]
        C.PERIOD = C.DATA["period"]
        C.TOKEN = C.DATA["access_token"]
        C.URL = C.DATA["url"]
        C.CAMPUS = C.DATA["campus"]

    program_path = Popen([C.PATHS["program"]], shell=True)
    program_path.wait()

    Application().mainloop()
