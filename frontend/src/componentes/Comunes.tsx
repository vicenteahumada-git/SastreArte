import type { ReactNode } from 'react'

export const moneda = (valor: number | null | undefined) =>
  new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(valor ?? 0)

export const fecha = (valor: string | null | undefined, larga = false) => {
  if (!valor) return 'Sin fecha'
  const base = valor.length === 10 ? `${valor}T12:00:00` : valor
  return new Intl.DateTimeFormat('es-CL', {
    day: '2-digit',
    month: larga ? 'long' : 'short',
    year: larga ? 'numeric' : undefined,
  }).format(new Date(base))
}

/** Convierte los tokens del dominio en texto legible: EN_PROCESO → En proceso. */
export const etiqueta = (valor: string | null | undefined) => {
  if (!valor) return 'Sin definir'
  const texto = valor.toLowerCase().replaceAll('_', ' ')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/**
 * Muestra la unidad de medida como se escribe de verdad. etiqueta() no sirve
 * acá porque capitaliza y dejaría "Mm" y "Cm" en vez de "mm" y "cm".
 */
const UNIDADES: Record<string, string> = {
  MM: 'mm',
  CM: 'cm',
  METROS: 'metros',
  UNIDADES: 'unidades',
}
export const unidad = (valor: string | null | undefined) =>
  UNIDADES[valor ?? ''] ?? (valor ?? '').toLowerCase()

/** Formatea una tasa 0.19 como "19%". */
export const porcentaje = (valor: number | null | undefined) =>
  `${Math.round((valor ?? 0) * 100)}%`

export function EstadoVacio({
  titulo,
  texto,
  accion,
}: {
  titulo: string
  texto: string
  accion?: ReactNode
}) {
  return (
    <div className="estado-vacio">
      <span className="estado-vacio__carrete" aria-hidden="true" />
      <h3>{titulo}</h3>
      <p>{texto}</p>
      {accion}
    </div>
  )
}

export function Cargando() {
  return (
    <div className="cargando" aria-live="polite">
      <span /> Preparando la mesa de trabajo…
    </div>
  )
}

export function Campo({
  etiqueta: nombre,
  ayuda,
  children,
  ancho = '',
}: {
  etiqueta: string
  ayuda?: string
  children: ReactNode
  ancho?: string
}) {
  return (
    <label className={`campo ${ancho}`}>
      <span>{nombre}</span>
      {children}
      {ayuda && <small>{ayuda}</small>}
    </label>
  )
}

