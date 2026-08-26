import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './estilos/base.css'
import './estilos/estructura.css'
import './estilos/componentes.css'
import './estilos/paginas.css'
import './estilos/impresion.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
