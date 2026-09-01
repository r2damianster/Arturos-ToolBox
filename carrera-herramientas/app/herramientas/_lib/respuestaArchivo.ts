import { NextResponse } from "next/server";

const MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const MIME_ZIP = "application/zip";

function respuestaBuffer(buffer: Buffer, mime: string, nombreArchivo: string) {
  return new NextResponse(new Uint8Array(buffer), {
    headers: {
      "Content-Type": mime,
      "Content-Disposition": `attachment; filename="${nombreArchivo}"`,
    },
  });
}

export function respuestaDocx(buffer: Buffer, nombreArchivo: string) {
  return respuestaBuffer(buffer, MIME_DOCX, nombreArchivo);
}

export function respuestaZip(buffer: Buffer, nombreArchivo: string) {
  return respuestaBuffer(buffer, MIME_ZIP, nombreArchivo);
}
