import cv2
import numpy as np
import random
import time
import math

# ----------------------------
# CONFIG
# ----------------------------
WIDTH, HEIGHT = 900, 700
FPS = 30

color_ranges = {
    "red":   [(0, 100, 80), (10, 255, 255)],
    "green": [(40, 60, 60), (80, 255, 255)],
    "blue":  [(95, 60, 40), (130, 255, 255)],
    "yellow":[(18, 90, 90), (35, 255, 255)]
}

color_map = {
    "red":    (0, 0, 255),
    "green":  (0, 255, 0),
    "blue":   (255, 0, 0),
    "yellow": (0, 255, 255)
}

pulse_ok = (30, 200, 30)      # verde 
pulse_fail = (30, 30, 150)    # rojo/granate 
pulse_seq = (240, 240, 240)   # secuencia blanca

center_x, center_y = WIDTH // 2, HEIGHT // 2
gap = 180
btn_radius = 90
# order: top-left (red), top-right (blue), bottom-left (green), bottom-right (yellow)
btn_positions = [
    (center_x - gap, center_y - gap),  # red (0)
    (center_x + gap, center_y - gap),  # blue (1)
    (center_x - gap, center_y + gap),  # green (2)
    (center_x + gap, center_y + gap)   # yellow (3)
]
btn_keys = ['red', 'blue', 'green', 'yellow']

DIFFICULTY = {
    'easy':   {'start_len': 1, 'per_color_time': 10.0},
    'normal': {'start_len': 2, 'per_color_time': 7.0},
    'hard':   {'start_len': 3, 'per_color_time': 5.0}
}

MAX_ROUNDS = 10

# ----------------------------
# UTILIDADES GRAFICAS | DIBUJO
# ----------------------------
def draw_gradient_bg(frame, t=0.0):
    """Fondo con gradiente vertical dinámico (seguro contra overflow)."""
    h, w = frame.shape[:2]
    for i in range(h):
        ratio = i / h
        r = int(30 + 80 * math.sin(t*0.6 + ratio * 3.0))
        g = int(40 + 140 * ratio)
        b = int(100 + 60 * (1 - ratio))
        r, g, b = np.clip([r, g, b], 0, 255)
        frame[i, :] = (b, g, r)

def draw_button(frame, idx, lit=False):
    x, y = btn_positions[idx]
    name = btn_keys[idx]
    color = color_map[name]
    cv2.circle(frame, (x, y), btn_radius, color, -1)
    cv2.circle(frame, (x, y), btn_radius, (0,0,0), 4)
    if lit:
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), btn_radius + 26, (255,255,255), 18)
        frame[:] = cv2.addWeighted(overlay, 0.22, frame, 0.78, 0)
        overlay2 = frame.copy()
        cv2.circle(overlay2, (x, y), btn_radius - 6, (255,255,255), -1)
        frame[:] = cv2.addWeighted(overlay2, 0.06, frame, 0.94, 0)

def draw_pulse(frame, pulse):
    age = time.time() - pulse['created']
    prog = age / pulse['ttl'] if pulse['ttl'] > 0 else 1.0
    if prog >= 1.0:
        return False
    x, y = btn_positions[pulse['lane']]
    big = pulse.get('big', False)
    if big:
        radius = int(btn_radius * 1.2 + 90 * prog)
        alpha = max(0.0, 0.55 * (1.0 - prog))
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), radius, pulse['color'], -1)
        frame[:] = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        ring_radius = int(radius * 1.02)
        overlay2 = frame.copy()
        cv2.circle(overlay2, (x, y), ring_radius, pulse['color'], max(6, int(16*(1-prog))))
        frame[:] = cv2.addWeighted(overlay2, 0.12 * (1-prog), frame, 1 - 0.12 * (1-prog), 0)
    else:
        radius = int(btn_radius + 8 + 40 * prog)
        alpha = max(0.0, 0.25 * (1.0 - prog))
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), radius, pulse['color'], 6)
        frame[:] = cv2.addWeighted(overlay, alpha + 0.05, frame, 1 - (alpha + 0.05), 0)
    return True

def draw_text_center(frame, text, y, scale=1.0, color=(255,255,255), thick=2):
    ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)[0]
    x = (frame.shape[1] - ts[0]) // 2
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)

# ----------------------------
# DETECCIÓN DE COLOR 
# ----------------------------
def detect_color_from_frame(frame):
    """Devuelve 'red'/'green'/'blue'/'yellow' o None."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for name, (low, high) in color_ranges.items():
        low_np = np.array(low, dtype=np.uint8)
        high_np = np.array(high, dtype=np.uint8)
        mask = cv2.inRange(hsv, low_np, high_np)
        mask = cv2.GaussianBlur(mask, (7,7), 0)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)
        if cv2.countNonZero(mask) > 3000:
            return name
    return None

def color_to_lane(colname):
    """Mapea nombre de color a índice de boton (lane)."""
    if colname == 'red': return 0
    if colname == 'blue': return 1
    if colname == 'green': return 2
    if colname == 'yellow': return 3
    return None

# ----------------------------
# LÓGICA DEL JUEGO
# ----------------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("Cam Preview", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Cam Preview", 640, 480)

state = 'menu'
difficulty = None
modo_infinito = False

sequence = []       # secuencia colores
round_idx = 0       # rondas completadas
expected_idx = 0    # color esperado
pulses = []         # efectos
last_input_time = 0
last_input_lane = None
input_released = True 
player_turn_start = 0
per_color_time = 7.0
start_len = 1
start_time_play = None
target_rounds = MAX_ROUNDS

def append_random_color():
    sequence.append(random.randrange(0,4))

seq_show_index = 0
seq_last_change = 0
seq_phase = 'idle'

round_pause_start = 0.0
round_pause_stage = 0  
ROUND_MSG_TIME = 0.9
LISTOS_TIME = 0.7

end_reason = ''
end_rounds = 0
end_time_played = 0.0

# ----------------------------
# LOOP PRINCIPAL
# ----------------------------
while True:
    t0 = time.time()
    ret, cam = cap.read()
    if not ret:
        break
    cam = cv2.flip(cam, 1)

    detected_color = detect_color_from_frame(cam)
    detected_lane = color_to_lane(detected_color) if detected_color else None

    cam_preview = cam.copy()
    bx, by = 12, 30
    txt = f"Detectado: {detected_color.upper()}" if detected_color else "Detectado: NINGUNO"
    text_color = color_map[detected_color] if detected_color else (255,255,255)
    cv2.putText(cam_preview, txt, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2, cv2.LINE_AA)

    cv2.imshow("Cam Preview", cam_preview)

    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    draw_gradient_bg(frame, t=time.time())

    # -----------------------
    # MENU
    # -----------------------
    if state == 'menu':
        draw_text_center(frame, "SIMON DICE (OpenCV)", 100, 1.4, (255,255,255), 3)
        # colores por modo
        draw_text_center(frame, "[F] Facil (1 color inicio, 10s/por color)", 220, 0.8, (180,255,200), 2)   # verde claro
        draw_text_center(frame, "[N] Normal (2 colores inicio, 7s/por color)", 270, 0.8, (255,255,160), 2)  # amarillo pálido
        draw_text_center(frame, "[D] Dificil (3 colores inicio, 5s/por color)", 320, 0.8, (255,180,180), 2)  # rojo suave
        draw_text_center(frame, "[ESPACIO] Alternar Modo Infinito: " + ("ON" if modo_infinito else "OFF"), 380, 0.8, (200,200,255) if modo_infinito else (200,120,120), 2)
        draw_text_center(frame, "Pulsa la tecla correspondiente para empezar", 450, 0.7, (230,230,230), 1)

        cv2.imshow("Simon Dice", frame)
        k = cv2.waitKey(int(1000/FPS)) & 0xFF
        if k == ord(' '):
            modo_infinito = not modo_infinito
        elif k == ord('f'):
            difficulty = 'easy'
        elif k == ord('n'):
            difficulty = 'normal'
        elif k == ord('d'):
            difficulty = 'hard'
        elif k == 27 or k == ord('q'):
            break

        if difficulty:
            start_len = DIFFICULTY[difficulty]['start_len']
            per_color_time = DIFFICULTY[difficulty]['per_color_time']
            sequence = []
            for _ in range(start_len):
                append_random_color()
            round_idx = 1
            expected_idx = 0
            seq_show_index = 0
            seq_phase = 'idle'
            seq_last_change = time.time()
            round_pause_start = time.time()
            round_pause_stage = 1
            state = 'round_pause'
            start_time_play = time.time()
            notes_shown = 0
            target_rounds = None if modo_infinito else MAX_ROUNDS
            continue

    # -----------------------
    # ROUND PAUSE
    # -----------------------
    if state == 'round_pause':
        for i in range(4):
            draw_button(frame, i, lit=False)
        nowt = time.time()
        stage_time = nowt - round_pause_start
        if round_pause_stage == 1:
            draw_text_center(frame, f"Ronda {round_idx}", HEIGHT//2 - 20, 2.0, (255,255,255), 4)
            if stage_time >= ROUND_MSG_TIME:
                round_pause_stage = 2
                round_pause_start = time.time()
        elif round_pause_stage == 2:
            draw_text_center(frame, "Listos?", HEIGHT//2 - 20, 1.8, (230,230,230), 3)
            if stage_time >= LISTOS_TIME:
                round_pause_stage = 0
                seq_show_index = 0
                seq_phase = 'off'
                seq_last_change = time.time() - 0.35
                state = 'show_sequence'
        pulses = [p for p in pulses if draw_pulse(frame, p)]
        draw_text_center(frame, f"Ronda {round_idx}" + ("" if target_rounds is None else f"/{target_rounds}"), 50, 0.9)
        cv2.imshow("Simon Dice", frame)
        k = cv2.waitKey(int(1000/FPS)) & 0xFF
        if k == 27 or k == ord('q'):
            break
        continue

    # -----------------------
    # SHOW SEQUENCE
    # -----------------------
    if state == 'show_sequence':
        for i in range(4):
            lit = (seq_phase == 'on' and seq_show_index < len(sequence) and sequence[seq_show_index] == i)
            draw_button(frame, i, lit=lit)
        pulses = [p for p in pulses if draw_pulse(frame, p)]
        draw_text_center(frame, f"Ronda {round_idx}" + ("" if target_rounds is None else f"/{target_rounds}"), 50, 0.9)
        draw_text_center(frame, "Muestra la secuencia...", 100, 0.8)
        elapsed_total = time.time() - start_time_play if start_time_play else 0.0
        mm = int(elapsed_total // 60); ss = int(elapsed_total % 60)
        cv2.putText(frame, f"Tiempo: {mm:02d}:{ss:02d}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230,230,230), 2)

        tnow = time.time()
        on_duration = 0.8
        off_duration = 0.35
        if seq_phase == 'off' and (tnow - seq_last_change) >= off_duration:
            if seq_show_index < len(sequence):
                seq_phase = 'on'
                seq_last_change = tnow
                pulses.append({'lane': sequence[seq_show_index], 'created': tnow, 'ttl': on_duration, 'color': pulse_seq, 'big': True})
            else:
                seq_show_index = 0
                seq_phase = 'idle'
                expected_idx = 0
                player_turn_start = time.time()
                state = 'player_turn'
                input_released = True
        elif seq_phase == 'on' and (tnow - seq_last_change) >= on_duration:
            seq_phase = 'off'
            seq_last_change = tnow
            seq_show_index += 1

        cv2.imshow("Simon Dice", frame)
        k = cv2.waitKey(int(1000/FPS)) & 0xFF
        if k == 27 or k == ord('q'):
            break
        continue

    # -----------------------
    # PLAYER TURN
    # -----------------------
    if state == 'player_turn':
        for i in range(4):
            draw_button(frame, i, lit=False)
        pulses = [p for p in pulses if draw_pulse(frame, p)]

        draw_text_center(frame, f"Ronda {round_idx}" + ("" if target_rounds is None else f"/{target_rounds}"), 50, 0.9)
        draw_text_center(frame, f"Repite la secuencia (te quedan {len(sequence) - expected_idx} colores)", 100, 0.7)
        elapsed_total = time.time() - start_time_play if start_time_play else 0.0
        mm = int(elapsed_total // 60); ss = int(elapsed_total % 60)
        cv2.putText(frame, f"Tiempo: {mm:02d}:{ss:02d}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230,230,230), 2)

        if expected_idx < len(sequence):
            time_allowed = per_color_time
            time_left = time_allowed - (time.time() - player_turn_start)
            if time_left < 0:
                pulses.append({'lane': sequence[expected_idx], 'created': time.time(), 'ttl': 1.0, 'color': pulse_fail, 'big': True})
                end_reason = 'Tiempo agotado'
                end_rounds = round_idx - 1
                end_time_played = time.time() - start_time_play if start_time_play else 0.0
                state = 'end'
                continue
            bar_w = 300
            bx = WIDTH - bar_w - 20
            by = 40
            cv2.rectangle(frame, (bx, by), (bx+bar_w, by+18), (40,40,40), -1)
            fill = int(bar_w * (time_left / time_allowed))
            cv2.rectangle(frame, (bx, by), (bx+fill, by+18), (50,200,50), -1)
            cv2.putText(frame, f"{int(time_left)}s", (bx+bar_w+6, by+15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230,230,230), 2)

        input_lane = None
        k = cv2.waitKey(int(1000/FPS)) & 0xFF
        if k != 255:
            if k == ord('1') or k == ord('r'):
                input_lane = 0
            elif k == ord('2') or k == ord('b'):
                input_lane = 1
            elif k == ord('3') or k == ord('g'):
                input_lane = 2
            elif k == ord('4') or k == ord('y'):
                input_lane = 3
            elif k == 27 or k == ord('q'):
                break
        if input_lane is None and detected_lane is not None:
            if input_released or detected_lane != last_input_lane:
                input_lane = detected_lane
                input_released = False
        if detected_lane is None:
            input_released = True
            last_input_lane = None
        else:
            last_input_lane = detected_lane

        if input_lane is not None:
            if expected_idx >= len(sequence):
                continue
            correct_lane = sequence[expected_idx]
            if input_lane == correct_lane:
                pulses.append({'lane': input_lane, 'created': time.time(), 'ttl': 0.9, 'color': pulse_ok, 'big': True})
                expected_idx += 1
                player_turn_start = time.time()
                if expected_idx >= len(sequence):
                    for i in range(4):
                        pulses.append({'lane': i, 'created': time.time(), 'ttl': 0.9, 'color': (80,180,80), 'big': True})
                    if (not modo_infinito) and round_idx >= MAX_ROUNDS:
                        end_reason = 'Victoria'
                        end_rounds = round_idx
                        end_time_played = time.time() - start_time_play if start_time_play else 0.0
                        state = 'end'
                        continue
                    round_idx += 1
                    append_random_color()
                    round_pause_start = time.time()
                    round_pause_stage = 1
                    state = 'round_pause'
                    continue
            else:
                pulses.append({'lane': input_lane, 'created': time.time(), 'ttl': 1.1, 'color': pulse_fail, 'big': True})
                end_reason = 'Color incorrecto'
                end_rounds = round_idx - 1
                end_time_played = time.time() - start_time_play if start_time_play else 0.0
                state = 'end'
                continue

        cv2.imshow("Simon Dice", frame)
        continue

    # -----------------------
    # END (victoria/derrota)
    # -----------------------
    if state == 'end':
        for i in range(HEIGHT):
            ratio = i / HEIGHT
            if end_reason == 'Victoria':
                r = int(60 + 120*ratio); g = int(160 + 50*ratio); b = int(80 + 30*(1-ratio))
            else:
                r = int(150 + 80*ratio); g = int(40 + 30*(1-ratio)); b = int(90 + 60*ratio)
            r,g,b = np.clip([r,g,b],0,255)
            frame[i, :] = (b,g,r)
        draw_text_center(frame, end_reason, HEIGHT//3, 2.0, (255,255,255), 4)
        draw_text_center(frame, f"Rondas completadas: {end_rounds}", HEIGHT//2 + 10, 0.9)
        mins = int(end_time_played // 60); secs = int(end_time_played % 60)
        draw_text_center(frame, f"Tiempo jugado: {mins:02d}:{secs:02d}", HEIGHT//2 + 60, 0.9)
        draw_text_center(frame, "Pulsa [R] para volver al menu o [Q]/ESC para salir", HEIGHT - 80, 0.7)
        cv2.imshow("Simon Dice", frame)
        k = cv2.waitKey(0) & 0xFF
        if k == ord('r'):
            state = 'menu'
            difficulty = None
            modo_infinito = False
            sequence = []
            round_idx = 0
            expected_idx = 0
            seq_show_index = 0
            seq_phase = 'idle'
            start_time_play = None
            continue
        elif k == 27 or k == ord('q'):
            break
        else:
            continue

    cv2.imshow("Simon Dice", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
