import flet as ft
from datetime import datetime
import json
import os
import utils as u

# Модели данных
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
    
    def get_icon(self):
        icons = {
            "Трёхножка": ft.Icons.LOCAL_PLAY,
            "Хватай-ка": ft.Icons.CATCHING_POKEMON,
            "Кофеаппарат": ft.Icons.LOCAL_CAFE,
            "Бахилы": ft.Icons.SNOWSHOEING
        }
        return icons.get(self.type, ft.Icons.BUSINESS)

class Note:
    def __init__(self, text, photos, date=None):
        self.text = text
        self.photos = photos if photos is not None else []
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
        return cls(data["text"], data.get("photos", []), date)

class VendingPoint:
    def __init__(self, name, address, machines, status="Работает и заполнен", map_link="", phones=[]):
        self.name = name
        self.address = address
        self.machines = machines
        self.status = status
        self.map_link = map_link
        self.phones = phones
        self.notes = []
        self.id = hash(f"{name}{address}")
    
    def add_note(self, note):
        self.notes.append(note)
    
    def days_since_last_note(self):
        if not self.notes:
            return "∞"
        last_note = max(self.notes, key=lambda x: x.date)
        delta = u.gen_activity_date(last_note.date)
        return delta
    
    def get_status_color(self):
        colors = {
            "Работает и заполнен": ft.Colors.GREEN,
            "Работает и не заполнен": ft.Colors.ORANGE,
            "Сломан": ft.Colors.RED
        }
        return colors.get(self.status, ft.Colors.GREY)
    
    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "map_link": self.map_link,
            "status": self.status,
            "machines": [machine.to_dict() for machine in self.machines],
            "phones": self.phones,
            "notes": [note.to_dict() for note in self.notes]
        }
    
    @classmethod
    def from_dict(cls, data):
        point = cls(
            data["name"],
            data["address"],
            [VendingMachine.from_dict(machine) for machine in data["machines"]],
            data.get("status", "Работает и заполнен"),
            data.get("map_link", ""),
            data["phones"]
        )
        point.notes = [Note.from_dict(note) for note in data.get("notes", [])]
        point.phones = data["phones"]
        return point

class Analytics:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_file = "./storage/data/vending_data.json"
        self.points = self.load_data()

    def load_data(self):
        """Загружает данные из JSON-файла и очищает несуществующие заметки"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Создаем временный список для хранения очищенных данных
                cleaned_data = []
                removed_notes = 0
                
                for point_data in data:
                    # Очищаем заметки для каждой точки
                    cleaned_notes = []
                    
                    for note in point_data['notes']:
                        # Проверяем существование всех фото в заметке
                        valid_photos = [
                            photo for photo in note['photos']
                            if os.path.exists(photo) and os.path.isfile(photo)
                        ]
                        
                        activity_date = u.gen_activity_date(datetime.fromisoformat(note["date"]) if note["date"] != "" else datetime.now())
                        
                        # Если есть хотя бы одно валидное фото или текст не пустой - сохраняем заметку
                        if any(substring in activity_date for substring in ["год", "года", "лет"]):
                            removed_notes += 1
                        else:
                            if valid_photos or note['text'].strip():
                                # Обновляем список фото в заметке
                                note['photos'] = valid_photos
                                cleaned_notes.append(note)
                            else:
                                removed_notes += 1
                    
                    # Обновляем список заметок в точке
                    point_data['notes'] = cleaned_notes

                    cleaned_data.append(point_data)
                
                # Сохраняем очищенные данные обратно в файл
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                
                # Конвертируем очищенные данные в объекты
                return [VendingPoint.from_dict(point_data) for point_data in cleaned_data]
                
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
                return []
        
        return "{}"

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
        self.page.floating_action_button = None
        analytics = self.build_analytics()
        types = self.get_types()
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(value="Аналитика", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(value="Точки", size=20, weight=ft.FontWeight.BOLD),
                    analytics,
                    ft.Text(value="Типы автоматов", size=20, weight=ft.FontWeight.BOLD),
                    types
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
        ),
        padding=10)