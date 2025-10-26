// src/App.js
import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import './App.css';

function App() {
  // Estados para gestionar el contenido, las rutas y los logs.
  const [filePath, setFilePath] = useState(null);
  const [texContent, setTexContent] = useState('% Escribe tu código LaTeX aquí...');
  const [pdfUrl, setPdfUrl] = useState(null);
  const [logs, setLogs] = useState('Aquí verás los mensajes de compilación.');

  // --- Handlers para interactuar con el backend ---

  const handleOpenFile = async () => {
    const result = await window.api.openFile();
    if (result) {
      setFilePath(result.filePath);
      setTexContent(result.content);
      setPdfUrl(null); // Limpiamos el visor al abrir nuevo archivo
      setLogs('Archivo abierto. Listo para compilar.');
    }
  };

  const handleSaveFile = async () => {
    const result = await window.api.saveFile({ filePath, content: texContent });
    if (result.success) {
      setFilePath(result.filePath);
      alert('Archivo guardado!');
    }
  };

  const handleCompile = async () => {
    setLogs('Compilando...');
    const result = await window.api.compile({ filePath, content: texContent });

    setLogs(result.log || 'Compilación finalizada.');

    if (result.success) {
      // Agregamos un timestamp para forzar al navegador a recargar el PDF
      setPdfUrl(`file://${result.pdfPath}?t=${new Date().getTime()}`);
    }
  };

  return (
    <div className="app-container">
      <div className="toolbar">
        <button onClick={handleOpenFile}>Abrir Proyecto</button>
        <button onClick={handleSaveFile}>Guardar</button>
        <button className="compile-btn" onClick={handleCompile}>Compilar</button>
      </div>
      <div className="main-content">
        <div className="editor-pane">
          <Editor
            height="100%"
            language="latex"
            value={texContent}
            onChange={(value) => setTexContent(value)}
            theme="vs-dark"
          />
        </div>
        <div className="pdf-pane">
          {pdfUrl ? (
            <iframe src={pdfUrl} title="PDF Viewer" width="100%" height="100%" />
          ) : (
            <div className="placeholder">El PDF aparecerá aquí después de compilar</div>
          )}
        </div>
      </div>
      <div className="logs-pane">
        <h3>Logs de Compilación</h3>
        <pre>{logs}</pre>
      </div>
    </div>
  );
}

export default App;
