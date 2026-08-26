import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { Trabajador } from '../modelos/tipos'
import { Campo, Cargando, EstadoVacio } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { Modal } from '../componentes/Modal'

export function TrabajadoresPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [cargando, setCargando] = useState(true)
  const [editando, setEditando] = useState<Trabajador | 'nuevo' | null>(null)
  const [error, setError] = useState('')

  const cargar = async () => {
    setCargando(true)
    try { setTrabajadores(await api.trabajadores()); setError('') }
    catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargar() }, [])

  const esNuevo = editando === 'nuevo'

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const datos: Record<string, unknown> = {
      nombre: String(form.get('nombre')),
      apellido: String(form.get('apellido')),
      telefono: String(form.get('telefono')),
      nombre_usuario: String(form.get('nombre_usuario')),
    }
    // Al modificar, la contraseña en blanco conserva la que tenía: no se
    // manda el campo vacío para que el backend no lo tome como un cambio.
    const clave = String(form.get('contrasena') || '')
    if (clave) datos.contrasena = clave

    try {
      if (esNuevo) await api.crearTrabajador(datos)
      else if (editando) await api.modificarTrabajador(editando.id_usuario, datos)
      setEditando(null)
      notificar(esNuevo ? 'Trabajador agregado con su cuenta.' : 'Trabajador actualizado.')
      await cargar()
    } catch (e) { setError((e as Error).message) }
  }

  const eliminar = async (trabajador: Trabajador) => {
    if (!window.confirm(`¿Eliminar a ${trabajador.nombre}?\n\nDejará de aparecer en el taller, pero los pedidos que hizo conservan su nombre.`)) return
    try {
      await api.eliminarTrabajador(trabajador.id_usuario)
      notificar('Trabajador eliminado del taller.')
      await cargar()
    } catch (e) { setError((e as Error).message) }
  }

  return (
    <div className="pagina">
      <section className="barra-herramientas barra-herramientas--derecha">
        <button className="boton boton--primario" onClick={() => setEditando('nuevo')}><Icono nombre="mas" /> Agregar trabajador</button>
      </section>
      {error && <p className="aviso aviso--error">{error}</p>}
      {cargando ? <Cargando /> : trabajadores.length === 0 ? (
        <EstadoVacio titulo="Aún no hay trabajadores" texto="Registra a la primera persona del equipo." />
      ) : (
        <section className="rejilla-trabajadores">
          {trabajadores.map((trabajador) => (
            <article className={`ficha-trabajador ${trabajador.estado_usuario === 'INACTIVO' ? 'ficha-trabajador--inactiva' : ''}`} key={trabajador.id_usuario}>
              <div className="ficha-trabajador__cabecera"><span className="avatar-grande">{trabajador.nombre.charAt(0)}{trabajador.apellido?.charAt(0)}</span><span className={`insignia ${trabajador.estado_usuario === 'ACTIVO' ? 'insignia--verde' : 'insignia--gris'}`}>{trabajador.estado_usuario.toLowerCase()}</span></div>
              <h2>{trabajador.nombre} {trabajador.apellido}</h2>
              <p>{trabajador.telefono || 'Sin teléfono registrado'}</p>
              {trabajador.nombre_usuario && <p className="texto-tenue">Usuario: {trabajador.nombre_usuario}</p>}
              <div className="ficha-trabajador__acciones"><button className="boton-texto" onClick={() => setEditando(trabajador)}><Icono nombre="editar" tamano={17} /> Editar</button>{trabajador.estado_usuario === 'ACTIVO' && <button className="boton-texto boton-texto--peligro" onClick={() => eliminar(trabajador)}>Eliminar</button>}</div>
            </article>
          ))}
        </section>
      )}
      {editando && (
        <Modal
          titulo={esNuevo ? 'Agregar trabajador' : 'Modificar trabajador'}
          subtitulo={esNuevo
            ? 'Con estos datos se crea su cuenta para entrar al sistema.'
            : 'Deja la contraseña en blanco para conservar la actual.'}
          cerrar={() => setEditando(null)}
        >
          <form className="formulario" onSubmit={guardar}>
            <Campo etiqueta="Nombre"><input name="nombre" required defaultValue={esNuevo ? '' : editando.nombre} autoFocus /></Campo>
            <Campo etiqueta="Apellido"><input name="apellido" defaultValue={esNuevo ? '' : editando.apellido ?? ''} /></Campo>
            <Campo etiqueta="Teléfono" ancho="campo--completo"><input name="telefono" defaultValue={esNuevo ? '' : editando.telefono ?? ''} placeholder="+56 9 1234 5678" /></Campo>
            <Campo etiqueta="Nombre de usuario" ayuda="Minúsculas, números, punto, guion o guion bajo.">
              <input name="nombre_usuario" required minLength={3} maxLength={50} pattern="[a-z0-9._-]{3,50}" defaultValue={esNuevo ? '' : editando.nombre_usuario ?? ''} placeholder="marta.silva" />
            </Campo>
            <Campo etiqueta="Contraseña" ayuda={esNuevo ? 'Al menos 8 caracteres.' : 'Solo si quieres cambiarla.'}>
              <input name="contrasena" type="password" required={esNuevo} minLength={8} maxLength={128} autoComplete="new-password" placeholder={esNuevo ? '' : '••••••••'} />
            </Campo>
            <div className="acciones-formulario"><button type="button" className="boton boton--suave" onClick={() => setEditando(null)}>Cancelar</button><button className="boton boton--primario">{esNuevo ? 'Agregar trabajador' : 'Guardar cambios'}</button></div>
          </form>
        </Modal>
      )}
    </div>
  )
}
