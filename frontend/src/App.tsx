import { useEffect, useRef, useState } from 'react'
import { BoletaPedido } from './componentes/BoletaPedido'
import { Encabezado } from './componentes/Encabezado'
import { Navegacion } from './componentes/Navegacion'
import type { Pedido, RolOperativo, Seccion, SesionUsuario } from './modelos/tipos'
import { ClientesPagina } from './paginas/ClientesPagina'
import { ComprasPagina } from './paginas/ComprasPagina'
import { InsumosPagina } from './paginas/InsumosPagina'
import { LoginPagina } from './paginas/LoginPagina'
import { PagosPagina } from './paginas/PagosPagina'
import { PedidosPagina } from './paginas/PedidosPagina'
import { ResumenPagina } from './paginas/ResumenPagina'
import { TrabajadoresPagina } from './paginas/TrabajadoresPagina'

const CLAVE_SESION = 'sastrearte_sesion'

const secciones: Seccion[] = ['resumen', 'pedidos', 'clientes', 'pagos', 'insumos', 'compras', 'trabajadores']
const soloDueno: Seccion[] = ['pagos', 'insumos', 'compras', 'trabajadores']

function seccionInicial(): Seccion {
  const hash = window.location.hash.replace('#/', '') as Seccion
  return secciones.includes(hash) ? hash : 'resumen'
}

function cargarSesion(): SesionUsuario | null {
  try {
    const crudo = localStorage.getItem(CLAVE_SESION)
    return crudo ? (JSON.parse(crudo) as SesionUsuario) : null
  } catch {
    return null
  }
}

export default function App() {
  const [sesion, setSesion] = useState<SesionUsuario | null>(cargarSesion)
  const [seccion, setSeccion] = useState<Seccion>(seccionInicial)
  const [menuAbierto, setMenuAbierto] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [abrirNuevoPedido, setAbrirNuevoPedido] = useState(false)
  const [boleta, setBoleta] = useState<Pedido | null>(null)
  const temporizador = useRef<number | null>(null)

  // El rol se deriva directamente del tipo de usuario autenticado
  const rol: RolOperativo = sesion?.tipo_usuario === 'DUENO' ? 'DUENO' : 'TRABAJADOR'

  // Mantener sincronía con X-Rol-Operativo que usa api.ts
  useEffect(() => {
    localStorage.setItem('sastrearte_rol', rol)
  }, [rol])

  const irA = (destino: Seccion) => {
    setSeccion(destino)
    window.location.hash = `/${destino}`
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cerrarSesion = () => {
    localStorage.removeItem(CLAVE_SESION)
    localStorage.removeItem('sastrearte_rol')
    setSesion(null)
    setSeccion('resumen')
    window.location.hash = ''
  }

  const notificar = (texto: string) => {
    setMensaje(texto)
    if (temporizador.current) window.clearTimeout(temporizador.current)
    temporizador.current = window.setTimeout(() => setMensaje(''), 3500)
  }

  useEffect(() => {
    const escuchar = () => setSeccion(seccionInicial())
    window.addEventListener('hashchange', escuchar)
    return () => window.removeEventListener('hashchange', escuchar)
  }, [])

  // Redirigir si la sección actual no está disponible para el rol
  useEffect(() => {
    if (rol === 'TRABAJADOR' && soloDueno.includes(seccion)) irA('resumen')
  }, [rol, seccion])

  useEffect(() => {
    if (!boleta) return
    let vigente = true
    const limpiar = () => setBoleta(null)
    window.addEventListener('afterprint', limpiar)

    const imprimir = async () => {
      await new Promise((listo) =>
        window.requestAnimationFrame(() => window.requestAnimationFrame(listo)),
      )
      const imagenes = Array.from(
        document.querySelectorAll<HTMLImageElement>('.boleta img'),
      )
      await Promise.all(
        imagenes.map((imagen) =>
          imagen.decode?.().catch(() => undefined) ?? Promise.resolve(),
        ),
      )
      if (vigente) window.print()
    }
    void imprimir()

    return () => {
      vigente = false
      window.removeEventListener('afterprint', limpiar)
    }
  }, [boleta])

  const registrarPedido = () => {
    setAbrirNuevoPedido(true)
    irA('pedidos')
  }

  const contenido = () => {
    switch (seccion) {
      case 'pedidos': return <PedidosPagina rol={rol} notificar={notificar} imprimirBoleta={setBoleta} abrirNuevo={abrirNuevoPedido} nuevoAbierto={() => setAbrirNuevoPedido(false)} />
      case 'clientes': return <ClientesPagina rol={rol} notificar={notificar} />
      case 'pagos': return <PagosPagina notificar={notificar} />
      case 'insumos': return <InsumosPagina notificar={notificar} />
      case 'compras': return <ComprasPagina notificar={notificar} />
      case 'trabajadores': return <TrabajadoresPagina notificar={notificar} />
      default: return <ResumenPagina irA={irA} registrarPedido={registrarPedido} />
    }
  }

  // Si no hay sesión activa, mostrar el login
  if (!sesion) {
    return (
      <LoginPagina
        onLogin={(nuevaSesion) => {
          localStorage.setItem(CLAVE_SESION, JSON.stringify(nuevaSesion))
          setSesion(nuevaSesion)
        }}
      />
    )
  }

  return (
    <>
      <div className="aplicacion">
        <Navegacion seccion={seccion} irA={irA} rol={rol} abierta={menuAbierto} cerrar={() => setMenuAbierto(false)} />
        {menuAbierto && <button className="velo-menu" aria-label="Cerrar navegación" onClick={() => setMenuAbierto(false)} />}
        <main className="contenido-principal">
          <Encabezado
            seccion={seccion}
            sesion={sesion}
            cerrarSesion={cerrarSesion}
            abrirMenu={() => setMenuAbierto(true)}
          />
          {contenido()}
        </main>
        {mensaje && <div className="notificacion" role="status"><span>✓</span>{mensaje}</div>}
      </div>
      {boleta && <BoletaPedido pedido={boleta} />}
    </>
  )
}
