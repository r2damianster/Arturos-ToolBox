import fs from "fs";
import path from "path";

const envPath = path.join(process.cwd(), ".env.local");
if (fs.existsSync(envPath)) {
  const contenido = fs.readFileSync(envPath, "utf8");
  for (const linea of contenido.split("\n")) {
    const match = /^([A-Z_][A-Z0-9_]*)=(.*)$/.exec(linea.trim());
    if (!match) continue;
    const [, clave, valor] = match;
    process.env[clave] = valor.trim();
  }
}
