import { neon } from "@neondatabase/serverless";

/** Cliente SQL de Neon. Reemplaza `logic/titulacion_db.py:get_conn()`. */
export const sql = neon(process.env.DATABASE_URL!);
