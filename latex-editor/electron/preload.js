// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

// Exponemos un objeto 'api' en el objeto 'window' del frontend.
contextBridge.exposeInMainWorld('api', {
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (args) => ipcRenderer.invoke('file:saveFile', args),
  compile: (args) => ipcRenderer.invoke('tex:compile', args),
});
