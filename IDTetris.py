import cv2
import numpy as np
import random
import time
import math

# ----------------------
# CONFIGURACIÓN Tetris 
# ----------------------
COLS, ROWS = 8, 16           # ancho x alto en celdas
CELL = 44                    # tamaño de celda en píxeles 
SIDE_PANEL = 360             # ancho del panel lateral 
WIDTH = COLS * CELL + SIDE_PANEL
HEIGHT = ROWS * CELL + 40
FPS = 30

GRAVITY_INTERVAL = 0.7       # segundos entre caídas
FAST_DROP_INTERVAL = 0.05
BASE_PARTICLE_COUNT = 90     # partículas/fondo

color_ranges = {
    "red":    [(0, 100, 80), (10, 255, 255)],
    "green":  [(40, 60, 60), (80, 255, 255)],
    "blue":   [(95, 60, 40), (130, 255, 255)],
    "yellow": [(18, 90, 90), (35, 255, 255)]
}

PIECE_COLORS = {
    'I': (180, 240, 240),  # cyan
    'O': (0, 240, 255),    # yellow
    'T': (200, 0, 200),    # magenta
    'S': (0, 220, 0),      # green
    'Z': (0, 0, 220),      # red
    'J': (220, 120, 0),    # blue
    'L': (0, 140, 220)     # orange
}

CAM_ACTION = {
    'red': 'right',
    'green': 'left',
    'yellow': 'rotate',
    'blue': 'swap'
}

# ----------------------
# PIEZAS 
# ----------------------
PIECES = {
    'I': [
        [(0,2),(1,2),(2,2),(3,2)],
        [(2,0),(2,1),(2,2),(2,3)],
    ],
    'O': [
        [(1,1),(2,1),(1,2),(2,2)],
    ],
    'T': [
        [(1,1),(0,2),(1,2),(2,2)],
        [(1,1),(1,2),(2,1),(1,0)],
        [(0,1),(1,1),(2,1),(1,2)],
        [(1,1),(0,1),(1,0),(1,2)],
    ],
    'S': [
        [(1,2),(2,2),(0,1),(1,1)],
        [(2,0),(2,1),(1,1),(1,2)],
    ],
    'Z': [
        [(0,2),(1,2),(1,1),(2,1)],
        [(1,0),(1,1),(2,1),(2,2)],
    ],
    'J': [
        [(0,1),(0,2),(1,2),(2,2)],
        [(1,0),(2,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(0,2),(1,2)],
    ],
    'L': [
        [(2,1),(0,2),(1,2),(2,2)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,1),(0,2)],
        [(0,0),(1,0),(1,1),(1,2)],
    ],
}

# Rotaciones normalizadas, 4 por pieza
def normalized_rotations(shape):
    rots = PIECES[shape]
    if len(rots) == 1:
        return rots * 4
    if len(rots) == 2:
        return [rots[0], rots[1], rots[0], rots[1]]
    if len(rots) == 4:
        return rots
    return rots * (4 // len(rots)) + rots[:(4 % len(rots))]

for k in list(PIECES.keys()):
    PIECES[k] = normalized_rotations(k)

# ----------------------
# UTILIDADES
# ----------------------
def create_particles(count):
    plist = []
    for _ in range(count):
        plist.append({
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(0, HEIGHT),
            "r": random.uniform(1.5, 5.0),
            "vx": random.uniform(-0.6, 0.6),
            "vy": random.uniform(-0.4, 0.4),
            "c": (random.randint(120,255), random.randint(120,255), random.randint(120,255))
        })
    return plist

def draw_particles(frame, plist):
    overlay = frame.copy()
    h,w = frame.shape[:2]
    for p in plist:
        p['x'] += p['vx']
        p['y'] += p['vy']
        if p['x'] < 0: p['x'] = w
        if p['x'] > w: p['x'] = 0
        if p['y'] < 0: p['y'] = h
        if p['y'] > h: p['y'] = 0
        cv2.circle(overlay, (int(p['x']), int(p['y'])), int(p['r']), p['c'], -1)
    frame[...] = cv2.addWeighted(overlay, 0.10, frame, 0.90, 0)

def draw_gradient_bg(frame, t=0.0):
    h, w = frame.shape[:2]
    for i in range(h):
        ratio = i / max(h-1,1)
        r = int(30 + 80 * math.sin(t*0.5 + ratio * 3.0))
        g = int(40 + 140 * ratio)
        b = int(100 + 60 * (1 - ratio))
        r,g,b = np.clip([r,g,b], 0, 255)
        frame[i, :] = (b, g, r)

def detect_color_from_frame(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for name, (low, high) in color_ranges.items():
        low_np = np.array(low, dtype=np.uint8)
        high_np = np.array(high, dtype=np.uint8)
        mask = cv2.inRange(hsv, low_np, high_np)
        mask = cv2.GaussianBlur(mask, (7,7), 0)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)
        if cv2.countNonZero(mask) > 4000:
            return name
    return None

def draw_text(img, text, x, y, size=0.7, color=(230,230,230), thick=2, bg=None):
    if bg:
        b,g,r,a = bg
        ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, size, thick)[0]
        pad = 8
        x2, y2 = x + ts[0] + pad, y - ts[1] - pad//2
        overlay = img.copy()
        cv2.rectangle(overlay, (x-4, y-24), (x2, y+6), (b,g,r), -1)
        img[...] = cv2.addWeighted(overlay, a, img, 1-a, 0)
    cv2.putText(img, text, (x,y), cv2.FONT_HERSHEY_SIMPLEX, size, color, thick, cv2.LINE_AA)

# ----------------------
# LÓGICA PIEZAS | TABLERO
# ----------------------
def create_empty_grid():
    return [[None for _ in range(COLS)] for _ in range(ROWS)]

class Piece:
    def __init__(self, shape):
        self.shape = shape
        self.rots = PIECES[shape]
        self.rot = 0
        self.x = (COLS // 2) - 2
        self.y = -1
        self.color = PIECE_COLORS[shape]
    def cells(self, rot=None, x_off=None, y_off=None):
        r = self.rots[self.rot if rot is None else rot]
        x0 = self.x if x_off is None else x_off
        y0 = self.y if y_off is None else y_off
        return [(x0 + cx, y0 + cy) for (cx,cy) in r]
    def rotate(self):
        return (self.rot + 1) % len(self.rots)
    def set_rotation(self, r):
        self.rot = r % len(self.rots)

def valid_position(grid, piece, rot=None, x_off=None, y_off=None):
    for (x,y) in piece.cells(rot=rot, x_off=x_off, y_off=y_off):
        if x < 0 or x >= COLS:
            return False
        if y >= ROWS:
            return False
        if y >= 0 and grid[y][x] is not None:
            return False
    return True

def lock_piece(grid, piece):
    count_blocks = 0
    for (x,y) in piece.cells():
        if y >= 0:
            grid[y][x] = piece.color
            count_blocks += 1
    lines_cleared = 0
    y = ROWS - 1
    while y >= 0:
        if all(grid[y][x] is not None for x in range(COLS)):
            del grid[y]
            grid.insert(0, [None for _ in range(COLS)])
            lines_cleared += 1
        else:
            y -= 1
    return count_blocks, lines_cleared

def random_piece():
    shape = random.choice(list(PIECES.keys()))
    return Piece(shape)

def get_ghost_y(grid, piece):
    y = piece.y
    while valid_position(grid, piece, x_off=piece.x, y_off=y+1):
        y += 1
    return y

# ----------------------
# DIBUJO tablero y panel
# ----------------------
def draw_board(frame, grid, current_piece=None):
    board_x = 20
    board_y = 20
    cv2.rectangle(frame, (board_x-6, board_y-6), (board_x + COLS*CELL +6, board_y + ROWS*CELL +6), (40,40,40), -1)
    for r in range(ROWS):
        for c in range(COLS):
            x = board_x + c*CELL
            y = board_y + r*CELL
            cell = grid[r][c]
            if cell is not None:
                cv2.rectangle(frame, (x+1,y+1), (x+CELL-1, y+CELL-1), cell, -1)
                cv2.rectangle(frame, (x+1,y+1), (x+CELL-1, y+CELL-1), (20,20,20), 2)
            else:
                cv2.rectangle(frame, (x,y), (x+CELL, y+CELL), (28,28,28), 1)
    if current_piece is not None:
        gy = get_ghost_y(grid, current_piece)
        for (xcell,ycell) in current_piece.cells(y_off=gy):
            if ycell >= 0:
                x = board_x + xcell*CELL
                y = board_y + ycell*CELL
                cv2.rectangle(frame,(x+3,y+3),(x+CELL-3,y+CELL-3),
                              tuple(int(c*0.4) for c in current_piece.color),1)
        for (xcell, ycell) in current_piece.cells():
            if ycell < 0:
                continue
            x = board_x + xcell*CELL
            y = board_y + ycell*CELL
            cv2.rectangle(frame, (x+1,y+1), (x+CELL-1, y+CELL-1), current_piece.color, -1)
            cv2.rectangle(frame, (x+1,y+1), (x+CELL-1, y+CELL-1), (10,10,10), 2)
    cv2.rectangle(frame, (board_x-6, board_y-6), (board_x + COLS*CELL +6, board_y + ROWS*CELL +6), (200,200,200), 2)

def draw_piece_preview(frame, piece, pos_x, pos_y, title="Next"):
    box_w = 4 * CELL // 2
    box_h = 4 * CELL // 2
    cv2.rectangle(frame, (pos_x, pos_y), (pos_x + box_w + 8, pos_y + box_h + 8), (40,40,40), -1)
    draw_text(frame, title, pos_x+8, pos_y+20, 0.65, (220,220,220))
    if piece is None:
        draw_text(frame, "(vacio)", pos_x+8, pos_y+box_h//2 + 12, 0.6, (190,190,190))
        return
    scale = 0.5
    ox = pos_x + 8 + (box_w // 2) - int(2 * CELL * scale)
    oy = pos_y + 30
    for (cx,cy) in piece.rots[piece.rot]:
        px = ox + int(cx * CELL * scale)
        py = oy + int(cy * CELL * scale)
        w = int(CELL*scale) - 2
        cv2.rectangle(frame, (px,py), (px+w, py+w), piece.color, -1)
        cv2.rectangle(frame, (px,py), (px+w, py+w), (10,10,10), 1)

# ----------------------
# BUCLE PRINCIPAL
# ----------------------
def run_tetris():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    cv2.namedWindow("Cam Preview", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Cam Preview", 560, 420)

    particles = create_particles(BASE_PARTICLE_COUNT)

    grid = create_empty_grid()
    current = random_piece()
    next_piece = random_piece()
    hold_piece = None
    swap_used = False
    score = 0
    start_time = time.time()
    last_drop = time.time()
    game_over = False
    game_over_time = None

    last_detected = None
    input_released = True

    while True:
        tnow = time.time()
        ret, cam = cap.read()
        if not ret:
            break
        cam = cv2.flip(cam, 1)
        detected_color = detect_color_from_frame(cam)

        draw_gradient_bg_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        draw_gradient_bg(draw_gradient_bg_frame, t=tnow)

        cam_preview = cam.copy()
        bx,by = 10,10
        bw,bh = 300,48
        if detected_color:
            txt = f"Detectado: {detected_color.upper()}"
            fill = {
                'red': (0,0,200),
                'green': (0,200,0),
                'blue': (200,0,0),
                'yellow': (0,200,200)
            }.get(detected_color, (120,120,120))
        else:
            txt = "Detectado: NINGUNO"
            fill = (100,100,100)
        cv2.rectangle(cam_preview, (bx,by), (bx+bw, by+bh), fill, -1)
        cv2.rectangle(cam_preview, (bx,by), (bx+bw, by+bh), (30,30,30), 2)
        cv2.putText(cam_preview, txt, (bx+12, by+32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
        cv2.imshow("Cam Preview", cam_preview)

        frame = draw_gradient_bg_frame
        draw_particles(frame, particles)

        action = None
        if detected_color:
            mapped = CAM_ACTION.get(detected_color)
            if mapped:
                if input_released or detected_color != last_detected:
                    action = mapped
                    input_released = False
                    last_detected = detected_color
        else:
            input_released = True
            last_detected = None

        k = cv2.waitKey(1) & 0xFF
        if k != 255:
            if k == ord('q') or k == 27:
                break
            if k == ord('r') and game_over:
                grid = create_empty_grid()
                current = random_piece()
                next_piece = random_piece()
                hold_piece = None
                swap_used = False
                score = 0
                start_time = time.time()
                last_drop = time.time()
                game_over = False
            if k == ord('p'):
                cv2.putText(frame, "PAUSA - pulsa cualquier tecla", (50, HEIGHT//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
                cv2.imshow("TETRIS OpenCV", frame)
                cv2.waitKey(0)
            if k == ord('a') or k == 81:
                action = 'left'
            if k == ord('d') or k == 83:
                action = 'right'
            if k == ord('w') or k == 82:
                action = 'rotate'
            if k == ord('s') or k == 84:
                if not game_over:
                    if valid_position(grid, current, x_off=current.x, y_off=current.y+1):
                        current.y += 1
                    else:
                        blocks, lines = lock_piece(grid, current)
                        score += blocks
                        score += 100 * lines
                        current = next_piece
                        next_piece = random_piece()
                        swap_used = False
                        if not valid_position(grid, current, x_off=current.x, y_off=current.y):
                            game_over = True
                    last_drop = time.time()
            if k == ord(' '):
                action = 'swap'

        if action and not game_over:
            if action == 'left':
                if valid_position(grid, current, x_off=current.x-1, y_off=current.y):
                    current.x -= 1
            elif action == 'right':
                if valid_position(grid, current, x_off=current.x+1, y_off=current.y):
                    current.x += 1
            elif action == 'rotate':
                new_rot = current.rotate()
                if valid_position(grid, current, rot=new_rot, x_off=current.x, y_off=current.y):
                    current.set_rotation(new_rot)
                else:
                    if valid_position(grid, current, rot=new_rot, x_off=current.x-1, y_off=current.y):
                        current.x -= 1
                        current.set_rotation(new_rot)
                    elif valid_position(grid, current, rot=new_rot, x_off=current.x+1, y_off=current.y):
                        current.x += 1
                        current.set_rotation(new_rot)
            elif action == 'swap':
                if not swap_used:
                    if hold_piece is None:
                        hold_piece = Piece(current.shape)
                        current = next_piece
                        next_piece = random_piece()
                    else:
                        temp = hold_piece
                        hold_piece = Piece(current.shape)
                        current = Piece(temp.shape)
                    current.x = (COLS // 2) - 2
                    current.y = -1
                    current.set_rotation(0)
                    swap_used = True

        if not game_over:
            if (tnow - last_drop) >= GRAVITY_INTERVAL:
                if valid_position(grid, current, x_off=current.x, y_off=current.y+1):
                    current.y += 1
                else:
                    blocks, lines = lock_piece(grid, current)
                    score += blocks
                    score += 100 * lines
                    current = next_piece
                    next_piece = random_piece()
                    swap_used = False
                    if not valid_position(grid, current, x_off=current.x, y_off=current.y):
                        game_over = True
                        start_time = tnow - elapsed
                last_drop = tnow

        draw_board(frame, grid, current)
        panel_x = COLS*CELL + 36
        cv2.rectangle(frame, (panel_x-8, 18), (WIDTH-18, HEIGHT-18), (30,30,30), -1)
        cv2.rectangle(frame, (panel_x-8, 18), (WIDTH-18, HEIGHT-18), (70,70,70), 2)

        draw_text(frame, f"Score: {score}", panel_x+12, 60, 0.95, (245,245,245), 2, bg=(0,0,0,0.45))
        elapsed = int(tnow - start_time)
        draw_text(frame, f"Time: {elapsed}s", panel_x+12, 100, 0.85, (230,230,230), 2, bg=(0,0,0,0.35))
        draw_text(frame, "Next:", panel_x+12, 150, 0.8, (220,220,220), 2, bg=(0,0,0,0.28))
        draw_piece_preview(frame, next_piece, panel_x+12, 160, title="Queue")
        draw_text(frame, "Hold:", panel_x+12, 260, 0.8, (220,220,220), 2, bg=(0,0,0,0.28))
        if hold_piece:
            draw_piece_preview(frame, hold_piece, panel_x+12, 270, title="Stored")
        else:
            draw_text(frame, "(vacío)", panel_x+12, 320, 0.7, (190,190,190))
        draw_text(frame, "Controles por COLOR:", panel_x+12, 410, 0.7, (210,210,210))
        draw_text(frame, "Rojo  -> Derecha", panel_x+12, 450, 0.62, (0,0,180))
        draw_text(frame, "Verde -> Izquierda", panel_x+12, 475, 0.62, (0,160,0))
        draw_text(frame, "Amarillo -> Girar", panel_x+12, 500, 0.62, (0,160,160))
        draw_text(frame, "Azul -> Cambiar", panel_x+12, 525, 0.62, (160,0,0))
        draw_text(frame, "Teclado: W/A/S/D, SPACE", panel_x+12, 560, 0.55, (200,200,200))

        if game_over:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (WIDTH, HEIGHT), (5,5,5), -1)
            frame[...] = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
            draw_text(frame, "GAME OVER", WIDTH//3, HEIGHT//3, 1.8, (220,80,80), 4)
            draw_text(frame, f"Puntuacion: {score}", WIDTH//3, HEIGHT//3 + 80, 1.0, (240,240,240), 2)
            draw_text(frame, "Pulsa R para reiniciar o Q/ESC para salir", WIDTH//6, HEIGHT//3 + 140, 0.85, (220,220,220), 2)

        cv2.imshow("TETRIS OpenCV", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_tetris()
