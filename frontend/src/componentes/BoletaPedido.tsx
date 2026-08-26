import { useState } from 'react'
import type { Pedido } from '../modelos/tipos'
import { TALLER } from '../modelos/taller'
import { moneda } from './Comunes'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']

function aFecha(valor: string | null | undefined): Date | null {
  if (!valor) return null
  return new Date(valor.length === 10 ? `${valor}T12:00:00` : valor)
}

/** "27 de julio de 2026", como se escribe a mano en la guía. */
function enPalabras(valor: string | null | undefined): string {
  const fecha = aFecha(valor)
  if (!fecha) return '—'
  return `${fecha.getDate()} de ${MESES[fecha.getMonth()]} de ${fecha.getFullYear()}`
}

/** "miércoles 29 de julio", que es como la dueña anota la entrega. */
function conDiaSemana(valor: string | null | undefined): string {
  const fecha = aFecha(valor)
  if (!fecha) return '—'
  return `${DIAS[fecha.getDay()]} ${fecha.getDate()} de ${MESES[fecha.getMonth()]}`
}

/**
 * Comprobante que se entrega al cliente, calcado del talonario de papel:
 * misma tinta azul, mismo orden de datos y la misma tabla con recuadro.
 *
 * En pantalla está oculto; sólo aparece al imprimir (estilos/impresion.css).
 * El monto es el total ya con IVA, descuento y recargo aplicados: el
 * desglose es información interna del taller y no va en la boleta.
 */
export function BoletaPedido({ pedido }: { pedido: Pedido }) {
  const [sinLogo, setSinLogo] = useState(false)

  return (
    <article className="boleta" aria-hidden="true">
      <header className="boleta__cabecera">
        {/* Si el logo no carga, va el nombre en texto: mejor eso que dejar
            un hueco en blanco arriba de la boleta. */}
        {sinLogo ? (
          <p className="boleta__nombre">{TALLER.nombre}</p>
        ) : (
          <img
            src="/logo-sastrearte.png"
            alt=""
            className="boleta__logo"
            onError={() => setSinLogo(true)}
          />
        )}
        <p className="boleta__direccion">{TALLER.direccion}</p>
        <p className="boleta__direccion">{TALLER.telefono}</p>
        <p className="boleta__aviso">{TALLER.aviso}</p>
      </header>

      <div className="boleta__guia">
        <span>Guía</span>
        <strong>N° {pedido.id_pedido}</strong>
      </div>

      <p className="boleta__lugar">
        Santiago, <em>{enPalabras(pedido.fecha_registro)}</em>
      </p>

      <div className="boleta__datos">
        <p className="boleta__linea boleta__linea--nombre">
          <span>Nombre</span><em>{pedido.cliente_nombre}</em>
        </p>
        <p className="boleta__linea">
          <span>Fono</span><em>{pedido.cliente_telefono}</em>
        </p>
        <p className="boleta__linea boleta__linea--ancha">
          <span>Fecha de entrega</span><em>{conDiaSemana(pedido.fecha_entrega)}</em>
        </p>
      </div>

      <table className="boleta__detalle">
        <thead>
          <tr>
            <th>Descripción</th>
            <th>Total</th>
            <th>Abono</th>
            <th>Saldo</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="boleta__encargo">{pedido.descripcion}</td>
            <td>{moneda(pedido.total)}</td>
            <td>{moneda(pedido.total_pagado)}</td>
            <td className="boleta__saldo">{moneda(pedido.saldo_restante)}</td>
          </tr>
        </tbody>
      </table>

      <p className="boleta__nota">NOTA: {TALLER.nota}</p>
    </article>
  )
}
