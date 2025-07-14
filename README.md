# Generador de Códigos QR Avanzado

Este proyecto es una aplicación web Flask que permite a los usuarios generar códigos QR personalizados para una amplia variedad de tipos de contenido, con opciones de personalización visual.

## Características Principales

*   **Múltiples Tipos de Contenido:**
    *   URL
    *   Texto Plano
    *   Configuración WiFi (SSID, Contraseña, Seguridad, Red Oculta)
    *   vCard (Tarjeta de Contacto detallada)
    *   MeCard (Tarjeta de Contacto simplificada)
    *   Email (Destinatario, Asunto, Cuerpo)
    *   SMS (Número de Teléfono, Mensaje)
    *   Número de Teléfono
    *   Evento de Calendario (iCalendar)
    *   Geolocalización (Latitud, Longitud)
    *   Pagos EPC (European Payments Council Quick Response Code)
*   **Formatos de Salida:**
    *   PNG (default)
    *   SVG (Vectorial)
    *   TXT (Representación en arte ASCII)
*   **Personalización del QR:**
    *   **Colores:** Color de los módulos (oscuro) y color de fondo (claro).
    *   **Fondo Transparente:** Opción para PNG y SVG.
    *   **Nivel de Corrección de Errores (ECC):** L, M, Q, H.
    *   **Escala:** Tamaño de los módulos individuales del QR.
    *   **Borde:** Grosor del borde alrededor del QR.
*   **Interfaz Web Intuitiva:**
    *   Formulario dinámico que se adapta al tipo de contenido seleccionado.
    *   Previsualización del código QR (PNG o Texto).
    *   Validación de datos en el cliente y en el servidor.
*   **Backend en Python:**
    *   Utiliza Flask como framework web.
    *   Emplea la biblioteca `python-qrcode[pil]` para la generación de los códigos QR.

## Próximas Características (Plan de Refinamiento)

Actualmente, el siguiente paso en desarrollo es **Refinar la Interfaz de Usuario Web y Añadir Personalizaciones Avanzadas**, que incluye:

*   **Mejoras UX/UI:**
    *   Diseño visual más pulido y profesional.
    *   Previsualización de SVG renderizado directamente en la página.
*   **Personalizaciones Visuales Avanzadas:**
    *   **Formas de los Módulos:** Permitir elegir diferentes estilos para los "píxeles" del QR (cuadrados, redondeados, puntos, etc.) utilizando `module_drawers` de `python-qrcode`.
    *   **Incrustar Logo:** Funcionalidad para subir un logo y superponerlo en el centro del QR.
    *   **(Opcional)** Explorar máscaras de color (`color_masks`).
*   **Pruebas de Interfaz / Integración.**

## Tecnologías Utilizadas

*   **Backend:** Python, Flask, qrcode (`python-qrcode[pil]`)
*   **Frontend:** HTML, CSS, JavaScript (básico)

## Configuración y Ejecución

### Prerrequisitos

*   Python 3.8 o superior.
*   `pip` (manejador de paquetes de Python).

### Instalación de Dependencias

1.  Clona este repositorio (o descarga los archivos en un directorio).
2.  Navega al directorio del proyecto en tu terminal.
3.  Crea un entorno virtual (recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
4.  Instala las dependencias desde `requirements.txt` (se generará en el próximo paso):
    ```bash
    pip install -r requirements.txt
    ```

### Ejecución de la Aplicación

Una vez instaladas las dependencias, ejecuta la aplicación Flask:
```bash
python app.py
```
La aplicación estará disponible por defecto en `http://127.0.0.1:5000` o `http://0.0.0.0:5000` (si Flask está configurado para escuchar en todas las interfaces).

### Ejecución de Pruebas

Para ejecutar las pruebas unitarias de la lógica de generación de QR:
```bash
python -m unittest test_qr_generator_logic.py
```

## Estructura del Proyecto

```
.
├── app.py                     # Lógica de la aplicación Flask (rutas, validación)
├── qr_generator_logic.py      # Módulo para la generación de QR y formato de datos
├── test_qr_generator_logic.py # Pruebas unitarias para qr_generator_logic.py
├── templates/
│   └── index.html             # Plantilla HTML para la interfaz de usuario
├── static/                    # (Directorio para CSS/JS estáticos futuros)
│   └── (vacío por ahora)
├── README.md                  # Este archivo
└── requirements.txt           # (Se generará)
```

## Contribuidores

*   Jules (AI Agent)

## Posibles Mejoras Futuras (Post-Refinamiento)

*   Soporte para más formatos de salida (PDF, EPS mediante conversión).
*   Internacionalización (i18n) de la interfaz.
*   Guardar configuraciones de QR personalizadas por el usuario (requeriría base de datos o almacenamiento local).
*   API para generación de QR.
*   Despliegue en una plataforma (ej. Docker, Heroku, etc.).

## Running with Docker

To run this application with Docker, you can use the provided `Dockerfile` and `docker-compose.yml` files.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2)

### Instructions

1.  **Build and run the container:**

    ```bash
    docker compose up --build -d
    ```

    *Note: Depending on your Docker installation, you may need to run this command with `sudo`.*

2.  **Access the application:**

    Once the container is running, you can access the application in your web browser at:

    [http://localhost:8080](http://localhost:8080)

3.  **Stopping the application:**

    To stop the application, run:

    ```bash
    docker compose down
    ```
```
