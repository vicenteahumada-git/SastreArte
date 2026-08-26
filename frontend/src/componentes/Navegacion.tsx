import type { RolOperativo, Seccion } from '../modelos/tipos'
import { Icono } from './Icono'

const opciones: Array<{ id: Seccion; texto: string; soloDueno?: boolean }> = [
  { id: 'resumen', texto: 'Mesa general' },
  { id: 'pedidos', texto: 'Pedidos' },
  { id: 'clientes', texto: 'Clientes' },
  { id: 'pagos', texto: 'Pagos y abonos', soloDueno: true },
  { id: 'insumos', texto: 'Insumos', soloDueno: true },
  { id: 'compras', texto: 'Lista de compras', soloDueno: true },
  { id: 'trabajadores', texto: 'Trabajadores', soloDueno: true },
]

export function Navegacion({
  seccion,
  irA,
  rol,
  abierta,
  cerrar,
}: {
  seccion: Seccion
  irA: (seccion: Seccion) => void
  rol: RolOperativo
  abierta: boolean
  cerrar: () => void
}) {
  return (
    <aside className={`navegacion ${abierta ? 'navegacion--abierta' : ''}`}>
      <div className="navegacion__marca">
        <img src="/logo-sastrearte.png" alt="SastreArte" />
        <span>Gestión de taller</span>
      </div>
      <nav aria-label="Secciones principales">
        <span className="navegacion__rotulo">Cuaderno del taller</span>
        {opciones
          .filter((opcion) => rol === 'DUENO' || !opcion.soloDueno)
          .map((opcion) => (
            <button
              key={opcion.id}
              className={seccion === opcion.id ? 'activo' : ''}
              onClick={() => {
                irA(opcion.id)
                cerrar()
              }}
            >
              <Icono nombre={opcion.id} />
              <span>{opcion.texto}</span>
            </button>
          ))}
      </nav>
      <div className="navegacion__pie">
        <span className="muestra-tela" />
        <div><strong>SastreArte</strong><small>Edición de taller</small></div>
      </div>
    </aside>
  )
}

