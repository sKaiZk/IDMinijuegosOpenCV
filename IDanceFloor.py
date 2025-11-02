import cv2
import numpy as np
import time

# --- CONFIG CAMERA ---
cap = cv2.VideoCapture(0)

# --- RANGOS DE COLORES (para controlar al jugador) ---
color_ranges = {
    "red":   [(0, 120, 70), (10, 255, 255)],
    "green": [(36, 100, 100), (86, 255, 255)],
    "blue":  [(94, 80, 2), (126, 255, 255)],
}

# --- COLORES DEL JUEGO ---
color_map = {
    "red": (0, 0, 255),
    "green": (0, 255, 0),
    "blue": (255, 0, 0),
    "yellow": (0, 255, 255),
    "purple": (255, 0, 255),
    "cyan": (255, 255, 0)
}

colors_list = list(color_map.keys())

# --- TABLERO ---
grid_size = 10
cell_size = 50
margin = 50
height = grid_size * cell_size + 200
width = grid_size * cell_size + 100

# --- JUGADOR ---
player_pos = [width//2, height - 100]
player_radius = 15
speed = 50

# --- VARIABLES DE JUEGO ---
score = 0
target_color = np.random.choice(colors_list)
grid = np.random.choice(colors_list, (grid_size, grid_size))
round_start = time.time()
round_duration = 10
show_phase = True
game_over = False

def detectar_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color, (low, high) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(low), np.array(high))
        if cv2.countNonZero(mask) > 4000:
            return color
    return None

# --- BUCLE PRINCIPAL ---
while True:
    ret, frame_cam = cap.read()
    if not ret:
        break
    frame_cam = cv2.flip(frame_cam, 1)

    color_detectado = detectar_color(frame_cam)

    # --- ACTUALIZAR MOVIMIENTO DEL JUGADOR ---
    if not game_over:
        if color_detectado == "red":
            player_pos[0] += speed
        elif color_detectado == "green":
            player_pos[0] -= speed
        elif color_detectado == "blue":
            player_pos[1] -= speed

        # límites
        player_pos[0] = np.clip(player_pos[0], margin, width - margin)
        player_pos[1] = np.clip(player_pos[1], 100, height - 50)

    # --- ACTUALIZAR FASE DE RONDA ---
    elapsed = time.time() - round_start
    if elapsed > round_duration:
        show_phase = not show_phase
        round_start = time.time()
        if show_phase:
            # Nueva ronda
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = np.random.choice(colors_list)
        else:
            # Fase de eliminación
            pass

    # --- DIBUJO DEL ESCENARIO ---
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, f"Puntuacion: {score}/5", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, f"Color objetivo: {target_color.upper()}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_map[target_color], 2)

    start_y = 100
    for i in range(grid_size):
        for j in range(grid_size):
            color = grid[i, j]
            x1, y1 = margin + j*cell_size, start_y + i*cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            if show_phase or color == target_color:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_map[color], -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,0), 1)

    # --- DIBUJAR JUGADOR ---
    cv2.circle(frame, tuple(player_pos), player_radius, (255,255,255), -1)

    # --- VERIFICAR SI ESTÁ SOBRE EL COLOR CORRECTO ---
    grid_x = (player_pos[0] - margin) // cell_size
    grid_y = (player_pos[1] - start_y) // cell_size

    if (0 <= grid_x < grid_size) and (0 <= grid_y < grid_size):
        current_color = grid[int(grid_y), int(grid_x)]
        if not show_phase and current_color == target_color:
            score += 1
            show_phase = True
            round_start = time.time()
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = np.random.choice(colors_list)

    # --- CONDICIÓN DE VICTORIA ---
    if score >= 5:
        game_over = True
        cv2.putText(frame, "VICTORIA!", (width//3, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 4)

    cv2.imshow("Color Dance - OpenCV", frame)
    cv2.imshow("Camara", frame_cam)

    key = cv2.waitKey(30) & 0xFF
    if key == 27 or key == ord('q'):
        break
    if key == ord('r'):
        score = 0
        game_over = False
        round_start = time.time()
        show_phase = True
        player_pos = [width//2, height - 100]

cap.release()
cv2.destroyAllWindows()