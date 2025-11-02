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
cell_size = 50
margin = 60
top_offset = 150
height = grid_size * cell_size + top_offset + 50
width = grid_size * cell_size + margin * 2

# --- VARIABLES DEL JUEGO ---
score = 0
grid = np.random.choice(colors_list, (grid_size, grid_size))
target_color = random.choice(colors_list)
round_start = time.time()
round_duration = 10  # depende de la dificultad
show_phase = True
game_over = False
game_result = None  # 'win' o 'lose'
difficulty_selected = False
difficulty = "facil"

# --- POSICIÓN DEL JUGADOR ---
player_pos = [grid_size // 2, grid_size // 2]
move_delay = 0.4
last_move = time.time()

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
    frame = np.zeros((400, 700, 3), dtype=np.uint8)
    cv2.putText(frame, "Selecciona dificultad:", (150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, "[F] Facil (10s)", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    cv2.putText(frame, "[N] Normal (7s)", (200, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
    cv2.putText(frame, "[D] Dificil (5s)", (200, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    cv2.putText(frame, "Presiona la tecla correspondiente", (150, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
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
    frame = np.zeros((400, 700, 3), dtype=np.uint8)
    if resultado == "win":
        cv2.putText(frame, "¡VICTORIA!", (180, 180), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 4)
        cv2.putText(frame, "Has ganado el Color Dance :)", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
    else:
        cv2.putText(frame, "DERROTA", (220, 180), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
        cv2.putText(frame, "No llegaste al color a tiempo", (120, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
    
    cv2.putText(frame, "Presiona [R] para reiniciar o [Q] para salir", (80, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
    cv2.imshow("Color Dance - OpenCV", frame)

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
            # Reiniciar
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

    # Detección de color para movimiento
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
            # Si no estaba en color correcto → derrota
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

    # Crear escenario
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, f"Dificultad: {difficulty.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"Puntuacion: {score}/5", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    cv2.putText(frame, f"Color objetivo: {target_color.upper()}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_map[target_color], 2)

    # Dibujar tablero
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
