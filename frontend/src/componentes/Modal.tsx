import type { ReactNode } from 'react'
import { Icono } from './Icono'

export function Modal({
  titulo,
  subtitulo,
  cerrar,
  children,
  ancho = 'medio',
}: {
  titulo: string
  subtitulo?: string
  cerrar: () => void
  children: ReactNode
  ancho?: 'medio' | 'amplio'
}) {
  return (
    <div className="modal-fondo" role="presentation" onMouseDown={cerrar}>
      <section
        className={`modal modal--${ancho}`}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onMouseDown={(evento) => evento.stopPropagation()}
      >
        <header className="modal__cabecera">
          <div>
            <span className="sobretitulo">Mesa de trabajo</span>
            <h2>{titulo}</h2>
            {subtitulo && <p>{subtitulo}</p>}
          </div>
          <button className="boton-icono" onClick={cerrar} aria-label="Cerrar">
            <Icono nombre="cerrar" />
          </button>
        </header>
        <div className="modal__contenido">{children}</div>
      </section>
    </div>
  )
}

