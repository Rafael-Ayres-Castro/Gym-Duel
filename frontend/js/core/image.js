// Prepares a proof photo before upload: applies the camera orientation, scales the longest
// side down to 1600 px and re-encodes as JPEG 0.8 (which also drops the photo's metadata).
// The server cleans it again; this keeps uploads small on mobile data.

export const MAX_PHOTO_BYTES = 8 * 1024 * 1024;
const MAX_SIDE_PX = 1600;
const JPEG_QUALITY = 0.8;

export class PhotoError extends Error {}

export async function preparePhoto(file) {
  if (!file.type.startsWith('image/')) throw new PhotoError('Escolha um arquivo de imagem.');
  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch {
    throw new PhotoError('Não deu para abrir essa foto. Tente outra.');
  }
  const scale = Math.min(1, MAX_SIDE_PX / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY));
  if (!blob) throw new PhotoError('Não deu para preparar essa foto. Tente outra.');
  if (blob.size > MAX_PHOTO_BYTES) throw new PhotoError('A foto pode ter no máximo 8 MB.');
  return blob;
}
