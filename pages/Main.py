import flet as ft
from datetime import datetime
import json
import os
import utils as u
import asyncio

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

    def get_last_note_date(self):
        if not self.notes:
            return datetime.min
        return max(self.notes, key=lambda x: x.date).date
    
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
    
class MainPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_file = "./storage/data/vending_data.json"
        self.points = self.load_data()
        self.filtered_points = self.points.copy()
        self.search_field = ft.TextField(
            hint_text="Поиск по названию или адресу...",
            expand=True,
            on_change=self.search_points
        )
        self.sort_mode = "default"
        self.sort_button = ft.PopupMenuButton(
            icon=ft.Icons.SORT,
            items=[
                ft.PopupMenuItem(text="По умолчанию", on_click=lambda e: self.set_sort("default")),
                ft.PopupMenuItem(text="По состоянию", on_click=lambda e: self.set_sort("status")),
                ft.PopupMenuItem(text="Дата (старые)", on_click=lambda e: self.set_sort("date_asc")),
                ft.PopupMenuItem(text="Дата (новые)", on_click=lambda e: self.set_sort("date_desc")),
                ft.PopupMenuItem(text="Тип автомата", on_click=lambda e: self.set_sort("type")),
            ]
        )
        
        # Создаем контейнер для списка точек, который будем обновлять
        self.points_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        self.attached_photos = []
        self.editing_note = None
        self.notes_list = None
        self.render_notes = None
        self.linked_photos = None
        self.update_points_list()

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
                        
                        # Если есть хотя бы одно валидное фото или текст не пустой - сохраняем заметку
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
        
        return []

    def save_data(self):
        """Сохраняет данные в JSON-файл"""
        try:
            data = [point.to_dict() for point in self.points]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")

    def search_points(self, e=None):
        query = self.search_field.value.lower().strip()
        if not query:
            self.filtered_points = self.points.copy()
        else:
            self.filtered_points = [
                p for p in self.points 
                if query in p.name.lower() or query in p.address.lower()
            ]
        self.update_points_list()
        self.page.update()

    def set_sort(self, mode):
        self.sort_mode = mode

        if mode == "default":
            self.filtered_points = self.points.copy()

        elif mode == "status":
            order = {
                "Работает и заполнен": 0,
                "Работает и не заполнен": 1,
                "Сломан": 2
            }
            self.filtered_points.sort(key=lambda x: order.get(x.status, 3), reverse=True)

        elif mode == "date_asc":
            self.filtered_points.sort(
                key=lambda x: x.get_last_note_date()
            )

        elif mode == "date_desc":
            self.filtered_points.sort(
                key=lambda x: x.get_last_note_date(),
                reverse=True
            )

        elif mode == "type":
            self.filtered_points.sort(
                key=lambda x: x.machines[0].type if x.machines else ""
            )

        if mode != "default":
            self.sort_button.icon_color = ft.Colors.BLUE
        else:
            self.sort_button.icon_color = None

        self.update_points_list()
        self.page.update()

    def open_image_in_gallery(self, image_path):
        try:
            img = ft.Image(
                src=image_path,
                fit=ft.ImageFit.CONTAIN,
                expand=True
            )

            dialog = ft.AlertDialog(
                content=ft.Container(
                    width=self.page.width * 0.9,
                    height=self.page.height * 0.8,
                    content=img
                ),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda e: self.page.close(dialog))
                ]
            )

            self.page.open(dialog)
            self.page.update()

        except Exception as e:
            self.show_snackbar(f"Ошибка открытия изображения: {str(e)}")

    def update_points_list(self):
        """Обновляет список точек в контейнере"""
        self.points_container.controls.clear()
        for point in self.filtered_points:
            self.points_container.controls.append(self.build_point_card(point))

    def build_point_card(self, point: VendingPoint):
        status_color = point.get_status_color()
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    # Иконка статуса
                    ft.Icon(
                        point.machines[0].get_icon() if point.machines else ft.Icons.QUESTION_MARK,
                        color=status_color,
                        size=40
                    ),
                    
                    # Информация о точке
                    ft.Column([
                        ft.Text(point.name, weight="bold", size=16),
                        ft.Text(point.address, size=12, color=ft.Colors.GREY),
                        ft.Text(
                            f"Автоматы: {', '.join([f'{m.type} ({m.count})' for m in point.machines])}",
                            size=12
                        ),
                        # Добавляем отображение статуса в карточке
                        ft.Text(
                            point.status, 
                            size=12, 
                            color=status_color,
                            weight="bold"
                        )
                    ], expand=True),
                    
                    # Дни с последнего примечания
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                str(point.days_since_last_note()),
                                size=14,
                                weight="bold",
                                color=ft.Colors.BLUE
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        padding=10
                    )
                ]),
                padding=15,
                on_click=lambda e, p=point: self.show_point_details(p)
            ),
            elevation=3,
            margin=ft.margin.only(bottom=10)
        )

    def show_point_details(self, point: VendingPoint):
        """Показывает диалог с информацией о точке"""
        try:
            # Создаем содержимое диалога
            details_content = self.build_point_details(point)
            
            # Обновляем диалог
            self.detail_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Text(point.name, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        on_click=lambda e: self.edit_point_dialog(point)
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        tooltip="Удалить точку",
                        icon_color=ft.Colors.RED,
                        on_click=lambda e: self.delete_point(point)
                    )
                ]),
                content=details_content,
                actions=[
                    ft.TextButton("Закрыть", on_click=self.close_dialog)
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                inset_padding=20
            )
            
            # Устанавливаем диалог на страницу и открываем
            self.page.open(self.detail_dialog)
            self.page.update()
            
        except Exception as e:
            print(f"Ошибка при открытии диалога: {e}")

    def delete_point(self, point: VendingPoint):
        """Удаляет точку с подтверждением"""
        def confirm_delete(e):
            # Удаляем точку из всех списков
            if point in self.points:
                self.points.remove(point)
            if point in self.filtered_points:
                self.filtered_points.remove(point)
            
            # Сохраняем данные
            self.save_data()
            
            # Обновляем интерфейс
            self.update_points_list()
            self.page.update()
            
            # Закрываем оба диалога
            confirm_dialog.open = False
            if hasattr(self, 'detail_dialog'):
                self.detail_dialog.open = False
            
            self.page.update()
            self.show_snackbar(f"Точка '{point.name}' удалена")
        
        def cancel_delete(e):
            confirm_dialog.open = False
            self.page.update()
        
        # Диалог подтверждения удаления
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Подтверждение удаления"),
            content=ft.Text(f"Вы уверены, что хотите удалить точку '{point.name}'? Это действие нельзя отменить."),
            actions=[
                ft.TextButton("Отмена", on_click=cancel_delete),
                ft.TextButton(
                    "Удалить", 
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color=ft.Colors.RED)
                ),
            ]
        )
        
        self.page.open(confirm_dialog)
        self.page.update()
    
    def edit_note(self, note: Note):
        self.editing_note = note

        self.new_note_field.value = note.text

        self.attached_photos.clear()
        self.attached_photos.extend(note.photos)

        if self.load_linked_images and self.linked_photos:
            self.load_linked_images(self.linked_photos)

        self.load_linked_images(self.linked_photos)
        self.page.update()

    def delete_note(self, point: VendingPoint, note: Note):
        def confirm_delete(e):
            """Удаляет заметку из точки и обновляет JSON-файл"""
            try:
                # Удаляем заметку из списка точки
                if note in point.notes:
                    point.notes.remove(note)
                    self.save_data()

                    if self.render_notes:
                        self.render_notes()

                    self.page.update()
                    self.show_snackbar("Примечание удалено")
                else:
                    self.show_snackbar("Примечание не найдено")
                    
            except Exception as e:
                self.show_snackbar(f"Ошибка при удалении: {str(e)}")
            
            confirm_dialog.open = False
            self.page.update()

        def cancel_delete(e):
            confirm_dialog.open = False
            self.page.update()
        
        # Диалог подтверждения удаления
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Подтверждение удаления"),
            content=ft.Text(f"Вы уверены, что хотите удалить заметку? Это действие нельзя отменить."),
            actions=[
                ft.TextButton("Отмена", on_click=cancel_delete),
                ft.TextButton(
                    "Удалить", 
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color=ft.Colors.RED)
                ),
            ]
        )
        
        self.page.open(confirm_dialog)
        self.page.update()

    def edit_point_dialog(self, point: VendingPoint):
        """Диалог редактирования точки"""

        name_field = ft.TextField(label="Название точки", value=point.name)

        address_field = ft.TextField(
            label="Адрес",
            value=point.address
        )

        map_field = ft.TextField(
            label="Ссылка на карту",
            value=point.map_link
        )

        phones_field = ft.TextField(
            label="Телефоны (через запятую)",
            value=", ".join(point.phones)
        )

        status_dropdown = ft.Dropdown(
            label="Статус",
            value=point.status,
            options=[
                ft.dropdown.Option("Работает и заполнен"),
                ft.dropdown.Option("Работает и не заполнен"),
                ft.dropdown.Option("Сломан"),
            ]
        )

        machines_column = ft.Column()
        machine_blocks = []

        def build_machine_block(machine: VendingMachine):

            type_field = ft.TextField(
                label="Тип автомата",
                value=machine.type,
                expand=True
            )

            count_field = ft.TextField(
                label="Количество",
                value=str(machine.count),
                keyboard_type=ft.KeyboardType.NUMBER,
                width=120
            )

            subtype_fields = [
                ft.TextField(value=s, label="Подтип")
                for s in machine.subtypes
            ]

            subtypes_column = ft.Column(subtype_fields)

            def add_subtype(e):
                tf = ft.TextField(label="Подтип")
                subtype_fields.append(tf)
                subtypes_column.controls.append(tf)
                self.page.update()

            add_subtype_btn = ft.IconButton(
                icon=ft.Icons.ADD,
                tooltip="Добавить подтип",
                on_click=add_subtype
            )

            block = ft.Container(
                content=ft.Column([
                    ft.Row([
                        type_field,
                        count_field
                    ]),
                    subtypes_column,
                    add_subtype_btn
                ]),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10
            )

            machine_blocks.append({
                "type": type_field,
                "count": count_field,
                "subtypes": subtype_fields
            })

            return block

        # существующие машины
        for machine in point.machines:
            machines_column.controls.append(build_machine_block(machine))

        def add_machine(e):
            machine = VendingMachine("", 1, [])
            machines_column.controls.append(build_machine_block(machine))
            self.page.update()

        add_machine_btn = ft.ElevatedButton(
            "Добавить автомат",
            icon=ft.Icons.ADD,
            on_click=add_machine
        )

        def save(e):

            try:

                point.name = name_field.value
                point.address = address_field.value
                point.map_link = map_field.value
                point.status = status_dropdown.value

                phones = [p.strip() for p in phones_field.value.split(",") if p.strip()]
                point.phones = phones

                machines = []

                for block in machine_blocks:

                    m_type = block["type"].value
                    m_count = int(block["count"].value)

                    subtypes = [
                        f.value for f in block["subtypes"]
                        if f.value.strip()
                    ]

                    machines.append(
                        VendingMachine(
                            m_type,
                            m_count,
                            subtypes
                        )
                    )

                point.machines = machines

                self.save_data()
                self.update_points_list()

                self.page.close(self.edit_point_dialog_ref)
                self.page.update()

                self.show_snackbar("Точка обновлена")

            except Exception as ex:
                self.show_snackbar(f"Ошибка: {ex}")

        content = ft.Column(
            [
                name_field,
                address_field,
                map_field,
                phones_field,
                status_dropdown,

                ft.Divider(),

                ft.Text("Автоматы", weight="bold"),
                machines_column,
                add_machine_btn
            ],
            scroll=ft.ScrollMode.AUTO,
            height=500
        )

        self.edit_point_dialog_ref = ft.AlertDialog(
            title=ft.Text("Редактирование точки"),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.page.close(self.edit_point_dialog_ref)),
                ft.TextButton("Сохранить", on_click=save),
            ]
        )

        self.page.open(self.edit_point_dialog_ref)

    def build_point_details(self, point: VendingPoint):
        """Создает содержимое для диалога с информацией о точке"""

        self.notes_list = ft.Column(width=200)
        
        # Кликабельный адрес с ссылкой на карту
        address_row = ft.Row([
            ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.BLUE),
            ft.TextButton(
                content=ft.Text(point.address, size=14, color=ft.Colors.BLUE, text_align=ft.TextAlign.LEFT),
                on_click=lambda e: self.open_map(point.map_link) if point.map_link else self.show_snackbar("Ссылка на карту не указана"),
                expand=True
            )
        ],
        expand=True)
        phones_row = ft.Row([
            ft.Icon(ft.Icons.PHONE_CALLBACK, size=16, color=ft.Colors.BLUE),
            ft.Column(controls=[ft.TextButton(
                content=ft.Text(t, size=14, color=ft.Colors.BLUE, text_align=ft.TextAlign.LEFT),
                on_click=lambda e: self.open_map(f"tel:{t}"),
                expand=True
            ) for t in point.phones])
        ], expand=True) if point.phones else ft.Row(visible=False)
        
        # Выпадающий список для изменения статуса
        status_dropdown = ft.Dropdown(
            value=point.status,
            options=[
                ft.dropdown.Option("Работает и заполнен"),
                ft.dropdown.Option("Работает и не заполнен"),
                ft.dropdown.Option("Сломан"),
            ],
            on_change=lambda e: self.change_status(point, status_dropdown.value),
            width=200
        )
        
        # Информация о машинах
        machines_info = ft.Column()
        for machine in point.machines:
            machine_row = ft.Row([
                ft.Icon(machine.get_icon(), size=24),
                ft.Text(f"{machine.type} x{machine.count}", weight="bold"),
            ])
            machines_info.controls.append(machine_row)
            
            if machine.subtypes:
                subtypes_text = ft.Text(f"Подтипы: {', '.join(machine.subtypes)}", size=12)
                machines_info.controls.append(subtypes_text)

        image_obj = ft.Row(expand=1, wrap=False, scroll=ft.ScrollMode.ALWAYS, visible=False)

        async def load_image_async(image_obj, url):
            image_url = u.get_first_image_url(url)
            if image_url:
                image_obj.controls.append(
                    ft.Image(
                        src=image_url,
                        height=150,
                        fit=ft.ImageFit.COVER,
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        border_radius=ft.border_radius.all(10),
                    )
                )
                image_obj.visible = True
            else:
                image_obj.visible = False
            
            self.page.update()

        self.page.run_thread(
            lambda: asyncio.run(load_image_async(image_obj, point.map_link))
        )

        # Форма для нового примечания
        self.new_note_field = ft.TextField(
            hint_text="Добавить примечание...",
            multiline=True,
            expand=True
        )

        self.attached_photos = []

        linked_photos = ft.Row(expand=0, wrap=False, scroll=ft.ScrollMode.ALWAYS, visible=False)
        self.linked_photos = linked_photos
        
        def load_linked_images(image_obj, urls=self.attached_photos):
            image_obj.controls.clear()

            def remove_photo(path):
                if path in self.attached_photos:
                    self.attached_photos.remove(path)
                    load_linked_images(image_obj)

            if urls:
                for image_url in urls:
                    image_obj.controls.append(
                        ft.Container(
                            content=ft.Image(
                                src=image_url,
                                height=150,
                                fit=ft.ImageFit.COVER,
                                border_radius=ft.border_radius.all(10),
                            ),
                            on_click=lambda e, p=image_url: remove_photo(p)
                        )
                    )
                image_obj.visible = True
            else:
                image_obj.visible = False

            self.page.update()

        self.load_linked_images = load_linked_images

        def clear_linked_photos():
            linked_photos.controls.clear()
            linked_photos.visible = False
        
        self.clear_linked_photos = clear_linked_photos
        
        load_linked_images(linked_photos)
        
        def add_note(e):
            text = self.new_note_field.value.strip()

            if not text and not self.attached_photos:
                return

            if self.editing_note:
                self.editing_note.text = text
                self.editing_note.photos = self.attached_photos.copy()

                self.editing_note = None
                message = "Примечание обновлено"
            else:
                point.add_note(
                    Note(text, self.attached_photos.copy())
                )
                message = f"Примечание добавлено к {point.name}"

            self.attached_photos.clear()
            clear_linked_photos()
            self.new_note_field.value = ""

            self.save_data()

            if self.render_notes:
                self.render_notes()

            self.page.update()
            self.show_snackbar(message)

        def attach_photo(e):
            if e.files:
                for f in e.files:
                    if os.path.exists(f.path) and os.path.isfile(f.path):
                        selected_file = f.path
                        # Добавляем путь к файлу в список
                        self.attached_photos.append(selected_file)
                        # Обновляем отображение прикрепленных фото
                        load_linked_images(linked_photos)

        def render_notes():
            self.notes_list.controls.clear()

            sorted_notes = sorted(point.notes, key=lambda x: x.date, reverse=True)

            if not sorted_notes:
                self.notes_list.visible = False
                return

            for note in sorted_notes:
                note_imgs = ft.Row(expand=1, wrap=False, scroll=ft.ScrollMode.ALWAYS, visible=False)

                for image_url in note.photos:
                    note_imgs.controls.append(
                        ft.Container(
                            content=ft.Image(
                                src=image_url,
                                height=100,
                                fit=ft.ImageFit.COVER,
                                border_radius=ft.border_radius.all(10),
                            ),
                            on_click=lambda e, url=image_url: self.open_image_in_gallery(url)
                        )
                    )
                    note_imgs.visible = True

                note_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(note.text),
                            note_imgs,
                            ft.Text(
                                note.date.strftime("%d.%m.%Y %H:%M"),
                                size=10,
                                color=ft.Colors.GREY
                            ),
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    on_click=lambda e, n=note: self.delete_note(point, n)
                                ),
                                ft.IconButton(
                                    ft.Icons.EDIT,
                                    icon_color=ft.Colors.BLUE,
                                    on_click=lambda e, n=note: self.edit_note(n)
                                ),
                            ])
                        ]),
                        padding=10
                    )
                )

                self.notes_list.controls.append(note_card)

            self.notes_list.visible = True
        
        self.render_notes = render_notes
        render_notes()

        file_picker = ft.FilePicker(on_result=attach_photo)
        self.page.overlay.append(file_picker)

        return ft.Column([
            address_row,
            phones_row,
            image_obj,
            ft.Text("Статус:", weight="bold"),
            status_dropdown,
            ft.Divider(),
            ft.Text("Автоматы:", weight="bold"),
            machines_info,
            ft.Divider(),
            ft.Text("Новое примечание:", weight="bold"),
            ft.Column([
                linked_photos,
                ft.Row([
                    self.new_note_field,
                    ft.IconButton(
                        ft.Icons.ATTACH_FILE, 
                        tooltip="Прикрепить фото",
                        on_click=lambda _: file_picker.pick_files(
                            allowed_extensions=["jpg", "jpeg", "png", "gif"],
                            allow_multiple=True
                        )
                    ),
                    ft.IconButton(ft.Icons.SEND, on_click=add_note)
                ]),
            ]),
            ft.Divider(),
            ft.Text("История примечаний:", weight="bold"),
            self.notes_list
        ], scroll=ft.ScrollMode.AUTO)

    def change_status(self, point: VendingPoint, new_status):
        """Изменяет статус точки и сохраняет данные"""
        point.status = new_status
        self.save_data()
        # Закрываем диалог и открываем заново для обновления цвета статуса
        self.close_dialog()
        self.update_points_list()
        # Небольшая задержка перед повторным открытием
        import time
        time.sleep(0.1)
        self.show_point_details(point)
        self.show_snackbar(f"Статус {point.name} изменен на '{new_status}'")

    def open_map(self, map_link):
        """Открывает ссылку на карту в браузере"""
        try:
            self.page.launch_url(map_link)
        except Exception as e:
            self.show_snackbar(f"Не удалось открыть карту: {e}")

    def close_dialog(self, e=None):
        self.page.close(self.detail_dialog)
        self.attached_photos.clear()

    def update_dialog(self, e=None):
        self.page.close(self.detail_dialog)
        self.page.update()
        self.page.open(self.detail_dialog)

    def show_snackbar(self, message):
        """Показывает уведомление"""
        self.page.open(ft.SnackBar(content=ft.Text(message)))
        self.page.update()

    def show_add_point_dialog(self, e=None):
        """Показывает диалог для добавления новой точки"""
        # Поля формы
        name_field = ft.TextField(label="Название точки*", expand=True)
        address_field = ft.TextField(label="Адрес*", expand=True)
        map_link_field = ft.TextField(label="Ссылка на Яндекс.Карты", expand=True)
        
        # Поля для добавления автоматов
        machine_type_dropdown = ft.Dropdown(
            label="Тип автомата*",
            options=[
                ft.dropdown.Option("Трёхножка"),
                ft.dropdown.Option("Хватай-ка"),
                ft.dropdown.Option("Кофеаппарат"),
                ft.dropdown.Option("Бахилы")
            ],
            expand=True
        )
        machine_count_field = ft.TextField(
            label="Количество*",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100
        )
        subtypes_field = ft.TextField(
            label="Подтипы (через запятую)",
            hint_text="жвачки, игрушки, конфеты",
            expand=True
        )
        
        machines_list = ft.Column()
        machines_container = ft.Container(
                content=machines_list,
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=5,
                height=150,
                visible=False
            )
        new_machines = []
        
        def add_machine(e):
            if machine_type_dropdown.value and machine_count_field.value:
                try:
                    count = int(machine_count_field.value)
                    if count <= 0:
                        raise ValueError
                except ValueError:
                    show_error("Количество должно быть положительным числом")
                    return
                    
                subtypes = [s.strip() for s in subtypes_field.value.split(",")] if subtypes_field.value else []
                machine = VendingMachine(
                    machine_type_dropdown.value,
                    count,
                    subtypes
                )
                new_machines.append(machine)
                
                # Добавляем в список
                machine_item = ft.Row([
                    ft.Icon(machine.get_icon(), size=20),
                    ft.Text(f"{machine.type} x{machine.count}", expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        on_click=lambda e, m=machine: remove_machine(m)
                    )
                ])
                machines_list.controls.append(machine_item)
                
                # Очищаем поля
                machine_type_dropdown.value = None
                machine_count_field.value = "1"
                subtypes_field.value = ""
                machines_container.visible = True
                
                self.add_point_dialog.update()
            else:
                show_error("Заполните тип и количество автомата")
        
        def remove_machine(machine):
            new_machines.remove(machine)
            # Перестраиваем список
            machines_list.controls.clear()
            for m in new_machines:
                machine_item = ft.Row([
                    ft.Icon(m.get_icon(), size=20),
                    ft.Text(f"{m.type} x{m.count}", expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        on_click=lambda e, mm=m: remove_machine(mm)
                    )
                ])
                machines_list.controls.append(machine_item)
            self.add_point_dialog.update()
        
        def save_point(e):
            if not name_field.value.strip():
                show_error("Введите название точки")
                return
            if not address_field.value.strip():
                show_error("Введите адрес точки")
                return
            if not new_machines:
                show_error("Добавьте хотя бы один автомат")
                return
                
            new_point = VendingPoint(
                name_field.value.strip(),
                address_field.value.strip(),
                new_machines.copy(),
                map_link=map_link_field.value.strip()
            )
            self.points.append(new_point)
            self.filtered_points = self.points.copy()
            self.save_data()
            self.update_points_list()
            self.page.update()
            self.page.close(self.add_point_dialog)
            self.page.update()
            self.show_snackbar(f"Точка '{name_field.value}' добавлена")
        
        def show_error(message):
            """Показывает ошибку в диалоге"""
            nonlocal error_text
            error_text.value = message
            error_text.visible = True
            self.add_point_dialog.update()
        
        # Текст для ошибок
        error_text = ft.Text(
            color=ft.Colors.RED,
            visible=False
        )
        
        content = ft.Column([
            name_field,
            address_field,
            map_link_field,
            ft.Divider(),
            ft.Text("Автоматы:", weight="bold"),
            ft.Row([
                machine_type_dropdown,
                machine_count_field,
            ]),
            subtypes_field,
            ft.ElevatedButton("Добавить автомат", on_click=add_machine),
            machines_container,
            error_text
        ], scroll=ft.ScrollMode.AUTO, height=400)
        
        self.add_point_dialog = ft.AlertDialog(
            title=ft.Text("Добавить новую точку"),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.page.close(self.add_point_dialog)),
                ft.TextButton("Сохранить", on_click=save_point),
            ]
        )
        
        self.page.open(self.add_point_dialog)
        self.page.update()

    def add_point(self, e):
        """Обработчик кнопки добавления точки"""
        self.show_add_point_dialog(e)

    def get_fab(self):
        return ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip="Добавить точку",
            on_click=self.add_point
        )

    def build(self):
        # Панель поиска и фильтров
        self.page.floating_action_button = self.get_fab()
        self.page.appbar = None
        search_row = ft.Row([
            self.search_field,
            self.sort_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            content=ft.Column([
                search_row,
                self.points_container,
            ]),
            padding=15,
            expand=True
        )