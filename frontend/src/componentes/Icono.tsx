import type { ReactNode } from 'react'

const trazos: Record<string, ReactNode> = {
  resumen: <><path d="M4 13h6V4H4zM14 20h6v-9h-6zM4 20h6v-3H4zM14 7h6V4h-6z" /></>,
  pedidos: <><path d="M7 4h10l2 3v13H5V7z" /><path d="M8 11h8M8 15h6" /></>,
  clientes: <><circle cx="9" cy="8" r="3" /><path d="M3.5 20v-2a5.5 5.5 0 0 1 11 0v2M16 8a3 3 0 0 1 0 6M18 16a4 4 0 0 1 2.5 4" /></>,
  pagos: <><rect x="3" y="6" width="18" height="12" rx="2" /><path d="M3 10h18M16 15h2" /></>,
  insumos: <><path d="M5 4h14v16H5zM9 4v16M15 4v16M5 9h14M5 15h14" /></>,
  compras: <><path d="M4 5h2l2 11h10l2-8H7M10 20h.01M17 20h.01" /></>,
  trabajadores: <><circle cx="12" cy="7" r="4" /><path d="M5 21v-2a7 7 0 0 1 14 0v2M19 5l2 2-2 2" /></>,
  buscar: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  mas: <><path d="M12 5v14M5 12h14" /></>,
  cerrar: <><path d="m6 6 12 12M18 6 6 18" /></>,
  editar: <><path d="m4 20 4.5-1 10-10-3.5-3.5-10 10zM13.5 7l3.5 3.5" /></>,
  eliminar: <><path d="M4 7h16M10 4h4M6 7l1 13h10l1-13M10 11v6M14 11v6" /></>,
  impresora: <><path d="M7 9V4h10v5M7 18H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 15h10v6H7z" /></>,
  flecha: <><path d="M5 12h14M14 7l5 5-5 5" /></>,
  aguja: <><path d="M6 18 18 6M15 5l4-1-1 4M5 15l4 4M4 20h4" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  'log-out': <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" /></>,
}

export function Icono({ nombre, tamano = 20 }: { nombre: string; tamano?: number }) {
  return (
    <svg
      className="icono"
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {trazos[nombre] ?? trazos.aguja}
    </svg>
  )
}

