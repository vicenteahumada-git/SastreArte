import { useState } from 'react'
import type { SesionUsuario } from '../modelos/tipos'
import { api } from '../servicios_api/api'

export function LoginPagina({ onLogin }: { onLogin: (sesion: SesionUsuario) => void }) {
  const [nombreUsuario, setNombreUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const sesion = await api.iniciarSesion({ nombre_usuario: nombreUsuario, contrasena })
      onLogin(sesion)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible iniciar sesión.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="login-fondo">
      <div className="login-contenedor">
        <div className="login-lateral" aria-hidden="true">
          <span className="login-lateral__marca">SastreArte</span>
          <p className="login-lateral__lema">
            El taller en orden,<br />el oficio en foco.
          </p>
          <div className="login-lateral__tejido" />
        </div>
        <div className="login-panel">
          <span className="sobretitulo">Bienvenida</span>
          <h1 className="login-titulo">Iniciar sesión</h1>
          <p className="login-bajada">Ingresa tus credenciales para acceder al taller</p>
          <form className="login-formulario" onSubmit={enviar}>
            <div className="campo">
              <label htmlFor="nombre_usuario">Usuario</label>
              <input
                id="nombre_usuario"
                type="text"
                autoComplete="username"
                value={nombreUsuario}
                onChange={(e) => setNombreUsuario(e.target.value)}
                placeholder="nombre de usuario"
                required
                disabled={cargando}
              />
            </div>
            <div className="campo">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                id="contrasena"
                type="password"
                autoComplete="current-password"
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                placeholder="contraseña"
                required
                disabled={cargando}
              />
            </div>
            {error && <p className="login-error" role="alert">{error}</p>}
            <button
              className="boton boton--primario login-boton"
              type="submit"
              disabled={cargando}
            >
              {cargando ? 'Ingresando…' : 'Ingresar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
