import { sql } from "./db";

export interface Docente {
  id: number;
  titulo_grado: string;
  nombre: string;
  post_grado: string;
  cargo: string;
  carrera: string;
  es_director: boolean;
}

export async function getAllDocentes(): Promise<Docente[]> {
  const rows = await sql`SELECT * FROM docentes ORDER BY es_director DESC, nombre ASC`;
  return rows as Docente[];
}

export async function getDocentesByCarrera(carrera: string): Promise<Docente[]> {
  const rows = await sql`
    SELECT * FROM docentes WHERE carrera = ${carrera} ORDER BY es_director DESC, nombre ASC
  `;
  return rows as Docente[];
}

export async function getAllCarreras(): Promise<string[]> {
  const rows = await sql`SELECT DISTINCT carrera FROM docentes ORDER BY carrera ASC`;
  return (rows as Array<{ carrera: string }>).map((r) => r.carrera);
}
