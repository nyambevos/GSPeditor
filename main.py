import tkinter as tk
from PIL import Image, ImageTk
from functools import lru_cache


class ImageViewer:
    def __init__(self, root, image):
        self.root = root
        self.original_image = image
        self.zoom = 1.0

        # Центр зображення (у пікселях Canvas)
        self.offset_x = 0
        self.offset_y = 0

        self.canvas = tk.Canvas(root, background="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._after_id = None


        # Контейнер
        self.zoom_control = tk.Frame(root, borderwidth=0)
        self.zoom_control.place(x=10, y=10)

        # Змінюємо ширину колонок:
        self.zoom_control.grid_columnconfigure(0, weight=0)  # "-" — фіксована ширина
        self.zoom_control.grid_columnconfigure(1, weight=1)  # "Zoom: 100%" — розтягується
        self.zoom_control.grid_columnconfigure(2, weight=0)  # "+" — фіксована ширина
        self.zoom_control.grid_columnconfigure(3, weight=0)
        self.zoom_control.grid_columnconfigure(4, weight=1)
        self.zoom_control.grid_columnconfigure(5, weight=1)
        self.zoom_control.grid_columnconfigure(6, weight=1)
        self.zoom_control.grid_columnconfigure(7, weight=0)
        self.zoom_control.grid_rowconfigure(0, weight=1)

        # Кнопка "-", мітка, кнопка "+"
        self.zoom_out_btn = tk.Button(
            self.zoom_control, text="-", borderwidth=0, command=self.zoom_out
        )
        self.zoom_label = tk.Label(
            self.zoom_control, text="Zoom: 100%", padx=0, pady=0, anchor="center"
        )
        self.zoom_in_btn = tk.Button(
            self.zoom_control, text="+", borderwidth=0, command=self.zoom_in
        )
        self.fit_btn = tk.Button(
            self.zoom_control, text="🔁", borderwidth=0, command=self.fit_to_window
        )
        self.marker_label = tk.Label(
            self.zoom_control, text="Marker:", padx=0, pady=0, anchor="center"
        )
        self.marker_orig_x_label = tk.Label(
            self.zoom_control, text="X:", padx=0, pady=0, anchor="center"
        )
        self.marker_orig_y_label = tk.Label(
            self.zoom_control, text="Y:", padx=0, pady=0, anchor="center"
        )
        self.copy_btn = tk.Button(
            self.zoom_control, text="📋", borderwidth=0, command=self.copy_marker_to_clipboard
        )
        

        # Вставка з однаковими відступами
        self.zoom_out_btn.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=(6, 6), ipady=2)
        self.zoom_label.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=(6, 6), ipady=2)
        self.zoom_in_btn.grid(row=0, column=2, sticky="ns", padx=(5, 10), pady=(6, 6), ipady=2)
        self.fit_btn.grid(row=0, column=3, sticky="ns", padx=(5, 10), pady=(6, 6), ipady=2)
        self.marker_label.grid(row=0, column=4, sticky="nsew", padx=(5, 5), pady=(6, 6), ipady=2)
        self.marker_orig_x_label.grid(row=0, column=5, sticky="nsew", padx=(5, 5), pady=(6, 6), ipady=2)
        self.marker_orig_y_label.grid(row=0, column=6, sticky="nsew", padx=(5, 5), pady=(6, 6), ipady=2)
        self.copy_btn.grid(row=0, column=7, sticky="ns", padx=(10, 5), pady=(6, 6), ipady=2)

        self.canvas.bind("<Configure>", self.resize_to_fit)
        
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/macOS
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux (up)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux (down)
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_move)
        self.marker_orig_x = None
        self.marker_orig_y = None
        self.canvas.bind("<Button-3>", self.on_right_click)



    def resize_to_fit(self, event=None):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        img_width, img_height = self.original_image.size

        # Обчислюємо масштаб під вікно
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height

        self.zoom_min = min(scale_w, scale_h)
        self.zoom = min(scale_w, scale_h)
        
        # Центруємо зображення
        self.offset_x = canvas_width // 2
        self.offset_y = canvas_height // 2

        # Виводимо панель керування
        self.zoom_control.place(x=10, y=canvas_height - 50)

        self.resize_and_draw()


    @lru_cache(maxsize=16)
    def _get_resized_tk_image(self, zoom_percent):
        w, h = self.original_image.size
        new_w = int(w * zoom_percent // 100)
        new_h = int(h * zoom_percent // 100)
        img = self.original_image.resize((new_w, new_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def resize_and_draw(self, event=None):
        zoom_pct = self.zoom * 100
        self.tk_image = self._get_resized_tk_image(zoom_pct)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_image)
        self.canvas.image = self.tk_image
        self.zoom_label.config(text=f"Zoom: {zoom_pct:.0f}%")
        self.displayed_size = (self.tk_image.width(), self.tk_image.height())

        # Draw marker if set
        if self.marker_orig_x is not None and self.marker_orig_y is not None:
            img_w, img_h = self.displayed_size # Розмір зображення
            half_w, half_h = img_w / 2, img_h / 2 # Центер зображення
            draw_x = self.offset_x - half_w + self.marker_orig_x * self.zoom
            draw_y = self.offset_y - half_h + self.marker_orig_y * self.zoom
            r = 5
            self.canvas.create_oval(
                draw_x - r, draw_y - r, draw_x + r, draw_y + r,
                outline="red", width=2, tags="marker"
            )



    def on_mouse_wheel(self, event):
        # оновлюємо self.zoom одразу, але відкладаємо малювання
        direction = 1 if getattr(event, 'delta', 0) > 0 or event.num == 4 else -1

        if direction == 1:
            self.zoom_in()
        elif direction == -1:
            self.zoom_out()
        else:
            return
        
        self.enforce_bounds()

        # скасовуємо попередній запланований виклик
        if self._after_id:
            self.canvas.after_cancel(self._after_id)

        # сплануємо малювання через 50 мс
        self._after_id = self.canvas.after(50, self.resize_and_draw)


    def on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_move(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        self.offset_x += dx
        self.offset_y += dy

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.enforce_bounds()
        self.resize_and_draw()


    def enforce_bounds(self):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.displayed_size
        half_img_w = img_w / 2
        half_img_h = img_h / 2

        # Compute min and max allowed offsets
        min_x = min(half_img_w, canvas_w - half_img_w)
        max_x = max(half_img_w, canvas_w - half_img_w)
        min_y = min(half_img_h, canvas_h - half_img_h)
        max_y = max(half_img_h, canvas_h - half_img_h)

        # Clamp offsets so image cannot go out of bounds, without recentering
        self.offset_x = min(max(self.offset_x, min_x), max_x)
        self.offset_y = min(max(self.offset_y, min_y), max_y)


    def zoom_in(self):
        if self.zoom == self.zoom_min:
            self.set_zoom(self.zoom // 0.1 / 10 + 0.1)
        else:
            self.set_zoom(self.zoom + 0.1)

    def zoom_out(self):
        self.set_zoom(self.zoom - 0.1)

    def set_zoom(self, new_zoom):
        self.zoom = max(self.zoom_min, min(round(new_zoom, 1), 1.0))
        
        self.enforce_bounds()
        self.resize_and_draw()
    
    def fit_to_window(self):
        self.resize_to_fit()
        
    def on_right_click(self, event):
        # Compute top-left corner of the displayed image
        img_w, img_h = self.displayed_size # Розмір вікна
        half_w, half_h = img_w / 2, img_h / 2 # Координати центру вікна
        # Координати верхнього лівого кута зображення
        tl_x = self.offset_x - half_w 
        tl_y = self.offset_y - half_h

        # Convert click position to original image coordinates
        # Коодинати маркера на зображені
        rel_x = event.x - tl_x
        rel_y = event.y - tl_y
        
        # Координати на оригінальному зображені
        orig_x = rel_x / self.zoom
        orig_y = rel_y / self.zoom

        # Store marker coordinates
        self.marker_orig_x = orig_x
        self.marker_orig_y = orig_y

        self.marker_orig_x_label.config(text=f"X: {self.marker_orig_x:.2f}")
        self.marker_orig_y_label.config(text=f"Y: {self.marker_orig_y:.2f}")

        # Redraw image and marker
        self.resize_and_draw()
    
    def copy_marker_to_clipboard(self):
        # Якщо маркера ще немає — нічого не робимо
        if self.marker_orig_x is None or self.marker_orig_y is None:
            return

        # Форматуємо координати з двома знаками після крапки
        coords = f"{self.marker_orig_x:.2f}\u0009{self.marker_orig_y:.2f}"

        # Копіюємо в буфер обміну
        self.root.clipboard_clear()
        self.root.clipboard_append(coords)



def main(root):
    img = Image.open("assets/image.jpg")
    app = ImageViewer(root=root, image=img)

if __name__ == '__main__':
    root = tk.Tk()
    main(root)
    root.mainloop()

    