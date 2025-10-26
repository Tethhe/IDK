# Editor de LaTeX con Electron y React

Este es un proyecto base para un editor de LaTeX de escritorio construido con Electron y React.

## Funcionalidades Mínimas

- Crear y abrir archivos `.tex`.
- Editor de código con resaltado de sintaxis para LaTeX.
- Compilación de `.tex` a PDF con un solo clic.
- Visor de PDF integrado.
- Panel para visualizar los logs de compilación y errores.

## Pre-requisitos

Antes de empezar, asegúrate de tener instalado lo siguiente en tu sistema:

1.  **Node.js y npm:** Puedes descargarlos desde [nodejs.org](https://nodejs.org/).
2.  **Una distribución de LaTeX:** El comando `pdflatex` debe estar disponible en la terminal de tu sistema. La forma más sencilla de obtenerlo es instalando:
    *   **Windows:** [MiKTeX](https://miktex.org/download)
    *   **macOS:** [MacTeX](https://www.tug.org/mactex/)
    *   **Linux:** `sudo apt-get install texlive-full` (o el paquete equivalente para tu distribución).

## Cómo Levantar la Aplicación

1.  **Clona o descarga este repositorio.**

2.  **Navega a la carpeta del proyecto:**
    ```bash
    cd latex-editor
    ```

3.  **Instala las dependencias del proyecto:**
    ```bash
    npm install
    ```

4.  **Ejecuta la aplicación en modo de desarrollo:**
    ```bash
    npm run dev
    ```

Este comando hará dos cosas simultáneamente:
- Iniciará el servidor de desarrollo de React.
- Lanzará la aplicación de escritorio de Electron, que cargará la interfaz de React.

¡Y listo! La aplicación debería estar funcionando en tu escritorio.
