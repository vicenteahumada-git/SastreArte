/**
 * Datos fijos del taller que van impresos en la boleta.
 *
 * No están en la base porque no hay entidad "taller": el sistema atiende a
 * uno solo. Si algún día se administran varios, esto pasa a una tabla.
 */
export const TALLER = {
  nombre: 'SastreArte',
  direccion: 'Francisco Bilbao 2415, Providencia',
  telefono: '+56 9 8202 8816 (Verónica)',
  aviso: 'Retiro desde las 17:30 hrs',
  nota: 'No se responde por prendas no retiradas pasado 60 días.',
} as const
