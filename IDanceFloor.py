import cv2
import numpy as np
import time
import random

# --- CÁMARA ---
cap = cv2.VideoCapture(0)

# --- RANGOS HSV DE COLOR ---
color_ranges = {
    "red": [(0, 100, 100), (10, 255, 255)],
    "green": [(45, 50, 50), (75, 255, 255)],
    "blue": [(100, 50, 50), (130, 255, 255)],
    "yellow": [(20, 100, 100), (30, 255, 255)]
}

# --- COLORES DISPONIBLES DEL JUEGO ---
color_map = {
    "red": (0, 0, 255),
    "green": (0, 255, 0),
    "blue": (255, 0, 0),
    "yellow": (0, 255, 255),
    "purple": (255, 0, 255),
    "cyan": (255, 255, 0)
}
colors_list = list(color_map.keys())

# --- DIMENSIONES DEL TABLERO ---
grid_size = 10
cell_size = 55
margin = 80
top_offset = 150
height = grid_size * cell_size + top_offset + 60
width = grid_size * cell_size + margin * 2

# --- VARIABLES DEL JUEGO ---
score = 0
grid = np.random.choice(colors_list, (grid_size, grid_size))
target_color = random.choice(colors_list)
round_start = time.time()
round_duration = 10
show_phase = True
game_over = False
game_result = None
difficulty_selected = False
difficulty = "facil"
modo_infinito = False
modo_infinito_activo = False  # alternador visual

# --- POSICIÓN DEL JUGADOR ---
player_pos = [grid_size // 2, grid_size // 2]
move_delay = 0.4
last_move = time.time()

# --- PARTÍCULAS DEL FONDO ---
particles = []
for _ in range(40):
    particles.append({
        "x": random.randint(0, width),
        "y": random.randint(0, height),
        "r": random.randint(2, 6),
        "dx": random.choice([-1, 1]) * random.random() * 0.7,
        "dy": random.choice([-1, 1]) * random.random() * 0.7,
        "color": (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
    })

def actualizar_particulas(frame):
    for p in particles:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        if p["x"] < 0 or p["x"] > width: p["dx"] *= -1
        if p["y"] < 0 or p["y"] > height: p["dy"] *= -1
        cv2.circle(frame, (int(p["x"]), int(p["y"])), p["r"], p["color"], -1)

def crear_fondo_animado():
    base = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        ratio = i / height
        color = (
            int(80 + 100 * ratio),
            int(50 + 120 * (1 - ratio)),
            int(150 + 80 * np.sin(time.time() * 0.8 + ratio * 3))
        )
        base[i, :] = color
    actualizar_particulas(base)
    return base

def crear_fondo_resultado(resultado):
    base = np.zeros((400, 700, 3), dtype=np.uint8)
    for i in range(400):
        ratio = i / 400
        if resultado == "win":
            color = (int(60 + 100 * ratio), int(180 + 50 * ratio), int(80 + 50 * (1 - ratio)))
        else:
            color = (int(150 + 70 * ratio), int(40 + 30 * (1 - ratio)), int(90 + 60 * ratio))
        base[i, :] = color
    return base

def crear_fondo_menu():
    base = np.zeros((500, 700, 3), dtype=np.uint8)
    for i in range(500):
        ratio = i / 500
        color = (
            int(80 + 80 * np.sin(time.time() * 0.6 + ratio * 2)),
            int(100 + 120 * ratio),
            int(150 + 100 * (1 - ratio))
        )
        base[i, :] = color
    return base

def detectar_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color, (low, high) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(low), np.array(high))
        if cv2.countNonZero(mask) > 4000:
            return color
    return None

def draw_centered_text(frame, text, y, scale, color, thickness):
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0]
    x = (frame.shape[1] - text_size[0]) // 2
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

def seleccionar_dificultad():
    global round_duration, difficulty_selected, difficulty, modo_infinito, modo_infinito_activo
    
    # --- Fondo con gradiente animado ---
    frame = crear_fondo_menu()
    
    # --- Texto centralizado ---
    draw_centered_text(frame, "Selecciona dificultad", 100, 1.1, (255,255,255), 3)
    draw_centered_text(frame, "[F] Facil (10s)", 180, 0.8, (0,255,0), 2)
    draw_centered_text(frame, "[N] Normal (7s)", 230, 0.8, (0,255,255), 2)
    draw_centered_text(frame, "[D] Dificil (5s)", 280, 0.8, (0,0,255), 2)
    
    # --- Botón modo infinito ---
    estado = "ACTIVADO" if modo_infinito_activo else "DESACTIVADO"
    color_estado = (0,255,0) if modo_infinito_activo else (0,0,255)
    draw_centered_text(frame, f"[ESPACIO] Modo Infinito: {estado}", 350, 0.8, color_estado, 2)
    draw_centered_text(frame, "Presiona la tecla correspondiente", 420, 0.7, (240,240,240), 2)
    
    cv2.imshow("Color Dance - OpenCV", frame)
    key = cv2.waitKey(1) & 0xFF

    # --- Control de botones ---
    if key == 32:  # Espacio
        modo_infinito_activo = not modo_infinito_activo
        modo_infinito = modo_infinito_activo

    elif key == ord('f'):
        round_duration = 10
        difficulty = "facil"
        difficulty_selected = True
    elif key == ord('n'):
        round_duration = 7
        difficulty = "normal"
        difficulty_selected = True
    elif key == ord('d'):
        round_duration = 5
        difficulty = "dificil"
        difficulty_selected = True

def mostrar_pantalla_final(resultado, rondas):
    frame = crear_fondo_resultado(resultado)
    if resultado == "win":
        draw_centered_text(frame, "VICTORIA", 150, 2, (0,255,0), 5)
        draw_centered_text(frame, "Has ganado el Color Dance :)", 230, 0.9, (255,255,255), 2)
    else:
        draw_centered_text(frame, "DERROTA", 150, 2, (0,0,255), 5)
        draw_centered_text(frame, "No llegaste al color a tiempo", 230, 0.9, (255,255,255), 2)
    draw_centered_text(frame, f"Has sobrevivido {rondas} rondas", 280, 0.8, (255,255,255), 2)
    draw_centered_text(frame, "Presiona [R] para reiniciar o [Q] para salir", 340, 0.7, (230,230,230), 2)
    cv2.imshow("Color Dance - OpenCV", frame)

# --- BUCLE PRINCIPAL ---
while True:
    ret, frame_cam = cap.read()
    if not ret:
        break
    frame_cam = cv2.flip(frame_cam, 1)

    if not difficulty_selected:
        seleccionar_dificultad()
        continue

    if game_over:
        mostrar_pantalla_final(game_result, score)
        key = cv2.waitKey(30) & 0xFF
        if key == ord('r'):
            score = 0
            player_pos = [grid_size // 2, grid_size // 2]
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = random.choice(colors_list)
            round_start = time.time()
            show_phase = True
            game_over = False
            game_result = None
            difficulty_selected = False
        elif key == ord('q') or key == 27:
            break
        continue

    color_detectado = detectar_color(frame_cam)
    texto_color = f"Color detectado: {color_detectado.upper() if color_detectado else 'Ninguno'}"
    color_texto = color_map[color_detectado] if color_detectado in color_map else (255, 255, 255)
    cv2.putText(frame_cam, texto_color, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)

    # Movimiento según color detectado
    if (time.time() - last_move > move_delay):
        if color_detectado == "red":
            player_pos[1] = min(player_pos[1] + 1, grid_size - 1)
            last_move = time.time()
        elif color_detectado == "green":
            player_pos[1] = max(player_pos[1] - 1, 0)
            last_move = time.time()
        elif color_detectado == "blue":
            player_pos[0] = max(player_pos[0] - 1, 0)
            last_move = time.time()
        elif color_detectado == "yellow":
            player_pos[0] = min(player_pos[0] + 1, grid_size - 1)
            last_move = time.time()

    elapsed = time.time() - round_start
    remaining_time = max(0, int(round_duration - elapsed))

    if elapsed > round_duration:
        if not show_phase:
            current_color = grid[player_pos[0], player_pos[1]]
            if current_color != target_color:
                game_over = True
                game_result = "lose"
                continue
        show_phase = not show_phase
        round_start = time.time()
        if show_phase:
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = random.choice(colors_list)

    frame = crear_fondo_animado()
    cv2.putText(frame, f"Modo: {difficulty.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    if modo_infinito:
        # En modo infinito solo se muestra la puntuación acumulada
        cv2.putText(frame, f"Puntuacion: {score}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    else:
        # En modo normal se muestra la ronda actual (de 5)
        cv2.putText(frame, f"Ronda: {score + 1}/5", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"Color objetivo: {target_color.upper()}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_map[target_color], 2)
    cv2.putText(frame, f"Tiempo: {remaining_time}s", (width - 200, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    for i in range(grid_size):
        for j in range(grid_size):
            color = grid[i, j]
            x1, y1 = margin + j * cell_size, top_offset + i * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            if show_phase or color == target_color:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_map[color], -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 1)

    player_x = margin + player_pos[1] * cell_size + cell_size // 2
    player_y = top_offset + player_pos[0] * cell_size + cell_size // 2
    cv2.circle(frame, (player_x, player_y), 18, (255, 255, 255), -1)

    if not show_phase:
        current_color = grid[player_pos[0], player_pos[1]]
        if current_color == target_color:
            score += 1
            show_phase = True
            round_start = time.time()
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = random.choice(colors_list)
            if not modo_infinito and score >= 5:
                game_over = True
                game_result = "win"

    cv2.imshow("Color Dance - OpenCV", frame)
    cv2.imshow("Camara", frame_cam)

    key = cv2.waitKey(30) & 0xFF
    if key == 27 or key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
