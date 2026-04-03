import flet as ft
import json, os

class GumApp():
    def __init__(self, page: ft.Page):
        self.page = page
        self.data_file = "./storage/data/gum_file.json"
        self.data = self.load_data()
        self.products_column = ft.Column(expand=True)
        self.notes_row = ft.Row()
        self.links_row = ft.Row()
        
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    return data[0], data[1]
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
                return []
            
        return "{}"

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)
    
    def save_data(self):
        """Сохраняет данные в JSON-файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.data = self.load_data()
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")

    def update_points_list(self):
        """Обновляет список точек в контейнере"""
        self.products_column.controls.clear()
        self.notes_row.controls.clear()
        self.links_row.controls.clear()

        self.links_row.controls.append(
            ft.Column([
                ft.Text(value="Полезные ссылки", size=14),
                ft.Row([
                    ft.Container(content=ft.Text(value=link, size=14, color=ft.Colors.BLUE), data=link, on_click=lambda e: self.open_link(e.control.data), padding=12)
                    for link in self.data[0]["links"]
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True)])
        )
        
        self.products_column.controls.append(ft.Card(content=ft.Container(content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(value=data['type'], weight="bold", size=14),
                                    ft.Text(value=f"{data['quantity']} {data['qtype']}", size=12, color=ft.Colors.GREY)
                                ]),
                                ft.Row([
                                    ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e: self.edit(self.data[1].index(e.control.data), e.control.data), data=data),
                                    ft.IconButton(icon=ft.Icons.DELETE, on_click=lambda e: self.delete(e.control.data), data=data)
                                ])
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN) 
                            for data in self.data[1]
                        ],
                        scroll=ft.ScrollMode.AUTO),
                        padding=ft.padding.all(14)),
                        elevation=3,
                        margin=ft.margin.only(bottom=10)))
        self.notes_row.controls.append(
                ft.Text(value=self.data[0]['notes'] if self.data[0]['notes'] else "", size=14),
            )
        
        self.page.update()

    def edit_note(self, note):
        notes = ft.TextField(value=note, expand=True)
        links = ft.TextField(label="Разделяйте ссылки запятыми", value=", ".join(self.data[0]["links"]), expand=True)
        content = ft.Column([
            links,
            notes
        ],
        scroll=ft.ScrollMode.AUTO)

        def save(e):
            self.data[0]["notes"] = notes.value.strip()
            self.data[0]["links"] = links.value.strip().split(", ")
            self.save_data()
            self.update_points_list()
            self.page.close(self.edit_note_dialog)

        self.edit_note_dialog = ft.AlertDialog(
            title=ft.Text("Изменение информации"),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.page.close(self.edit_note_dialog)),
                ft.TextButton("Сохранить", on_click=save),
            ]
        )

        self.page.open(self.edit_note_dialog)

    def delete(self, d):
        self.data[1].remove(d)
        self.save_data()
        self.update_points_list()
    
    def edit(self, product, data):
        type_field = ft.TextField(label="Тип товара", value=data["type"], expand=True)
        quantity_field = ft.TextField(label="Количество", value=data["quantity"], expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        qtype_field = ft.TextField(label="Тип количества (уп. или кор.)", value=data["qtype"], expand=True)

        error_text = ft.Text(
            color=ft.Colors.RED,
            visible=False
        )

        content = ft.Column([
            type_field,
            ft.Row([
                quantity_field,
                qtype_field
            ]),
            error_text
        ], scroll=ft.ScrollMode.AUTO)

        def save(e):
            new_product = {
                "type": type_field.value,
                "quantity": int(quantity_field.value),
                "qtype": qtype_field.value
            }
            if not type_field.value.strip():
                show_error("Введите тип продукта")
                return
            if not quantity_field.value:
                show_error("Введите количество продукта")
                return
            if not qtype_field.value.strip():
                show_error("Введите тип количества продукта")
                return
            try:
                count = int(quantity_field.value)
                if count <= 0:
                    raise ValueError
            except ValueError:
                show_error("Количество должно быть положительным целым числом")
                return
            
            self.data[1][product] = new_product
            self.save_data()
            print(self.data)
            self.update_points_list()
            self.page.close(self.edit_product_dialog)

        def show_error(message):
            """Показывает ошибку в диалоге"""
            nonlocal error_text
            error_text.value = message
            error_text.visible = True
            self.edit_product_dialog.update()

        self.edit_product_dialog = ft.AlertDialog(
            title=ft.Text("Изменение информации"),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.page.close(self.edit_product_dialog)),
                ft.TextButton("Сохранить", on_click=save),
            ]
        )

        self.page.open(self.edit_product_dialog)

    def add_product(self, e):
        type_field = ft.TextField(label="Тип товара", expand=True)
        quantity_field = ft.TextField(label="Количество", expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        qtype_field = ft.TextField(label="Тип количества (уп. или кор.)", expand=True)

        error_text = ft.Text(
            color=ft.Colors.RED,
            visible=False
        )

        content = ft.Column([
            type_field,
            ft.Row([
                quantity_field,
                qtype_field
            ]),
            error_text
        ], scroll=ft.ScrollMode.AUTO)

        def save(e):
            if not type_field.value.strip():
                show_error("Введите тип продукта")
                return
            if not quantity_field.value:
                show_error("Введите количество продукта")
                return
            if not qtype_field.value.strip():
                show_error("Введите тип количества продукта")
                return
            try:
                count = int(quantity_field.value)
                if count <= 0:
                    raise ValueError
            except ValueError:
                show_error("Количество должно быть положительным целым числом")
                return
            
            new_product = {
                "type": type_field.value,
                "quantity": int(quantity_field.value),
                "qtype": qtype_field.value
            }
            self.data[1].append(new_product)
            self.save_data()
            self.update_points_list()
            self.page.close(self.add_product_dialog)

        def show_error(message):
            """Показывает ошибку в диалоге"""
            nonlocal error_text
            error_text.value = message
            error_text.visible = True
            self.add_product_dialog.update()

        self.add_product_dialog = ft.AlertDialog(
            title=ft.Text("Изменение информации"),
            content=content,
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self.page.close(self.add_product_dialog)),
                ft.TextButton("Сохранить", on_click=save),
            ]
        )

        self.page.open(self.add_product_dialog)

    def build(self):
        self.page.floating_action_button = None
        self.page.appbar = None
        self.update_points_list()
        return ft.Container(content=ft.Column([
            ft.Row([
                ft.Text(value="Наполнители", weight=ft.FontWeight.BOLD, size=20),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.ADD, on_click=self.add_product, icon_size=30),
                    ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, note=self.data[0]['notes']: self.edit_note(note))
                ])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.links_row,
            self.notes_row,
            self.products_column
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True),
        padding=7)