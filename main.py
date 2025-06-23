import tkinter as tk
from PIL import Image, ImageTk


class ImageViewer:
    def __init__(self, root, image):
        self.root = root
        self.original_image = image
        self.zoom = 1.0

        # Центр зображення (у пікселях Canvas)
        self.offset_x = 0
        self.offset_y = 0

        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", self.resize_to_fit)
        
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/macOS
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux (up)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux (down)
        
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_move)


    def resize_to_fit(self, event=None):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        img_width, img_height = self.original_image.size

        # Обчислюємо масштаб під вікно
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        self.zoom = min(scale_w, scale_h)

        # Центруємо зображення
        self.offset_x = canvas_width // 2
        self.offset_y = canvas_height // 2

        self.resize_and_draw()

        self.resize_and_draw()


    def resize_and_draw(self, event=None):
        img_width, img_height = self.original_image.size

        # Розрахунок нового розміру
        new_width = int(img_width * self.zoom)
        new_height = int(img_height * self.zoom)

        resized = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")


        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_image)
        self.canvas.image = self.tk_image
    
        # Зберігаємо для подальших обчислень
        self.displayed_size = (new_width, new_height)


    def on_mouse_wheel(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        dx = canvas_x - self.offset_x
        dy = canvas_y - self.offset_y


        # Cross-platform scroll
        direction = 0
        if hasattr(event, 'delta'):  # Windows/macOS
            direction = 1 if event.delta > 0 else -1
        elif event.num == 4:  # Linux scroll up
            direction = 1
        elif event.num == 5:  # Linux scroll down
            direction = -1

        # Змінюємо зум
        zoom_step = 0.1
        new_zoom = self.zoom + direction * zoom_step
        new_zoom = max(0.1, min(new_zoom, 5.0))

        if new_zoom == self.zoom:
            return
        
        # Обчислюємо нове положення центру
        scale_change = new_zoom / self.zoom
        self.zoom = new_zoom

        self.offset_x -= int(dx * (scale_change - 1))
        self.offset_y -= int(dy * (scale_change - 1))

        # self.enforce_bounds()
        self.resize_and_draw()


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

        min_x = canvas_w - img_w // 2
        max_x = img_w // 2

        min_y = canvas_h - img_h // 2
        max_y = img_h // 2

        self.offset_x = min(max(self.offset_x, min_x), max_x)
        self.offset_y = min(max(self.offset_y, min_y), max_y)
        



def main(root):
    img = Image.open("assets/image.jpg")
    app = ImageViewer(root=root, image=img)

if __name__ == '__main__':
    root = tk.Tk()
    main(root)
    root.mainloop()