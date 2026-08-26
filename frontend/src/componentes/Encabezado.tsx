import type { Seccion, SesionUsuario } from '../modelos/tipos'
import { Icono } from './Icono'

const titulos: Record<Seccion, [string, string]> = {
  resumen: ['Mesa general', 'Lo importante del taller, de un vistazo'],
  pedidos: ['Pedidos', 'Cada encargo, su historia y su fecha'],
  clientes: ['Clientes', 'Una libreta clara y siempre disponible'],
  pagos: ['Pagos y abonos', 'Cuentas visibles, saldos sin cálculos manuales'],
  insumos: ['Insumos', 'Materiales del taller y de cada pedido'],
  compras: ['Lista de compras', 'Lo pendiente, reunido en una sola hoja'],
  trabajadores: ['Trabajadores', 'Equipo, carga y continuidad del taller'],
}

export function Encabezado({
  seccion,
  sesion,
  cerrarSesion,
  abrirMenu,
}: {
  seccion: Seccion
  sesion: SesionUsuario
  cerrarSesion: () => void
  abrirMenu: () => void
}) {
  const [titulo, bajada] = titulos[seccion]
  const nombreMostrado = sesion.apellido
    ? `${sesion.nombre} ${sesion.apellido}`
    : sesion.nombre
  const etiquetaRol = sesion.tipo_usuario === 'DUENO' ? 'Dueña' : 'Trabajador/a'

  return (
    <header className="encabezado">
      <button className="boton-menu" onClick={abrirMenu} aria-label="Abrir navegación">
        <Icono nombre="menu" />
      </button>
      <div className="encabezado__titulo">
        <span className="sobretitulo">SastreArte</span>
        <h1>{titulo}</h1>
        <p>{bajada}</p>
      </div>
      <div className="encabezado__usuario">
        <span className="encabezado__usuario-nombre">{nombreMostrado}</span>
        <span className="encabezado__usuario-rol">{etiquetaRol}</span>
        <button
          className="boton boton--secundario encabezado__cerrar-sesion"
          onClick={cerrarSesion}
          title="Cerrar sesión"
        >
          <Icono nombre="log-out" />
          <span>Salir</span>
        </button>
      </div>
    </header>
  )
}
