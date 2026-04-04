import flet as ft
from datetime import datetime
import json
import os
import utils as u

class VendingMachine:
    def __init__(self, machine_type, count=1, subtypes=None):
        self.type = machine_type
        self.count = count
        self.subtypes = subtypes or []

    def to_dict(self):
        return {
            "type": self.type,
            "count": self.count,
            "subtypes": self.subtypes
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["type"], data.get("count", 1), data.get("subtypes", []))


class Note:
    def __init__(self, text, photos, date=None):
        self.text = text
        self.photos = photos if photos else []
        self.date = date or datetime.now()

    def to_dict(self):
        return {
            "text": self.text,
            "photos": self.photos,
            "date": self.date.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        date = datetime.fromisoformat(data["date"]) if "date" in data else datetime.now()
        return cls(data.get("text", ""), data.get("photos", []), date)


class VendingPoint:
    def __init__(self, name, address, machines, status="Работает и заполнен", map_link="", phones=None):
        self.name = name
        self.address = address
        self.machines = machines
        self.status = status
        self.map_link = map_link
        self.phones = phones or []
        self.notes = []

    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "map_link": self.map_link,
            "status": self.status,
            "machines": [m.to_dict() for m in self.machines],
            "phones": self.phones,
            "notes": [n.to_dict() for n in self.notes]
        }

    @classmethod
    def from_dict(cls, data):
        point = cls(
            data["name"],
            data["address"],
            [VendingMachine.from_dict(m) for m in data.get("machines", [])],
            data.get("status", "Работает и заполнен"),
            data.get("map_link", ""),
            data.get("phones", [])
        )
        point.notes = [Note.from_dict(n) for n in data.get("notes", [])]
        return point

class Analytics:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_file = "./storage/data/vending_data.json"
        self.points = self.load_data()

        # FilePicker
        self.file_picker = ft.FilePicker(on_result=self.on_file_selected)
        self.page.overlay.append(self.file_picker)

        self.export_picker = ft.FilePicker(on_result=self.on_export_selected)
        self.page.overlay.append(self.export_picker)

        self.pending_action = None

    def load_data(self):
        if not os.path.exists(self.data_file):
            return []

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return [VendingPoint.from_dict(p) for p in data]

        except Exception as e:
            print("Ошибка загрузки:", e)
            return []

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self.points], f, ensure_ascii=False, indent=2)

    def validate_json(self, data):
        if not isinstance(data, list):
            return False

        required_keys = {"name", "address", "machines"}

        for point in data:
            if not all(k in point for k in required_keys):
                return False

        return True

    def on_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        path = e.files[0].path

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not self.validate_json(data):
                raise ValueError("Неверная структура JSON")

            self.points = [VendingPoint.from_dict(p) for p in data]
            self.save_data()

            self.page.snack_bar = ft.SnackBar(ft.Text("Импорт успешно выполнен"))
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка импорта: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def on_export_selected(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return

        try:
            with open(e.path, "w", encoding="utf-8") as f:
                json.dump([p.to_dict() for p in self.points], f, ensure_ascii=False, indent=2)

            self.page.snack_bar = ft.SnackBar(ft.Text("Экспорт выполнен"))
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка экспорта: {ex}"))
            self.page.snack_bar.open = True
            self.page.update()

    def open_import(self, e):
        self.pending_action = "import"
        self.file_picker.pick_files(allow_multiple=False)

    def open_export(self, e):
        self.pending_action = "export"
        self.export_picker.save_file(file_name="vending_data.json")

    def build_menu(self):
        return ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(text="Импорт точек", on_click=self.open_import),
                ft.PopupMenuItem(text="Экспорт точек", on_click=self.open_export),
            ]
        )

    def build_analytics(self):
        all_count = 0
        break_count = 0
        unfull_count = 0
        for p in self.points:
            if p.status == "Работает и не заполнен":
                unfull_count += 1
            elif p.status == "Сломан":
                break_count += 1

            all_count += 1

        graphs_row = ft.Row(expand=True, height=125)
        all_points_chart = ft.PieChart(
            sections=[
                ft.PieChartSection(
                    (break_count/all_count)*100,
                    color=ft.Colors.RED,
                    radius=20
                ),
                ft.PieChartSection(
                    (unfull_count/all_count)*100,
                    color=ft.Colors.YELLOW,
                    radius=20
                ),
                ft.PieChartSection(
                    ((all_count-break_count-unfull_count)/all_count)*100,
                    color=ft.Colors.GREEN,
                    radius=20
                )
            ],
            height=10,
            center_space_radius=29,
            expand=True
        )

        all_points = ft.Text(value=f"{all_count} Всего", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
        unfull_points = ft.Text(value=f"{unfull_count} Не заполнено", color=ft.Colors.ORANGE, weight=ft.FontWeight.BOLD)
        break_points = ft.Text(value=f"{break_count} Сломано", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)

        graphs_row.controls.append(all_points_chart)
        graphs_row.controls.append(ft.Column(
            [all_points, unfull_points, break_points],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        ))

        return graphs_row
    
    def get_types(self):
        types_col = ft.Column()
        all_subtypes = {}
        all_types = {}

        def extract_quantity(text):
            import re
            # Ищем число, за которым следуют маркеры типа 'x', 'шт.', 'единиц' и др.
            match = re.search(r'(\d+)\s*(?:x|х)', text)
            if match:
                return int(match.group(1))
            else:
                # Если не нашли по шаблону, ищем первое число в строке
                match = re.search(r'\d+', text)
                if match:
                    return int(match.group())
                else:
                    return 1  # Если число не найдено

        for point in self.points:
            for machine in point.machines:
                subtypes = machine.subtypes
                types = machine.type
                type_count = machine.count

                if types not in all_types:
                    all_types.update({types: int(type_count)})
                else:
                    all_types[types] = all_types[types] + int(type_count)

                for st in subtypes:
                    if st[3:].title() not in all_subtypes:
                        all_subtypes.update({st[3:].title(): extract_quantity(st)})
                    else:
                        all_subtypes[st[3:].title()] = all_subtypes[st[3:].title()] + extract_quantity(st)

        for t, tq in all_types.items():
            types_col.controls.append(ft.Row(
                    [
                        ft.Text(value=f"{tq} шт. ", size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(value=t, size=15, weight=ft.FontWeight.BOLD)
                    ],
                    scroll=ft.ScrollMode.AUTO
                ))
            
            if "трёхножка" in str(t).lower():
                for t, q in all_subtypes.items():
                    types_col.controls.append(ft.Row(
                        [
                            ft.Text(value=f"{q} шт. ", size=15),
                            ft.Text(value=t, size=15)
                        ],
                        scroll=ft.ScrollMode.AUTO
                    ))

        return types_col

    def build(self):
        self.page.appbar = ft.AppBar(
            ft.Text(value="Аналитика", size=22, weight=ft.FontWeight.BOLD),
            actions=[self.build_menu()]
        )
        self.page.floating_action_button = None
        analytics = self.build_analytics()
        types = self.get_types()
        return ft.Container(
            content=ft.Column(
                controls=[
                    analytics,
                    types
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
        ),
        padding=10)