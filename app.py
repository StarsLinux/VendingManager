import flet as ft
from pages.Main import MainPage
from pages.RentGum import GumApp
from pages.Analytics import Analytics

def setup(page: ft.Page):
    page.title = "Vending Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 10
    
    def navigate(e):
        page.controls.clear()
        page.floating_action_button = None

        if e.control.selected_index == 0:
            main = MainPage(page)
            page.add(main.build())
            page.floating_action_button = main.get_fab()
        elif e.control.selected_index == 1:
            main = Analytics(page)
            page.add(main.build())
            page.appbar = ft.AppBar(
                title=ft.Text(value="Аналитика", size=22, weight=ft.FontWeight.BOLD),
                actions=[main.build_menu()]
            )
        elif e.control.selected_index == 2:
            main = GumApp(page)
            page.add(main.build())

        page.update()
    
    # Навигационная панель
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, label="Главная", selected_icon=ft.Icons.HOME),
            ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS_OUTLINED, label="Данные", selected_icon=ft.Icons.ANALYTICS),
            ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_BAG_OUTLINED, label="Наполнители", selected_icon=ft.Icons.SHOPPING_BAG),
        ],
        on_change=navigate,
        selected_index=0
    )

    page.add(MainPage(page).build())

if __name__ == '__main__':
    ft.app(target=setup, assets_dir="assets/data")