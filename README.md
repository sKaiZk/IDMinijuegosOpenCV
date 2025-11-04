# 🎮 MiniJuegos OpenCV — *IDanceFloor · SimonDicv · Tetris*

Bienvenido/a a **MiniJuegos OpenCV**, un conjunto de tres juegos clásicos reinventados con **visión por computadora** usando la cámara web y la librería **OpenCV**.  
El proyecto incluye un menú interactivo que permite elegir entre **Dance Floor**, **Simon Dice** y **Tetris**, todo controlado mediante detección de colores.

---

## 🧩 Índice

1. [🎬 Vista general](#-vista-general)  
2. [🕹️ Menú principal](#️-menú-principal)  
3. [💃 Dance Floor](#-dance-floor)  
4. [🧠 Simon Dice](#-simon-dice)  
5. [🧱 Tetris](#-tetris)  
6. [⚙️ Tecnologías utilizadas](#️-tecnologías-utilizadas)  
7. [🚀 Ejecución del proyecto](#-ejecución-del-proyecto)  
8. [📂 Estructura del repositorio](#-estructura-del-repositorio)  
9. [🧠 Autor y créditos](#-autor-y-créditos)

---

## 🎬 Vista general

Este proyecto combina **juegos interactivos** con **visión artificial**, permitiendo controlar los minijuegos moviendo objetos de colores frente a la cámara.  
Cada juego incluye su propio sistema de dificultad, detección de colores, puntuaciones y animaciones visuales, junto con pantallas de **inicio**, **victoria** y **derrota**.

---

## 🕹️ Menú principal

El menú es la puerta de entrada a los tres minijuegos.  
Permite seleccionar el juego con un clic o con el ratón, mostrando un **fondo degradado dinámico** y botones que cambian de color al pasar el cursor.

**Características:**
- Interfaz visual limpia en OpenCV.  
- Botones interactivos con detección del ratón.  
- Fondo animado con gradiente dinámico.  
- Opciones:  
  - 🎵 *Dance Floor*  
  - 🧠 *Simon Dice*  
  - 🧱 *Tetris*  
  - ❌ *Salir*  

---

## 💃 Dance Floor 

Un juego rítmico donde debes **moverte según el color objetivo** antes de que se acabe el tiempo.

**🎨 Controles por color:**
| Color Detectado | Movimiento / Acción |
|-----------------|---------------------|
| 🔴 Rojo         | Mover derecha       |
| 🟢 Verde        | Mover izquierda     |
| 🔵 Azul         | Mover arriba        |
| 🟡 Amarillo     | Mover abajo         |

**🧠 Mecánica:**
- El tablero se llena de celdas de colores aleatorios.
- El jugador (un círculo blanco) debe llegar al color objetivo antes de que acabe la ronda.
- El tiempo depende de la **dificultad** seleccionada (Fácil, Normal o Difícil).
- Incluye un **modo infinito**, donde las rondas no terminan hasta fallar.

**🎉 Pantallas y efectos:**
- Fondos animados según victoria o derrota.
- Contador de tiempo restante.
- Detección visual del color activo en la cámara.

---

## 🧠 Simon Dice

El clásico juego de memoria, pero controlado con **detección de color**.

**🎮 Mecánica:**
- Se muestran secuencias de colores (rojo, verde, azul, amarillo).
- El jugador debe repetirlas moviendo el color correcto frente a la cámara.
- Cada ronda añade un nuevo color a la secuencia.

**⚙️ Dificultades:**
| Dificultad | Secuencia inicial | Tiempo por color |
|-------------|------------------|------------------|
| 🟢 Fácil     | 1 color           | 10 segundos       |
| 🟡 Normal    | 2 colores         | 7 segundos        |
| 🔴 Difícil   | 3 colores         | 5 segundos        |

**✨ Detalles visuales:**
- Cuatro círculos centrales con animaciones de pulsación.  
- Verde si aciertas, rojo si fallas.  
- Fondos diferenciados para victoria, derrota y modo infinito.  

---

## 🧱 Tetris

Una versión del **Tetris clásico** totalmente jugable con la cámara 🎥  
Las piezas caen, puedes moverlas o girarlas usando **colores detectados**.

**🎨 Controles por color:**
| Color Detectado | Acción |
|-----------------|---------|
| 🔴 Rojo         | Mover a la derecha |
| 🟢 Verde        | Mover a la izquierda |
| 🟡 Amarillo     | Rotar la pieza |
| 🔵 Azul         | Cambiar pieza (swap) |

**🎯 Objetivo:**
- Completar líneas horizontales (8x16 celdas).
- Al completar una, desaparece y el resto baja.
- Ganas puntos por cada bloque colocado y por cada línea completada (+100 puntos por línea).

**📊 HUD:**
- Puntuación total.  
- Tiempo de partida.  
- Próxima pieza visible.  
- Caja lateral con la pieza guardada (swap).  

---

## ⚙️ Tecnologías utilizadas

**🧠 OpenCV (cv2)**  
- Detección de color en espacio HSV (`cv2.inRange`)  
- Control de cámara en tiempo real (`cv2.VideoCapture`)  
- Renderizado de interfaces con figuras (`cv2.rectangle`, `cv2.circle`, `cv2.putText`)  
- Efectos visuales (gradientes, pulsaciones, partículas)  
- Ventanas interactivas (`cv2.setMouseCallback`, `cv2.imshow`)

**🐍 Python estándar**  
- `time` para controlar rondas, animaciones y duración.  
- `random` para la generación de colores y piezas.  
- `os` y `subprocess` para ejecutar los minijuegos desde el menú.  
- `numpy` para el manejo de matrices (tableros, fondos y animaciones).

---

## 🚀 Ejecución del proyecto

### 🔧 Requisitos previos
Asegúrate de tener instalados:
```bash
pip install opencv-python numpy
```
### ▶️ Iniciar el menú principal
```bash
python IDMenu.py
```

---

## 📂 Estructura del repositorio

La siguiente estructura muestra cómo se organizan los archivos del proyecto de minijuegos creados con **OpenCV**.  
Cada juego puede ejecutarse de forma independiente o desde el menú principal:

### 📦 MiniJuegos_OpenCV

 ┣ 📜 IDMenu.py           → Menú de selección de juegos
 
 ┣ 🎮 IDanceFloor.py       → IDanceFloor
 
 ┣ 🧠 Simondicv.py          → SimonDicv
 
 ┣ 🧱 IDTetris.py           → IDTetris
 
 ┗ 📄 README.md              → Este archivo

---

## 🧠 **Autor y créditos**

👨‍💻 **Desarrollado por:** *Samuel Monasterio Pérez*  
🎯 **Propósito:** Proyecto educativo y experimental para explorar las capacidades de **OpenCV** en el desarrollo de minijuegos interactivos.  
💡 **Inspiración:** Basado en la estética de los juegos retro y el reconocimiento por color como medio de control alternativo.  
🛠️ **Tecnologías:** `Python`, `OpenCV`, `NumPy`

---
