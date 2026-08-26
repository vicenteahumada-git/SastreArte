import { useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { Resumen, Seccion } from '../modelos/tipos'
import { Cargando, EstadoVacio, etiqueta, fecha, moneda } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'

export function ResumenPagina({
  irA,
  registrarPedido,
}: {
  irA: (seccion: Seccion) => void
  registrarPedido: () => void
}) {
  const [resumen, setResumen] = useState<Resumen | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.resumen().then(setResumen).catch((e: Error) => setError(e.message))
  }, [])

  if (!resumen && !error) return <Cargando />
  if (!resumen) return <EstadoVacio titulo="No pudimos abrir la mesa" texto={error} />

  const metricas = [
    { rotulo: 'Pedidos activos', valor: resumen.metricas.pedidos_activos, detalle: `${resumen.metricas.pedidos_totales} registrados`, icono: 'pedidos' },
    { rotulo: 'Entregas esta semana', valor: resumen.metricas.entregas_semana, detalle: 'Próximos 7 días', icono: 'aguja' },
    { rotulo: 'Saldo por cobrar', valor: moneda(resumen.metricas.saldo_pendiente), detalle: 'En pedidos vigentes', icono: 'pagos' },
    { rotulo: 'Insumos pendientes', valor: resumen.metricas.insumos_pendientes, detalle: 'Materiales por comprar', icono: 'compras' },
  ]
  const maximoEstado = Math.max(...resumen.estados.map((item) => item.cantidad), 1)

  return (
    <div className="pagina pagina-resumen">
      <section className="bienvenida-taller">
        <div>
          <span className="sobretitulo">Puntada del día</span>
          <h2>Todo el taller, bien hilado</h2>
          <p>
            Hay <strong>{resumen.metricas.pedidos_activos} encargos activos</strong> y{' '}
            <strong>{resumen.metricas.entregas_semana} entregas</strong> que requieren atención esta semana.
          </p>
          <div className="acciones-bienvenida">
            <button className="boton boton--claro" onClick={registrarPedido}>
              <Icono nombre="mas" /> Registrar pedido
            </button>
            <button className="boton-texto boton-texto--claro" onClick={() => irA('pedidos')}>
              Revisar pedidos <Icono nombre="flecha" />
            </button>
          </div>
        </div>
        <div className="bienvenida-taller__figura" aria-hidden="true">
          <span className="cinta cinta--uno">10</span>
          <span className="cinta cinta--dos">20</span>
          <span className="maniqui-linea" />
        </div>
      </section>

      <section className="rejilla-metricas" aria-label="Indicadores del taller">
        {metricas.map((metrica) => (
          <article className="tarjeta-metrica" key={metrica.rotulo}>
            <span className="tarjeta-metrica__icono"><Icono nombre={metrica.icono} /></span>
            <div><span>{metrica.rotulo}</span><strong>{metrica.valor}</strong><small>{metrica.detalle}</small></div>
          </article>
        ))}
      </section>

      <div className="rejilla-resumen">
        <section className="panel papel-costura">
          <header className="panel__cabecera">
            <div><span className="sobretitulo">Agenda próxima</span><h2>Entregas en la mesa</h2></div>
            <button className="boton-texto" onClick={() => irA('pedidos')}>Ver todas</button>
          </header>
          {resumen.proximos.length === 0 ? (
            <EstadoVacio titulo="La agenda está despejada" texto="No hay entregas activas registradas." />
          ) : (
            <div className="lista-entregas">
              {resumen.proximos.map((pedido) => (
                <article className="entrega" key={pedido.id_pedido}>
                  <time><b>{fecha(pedido.fecha_entrega).split(' ')[0]}</b><span>{fecha(pedido.fecha_entrega).split(' ')[1]}</span></time>
                  <div className="entrega__detalle">
                    <strong>Guía #{pedido.id_pedido}</strong>
                    <span>{pedido.cliente_nombre}</span>
                    <p>{pedido.descripcion}</p>
                  </div>
                  <span className={`insignia estado-${pedido.estado.toLowerCase()}`}>{etiqueta(pedido.estado)}</span>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel panel-estados">
          <header className="panel__cabecera">
            <div><span className="sobretitulo">Carga actual</span><h2>Estado de los encargos</h2></div>
          </header>
          <div className="barras-estados">
            {resumen.estados.map((item) => (
              <div key={item.estado}>
                <div><span>{etiqueta(item.estado)}</span><b>{item.cantidad}</b></div>
                <span className="barra"><i style={{ width: `${(item.cantidad / maximoEstado) * 100}%` }} /></span>
              </div>
            ))}
          </div>
          <div className="nota-taller">
            <Icono nombre="aguja" />
            <p><strong>{resumen.metricas.trabajadores_activos} personas activas</strong><span>disponibles para asignaciones.</span></p>
          </div>
        </section>
      </div>
    </div>
  )
}

