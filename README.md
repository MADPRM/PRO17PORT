# PRO17PORT — Pro Evolution Soccer 2017 PC Native Port

<div align="center">
  <h3>Reimplementación Nativa de Pro Evolution Soccer 2017 para PC (x86-64 / Vulkan 1.3)</h3>
  <p>Rendimiento nativo, soporte para altas tasas de refresco, antialiasing TAA / AMD FSR y superposición en vivo de DataPacks.</p>
</div>

---

> [!IMPORTANT]
> **No se incluyen archivos ni datos comerciales del juego.** Este proyecto es únicamente el motor de compatibilidad y ejecución nativa en PC. Para jugar, debes proveer tu propia copia legal de **Pro Evolution Soccer 2017 (PS4 - CUSA04957)**.
> 
> *Pro Evolution Soccer, PES y KONAMI son marcas registradas de Konami Digital Entertainment Co., Ltd. Este proyecto no está afiliado, respaldado ni asociado con Konami ni con Sony Interactive Entertainment.*

---

## 🌟 Características Principales

* **Renderizado Nativo en Vulkan 1.3:** Motor de baja sobrecarga en GPU con búferes directos y sincronización optimizada para Windows 10 y 11.
* **Escalado Avanzado y Suavizado de Bordes (Antialiasing):**
  * **TAA (Temporal Anti-Aliasing):** Eliminación completa del aliasing en camisetas, mallas y público mediante acumulación temporal con *neighborhood clamping*.
  * **AMD FSR (FidelityFX Super Resolution):** Reconstrucción espacial con nitidez adaptativa RCAS (*Robust Contrast-Adaptive Sharpening*).
* **Filtro Anisotrópico (AF 2x – 16x):** Césped nítido a ángulos rasantes sin las líneas rojas ni artefactos de muestreo del juego original.
* **Estabilidad de Iluminación y Exposición:** Protección contra lectura desincronizada de texturas temporales en las cámaras de transmisión dinámica.
* **Soporte de Parche y DataPacks Separados (Sin Fusionar):**
  * Permite tener la carpeta del juego base (`CUSA04957`) y la de la actualización/parche (`CUSA04957-patch`) por separado.
  * El motor aplica una **superposición virtual en caliente**, cargando los DataPacks (CPK) y la versión v01.07 sin modificar ni sobrescribir los archivos del juego original.
* **Altas Tasas de Refresco (High Refresh Rate):**
  * Modos de 60 FPS (velocidad reglamentaria de simulación), 120 FPS, 144 FPS y sin límite con VSync.
* **Audio Envolvente y Guardado Directo:**
  * Mezcla multicanal Estéreo, 5.1 y 7.1 Surround.
  * Gestión de partidas guardadas (`Savedata`) en formato estándar accesible en Windows.
* **Launcher Moderno Incluido (`PES2017_Launcher.exe`):**
  * Interfaz gráfica intuitiva con detección automática de carpetas, ajuste de resolución (720p hasta 4K y Ultrawide 21:9), idioma, volumen y conmutador en vivo del parche.
  * Menú de ajustes en pleno partido con la tecla `Insert` o la combinación de mando `R3 + L2`.

---

## 🖥 Requisitos del Sistema

* **Sistema Operativo:** Windows 10 / Windows 11 (64-bit).
* **Procesador (CPU):** Procesador x86-64 con soporte **AVX y SSE4.2** (Intel Core 2ª Gen Sandy Bridge / AMD FX o AMD Ryzen superior). *(Nota: No requiere AVX2; la PS4 utiliza la arquitectura Jaguar con AVX 1.0).*
* **Software:** Python 3 instalado en Windows (para la interfaz visual del launcher).
* **Tarjeta Gráfica (GPU):** Compatible con **Vulkan 1.3**:
  * NVIDIA: GeForce GTX 900 / 1050 o superior.
  * AMD: Radeon RX 400 / Vega / RDNA o superior.
  * Intel: Intel Arc / Gráficos Iris Xe.
* **Memoria RAM:** 8 GB de RAM recomendados.
* **Archivos del Juego:** Copia legítima de **PES 2017** para PS4 (`CUSA04957`).

---

## 🚀 Inicio Rápido (Cómo Jugar)

1. **Descarga o clona el repositorio `PRO17PORT`.**
2. **Coloca tu carpeta del juego:**
   * Ubica la carpeta `CUSA04957` (que contiene `eboot.bin` y `sce_module/libc.prx`) junto al proyecto o en tu disco.
   * *(Opcional)* Si cuentas con la actualización o parche con DataPacks, coloca la carpeta `CUSA04957-patch` al lado.
3. **Ejecuta el Launcher:**
   * Abre `PES2017_Launcher.exe`.
   * El launcher detectará automáticamente la versión base y el parche de actualización.
   * Configura tu resolución deseada, filtro anisotrópico y antialiasing (TAA o FSR).
   * Haz clic en **▶ JUGAR PES 2017**.
4. **Controles durante el juego:**
   * `Insert` o `R3 + L2` (en el mando): Abre el menú flotante de ajustes gráficos y de sistema en vivo.
   * `F12`: Captura de pantalla en alta resolución (guardada en `out/user/screenshots`).

---

## 🛠 Compilación desde el Código Fuente

El proyecto utiliza el entorno nativo **MSYS2 Clang64** en Windows:

### 1. Preparar las dependencias (MSYS2 Clang64)
Abre la terminal `MSYS2 CLANG64` e instala las herramientas necesarias:
```bash
pacman -S --needed \
  mingw-w64-clang-x86_64-clang \
  mingw-w64-clang-x86_64-cmake \
  mingw-w64-clang-x86_64-ninja \
  mingw-w64-clang-x86_64-pkgconf \
  mingw-w64-clang-x86_64-vulkan-headers \
  mingw-w64-clang-x86_64-vulkan-loader \
  mingw-w64-clang-x86_64-sdl3 \
  mingw-w64-clang-x86_64-ffmpeg \
  mingw-w64-clang-x86_64-boost \
  mingw-w64-clang-x86_64-xxhash
```

### 2. Configurar y compilar con CMake & Ninja
```bash
# Configuración del motor gráfico Vulkan
cmake -S gpu -B out/gpu -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++

# Compilación del ejecutable nativo PES2017.exe
ninja -C out/gpu spartanport-probe
cp out/gpu/PES2017.exe out/
```

### 3. Compilar el Launcher nativo (`PES2017_Launcher.exe`)
```bash
windres scratch/launcher_win32.rc -O coff -o scratch/launcher_win32.res
clang -O2 -mwindows -municode scratch/launcher_win32.c scratch/launcher_win32.res -luser32 -o PES2017_Launcher.exe
```

---

## ⚖️ Licencia y Aviso Legal

Este proyecto de código abierto se distribuye bajo los términos de la licencia **GPLv2 o posterior**.

* Este software no contiene código propietario de Konami Digital Entertainment ni claves criptográficas de Sony.
* Todas las marcas, logotipos y nombres de productos comerciales pertenecen a sus respectivos dueños.
