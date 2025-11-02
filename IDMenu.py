import cv2
import numpy as np
import os

# --- Configuración del menú ---
WIDTH, HEIGHT = 800, 600
BUTTON_COLOR = (60, 60, 200)
HOVER_COLOR = (100, 100, 255)
TEXT_COLOR = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX

# --- Botones del menú ---
buttons = [
    {"label": "Dance Floor", "file": "IDanceFloor.py"},
    {"label": "Simon Dice", "file": "Simondicv.py"},
    {"label": "Tetris", "file": "IDTetris.py"},
    {"label": "Salir", "file": None}
]

def draw_gradient_background(frame):
    for i in range(frame.shape[0]):
        color_ratio = i / frame.shape[0]
        r = int(40 + 60 * color_ratio)
        g = int(20 + 80 * (1 - color_ratio))
        b = int(100 + 100 * abs(0.5 - color_ratio))
        frame[i, :] = (b, g, r)
    return frame

def draw_menu(frame, mouse_pos):
    top_offset = 180  # Espacio superior
    spacing = 80      # Distancia entre botones

    for i, button in enumerate(buttons):
        y = top_offset + i * spacing
        text = button["label"]
        text_size = cv2.getTextSize(text, FONT, 1, 2)[0]
        x = (WIDTH - text_size[0]) // 2
        rect_w, rect_h = text_size[0] + 60, text_size[1] + 25
        rect_x, rect_y = x - 30, y - rect_h // 2

        if rect_x < mouse_pos[0] < rect_x + rect_w and rect_y - 10 < mouse_pos[1] < rect_y + rect_h:
            color = HOVER_COLOR
        else:
            color = BUTTON_COLOR

        cv2.rectangle(frame, (rect_x, rect_y - 10), (rect_x + rect_w, rect_y + rect_h), color, -1)
        cv2.putText(frame, text, (x, y + text_size[1] // 2), FONT, 1, TEXT_COLOR, 2, cv2.LINE_AA)

def main_menu():
    cv2.namedWindow("MiniJuegos OpenCV")
    mouse_pos = (0, 0)

    def mouse_callback(event, x, y, flags, param):
        nonlocal mouse_pos
        mouse_pos = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            top_offset = 180
            spacing = 80
            for i, button in enumerate(buttons):
                yb = top_offset + i * spacing
                text = button["label"]
                text_size = cv2.getTextSize(text, FONT, 1, 2)[0]
                xb = (WIDTH - text_size[0]) // 2
                rect_w, rect_h = text_size[0] + 60, text_size[1] + 25
                rect_x, rect_y = xb - 30, yb - rect_h // 2

                if rect_x < x < rect_x + rect_w and rect_y - 10 < y < rect_y + rect_h:
                    if button["file"] is None:
                        cv2.destroyAllWindows()
                        exit()
                    else:
                        os.system(f"python {button['file']}")

    cv2.setMouseCallback("MiniJuegos OpenCV", mouse_callback)

    while True:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        frame = draw_gradient_background(frame)
        draw_menu(frame, mouse_pos)
        title = "Selecciona un juego"
        tsize = cv2.getTextSize(title, FONT, 1.3, 3)[0]
        cv2.putText(frame, title, ((WIDTH - tsize[0]) // 2, 100), FONT, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.imshow("MiniJuegos OpenCV", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main_menu()
