// electron/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

function createWindow() {
  // Crea la ventana principal de la aplicación.
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      // El preload script es el puente entre el frontend (React) y el backend (Node.js).
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Carga la aplicación de React que se está ejecutando en el servidor de desarrollo.
  win.loadURL('http://localhost:3000');

  // Opcional: Abre las herramientas de desarrollo de Chrome.
  win.webContents.openDevTools();
}

app.whenReady().then(createWindow);

// --- IPC Handlers: Aquí definimos las funciones del backend ---

// 1. Abrir un archivo .tex
ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'LaTeX', extensions: ['tex'] }],
  });
  if (canceled) {
    return;
  } else {
    const filePath = filePaths[0];
    const content = fs.readFileSync(filePath, 'utf-8');
    return { filePath, content };
  }
});

// 2. Guardar el contenido en un archivo .tex
ipcMain.handle('file:saveFile', async (event, { filePath, content }) => {
  let finalPath = filePath;
  // Si no hay una ruta de archivo, significa que es un "Guardar como..."
  if (!finalPath) {
    const { canceled, filePath: newPath } = await dialog.showSaveDialog({
      filters: [{ name: 'LaTeX', extensions: ['tex'] }],
    });
    if (canceled) return { success: false };
    finalPath = newPath;
  }

  fs.writeFileSync(finalPath, content);
  return { success: true, filePath: finalPath };
});


// 3. Compilar el archivo .tex a PDF
ipcMain.handle('tex:compile', async (event, { filePath, content }) => {
  if (!filePath) {
    return { success: false, log: 'Por favor, guarda el archivo antes de compilar.' };
  }

  // Primero, nos aseguramos de que el archivo esté guardado con el contenido más reciente.
  fs.writeFileSync(filePath, content);

  const dir = path.dirname(filePath);
  const command = `pdflatex -interaction=nonstopmode -output-directory="${dir}" "${filePath}"`;

  return new Promise((resolve) => {
    exec(command, (error, stdout, stderr) => {
      const pdfPath = filePath.replace('.tex', '.pdf');
      if (error) {
        // Si hay un error, devolvemos el log para mostrarlo en el frontend.
        resolve({ success: false, log: stdout || stderr });
      } else {
        // Si la compilación es exitosa, devolvemos la ruta al PDF.
        resolve({ success: true, pdfPath });
      }
    });
  });
});
