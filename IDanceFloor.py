import cv2
import numpy as np
import time
import random

# --- CÁMARA ---
cap = cv2.VideoCapture(0)

# --- RANGOS HSV DE COLOR (para control del jugador) ---
color_ranges = {
    "red":   [(0, 100, 100), (10, 255, 255)],
    "green": [(45, 50, 50), (75, 255, 255)],
    "blue":  [(100, 50, 50), (130, 255, 255)],
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
cell_size = 60  # un poco más grande
margin = 80
top_offset = 180
height = grid_size * cell_size + top_offset + 80
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

# --- POSICIÓN DEL JUGADOR ---
player_pos = [grid_size // 2, grid_size // 2]
move_delay = 0.4
last_move = time.time()

# --- PARTICULAS DE FONDO ---
num_particles = 60
particles = np.random.randint(0, [width, height], (num_particles, 2))
particle_speeds = np.random.randint(1, 4, num_particles)

# --- FUNCIONES ---
def detectar_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color, (low, high) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(low), np.array(high))
        if cv2.countNonZero(mask) > 4000:
            return color
    return None

def seleccionar_dificultad():
    global round_duration, difficulty_selected, difficulty
    frame = np.zeros((500, 800, 3), dtype=np.uint8)
    cv2.putText(frame, "Selecciona dificultad:", (200, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, "[F] Facil (10s)", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    cv2.putText(frame, "[N] Normal (7s)", (250, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
    cv2.putText(frame, "[D] Dificil (5s)", (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    cv2.putText(frame, "Presiona la tecla correspondiente", (150, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
    cv2.imshow("Color Dance - OpenCV", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('f'):
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

def mostrar_pantalla_final(resultado):
    frame = np.zeros((500, 800, 3), dtype=np.uint8)
    if resultado == "win":
        cv2.putText(frame, "¡VICTORIA!", (220, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 4)
        cv2.putText(frame, "Has ganado el Color Dance :)", (150, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
    else:
        cv2.putText(frame, "DERROTA", (270, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
        cv2.putText(frame, "No llegaste al color a tiempo", (160, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
    
    cv2.putText(frame, "Presiona [R] para reiniciar o [Q] para salir", (130, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
    cv2.imshow("Color Dance - OpenCV", frame)

def fondo_animado(frame, t):
    """Crea un degradado dinámico y partículas."""
    h, w = frame.shape[:2]
    for y in range(h):
        r = int(80 + 80 * np.sin(y/80 + t))
        g = int(60 + 120 * np.sin(y/60 + t/2))
        b = int(100 + 100 * np.sin(y/100 + t/3))
        cv2.line(frame, (0, y), (w, y), (b, g, r), 1)

    # Partículas flotando
    for i in range(num_particles):
        x, y = particles[i]
        cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)
        particles[i, 1] += particle_speeds[i]
        if particles[i, 1] > h:
            particles[i, 1] = 0
            particles[i, 0] = random.randint(0, w)

# --- BUCLE PRINCIPAL ---
while True:
    ret, frame_cam = cap.read()
    if not ret:
        break
    frame_cam = cv2.flip(frame_cam, 1)

    # Pantalla de dificultad
    if not difficulty_selected:
        seleccionar_dificultad()
        continue

    # Pantalla final
    if game_over:
        mostrar_pantalla_final(game_result)
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

    # Detección de color
    color_detectado = detectar_color(frame_cam)

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

    # Fases del juego
    elapsed = time.time() - round_start
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

    # Fondo animado
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    fondo_animado(frame, time.time() / 2)

    # HUD
    cv2.putText(frame, f"Dificultad: {difficulty.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"Puntuacion: {score}/5", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"Color objetivo: {target_color.upper()}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_map[target_color], 2)

    # Tablero
    for i in range(grid_size):
        for j in range(grid_size):
            color = grid[i, j]
            x1, y1 = margin + j * cell_size, top_offset + i * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            if show_phase or color == target_color:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color_map[color], -1)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 1)

    # Jugador
    player_x = margin + player_pos[1] * cell_size + cell_size // 2
    player_y = top_offset + player_pos[0] * cell_size + cell_size // 2
    cv2.circle(frame, (player_x, player_y), 15, (255, 255, 255), -1)

    # Si acierta el color
    if not show_phase:
        current_color = grid[player_pos[0], player_pos[1]]
        if current_color == target_color:
            score += 1
            show_phase = True
            round_start = time.time()
            grid = np.random.choice(colors_list, (grid_size, grid_size))
            target_color = random.choice(colors_list)
            if score >= 5:
                game_over = True
                game_result = "win"

    cv2.imshow("Color Dance - OpenCV", frame)
    cv2.imshow("Camara", frame_cam)

    key = cv2.waitKey(30) & 0xFF
    if key == 27 or key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
