import JSZip from "jszip";

export async function crearZip(archivos: Array<{ nombre: string; buffer: Buffer }>): Promise<Buffer> {
  const zip = new JSZip();
  for (const { nombre, buffer } of archivos) {
    zip.file(nombre, buffer);
  }
  return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
}
