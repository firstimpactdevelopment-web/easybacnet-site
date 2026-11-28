// Easy BACnet shared-scan crypto (format v1). Must match ShareCrypto.kt in the
// phone and PC apps byte for byte.
//
//   code    8 characters from ALPHABET (no 0/O, 1/I look-alikes)
//   PBKDF2-HMAC-SHA256(code, "easybacnet-share-v1", 600000 rounds) -> 64 bytes
//   bytes  0..31  AES-256-GCM key
//   bytes 32..47  folder id (hex) the server files scans under
//   blob    base64( 12-byte nonce || AES-GCM(gzip(JSON)) ), additional data = folder id
//   open-mode blob = base64( gzip(JSON) ), not encrypted

export const ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
export const SALT = "easybacnet-share-v1";
export const ROUNDS = 600000;

const enc = new TextEncoder();
const dec = new TextDecoder();

/** "k7qm 4xpr" / "K7QM-4XPR" -> "K7QM4XPR", or null when it can't be a code. */
export function normalizeCode(text) {
  // Same rule as ShareCrypto.normalize in the apps: keep only letters and digits.
  const s = String(text || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (s.length !== 8) return null;
  for (const ch of s) if (!ALPHABET.includes(ch)) return null;
  return s;
}

export function formatCode(code) {
  return code.slice(0, 4) + "-" + code.slice(4);
}

export function newCode() {
  const r = crypto.getRandomValues(new Uint8Array(8));
  return [...r].map((b) => ALPHABET[b & 31]).join("");
}

const hex = (u8) => [...u8].map((b) => b.toString(16).padStart(2, "0")).join("");

export async function deriveKeys(code) {
  const base = await crypto.subtle.importKey("raw", enc.encode(code), "PBKDF2", false, ["deriveBits"]);
  const bits = new Uint8Array(await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt: enc.encode(SALT), iterations: ROUNDS }, base, 512));
  const key = await crypto.subtle.importKey("raw", bits.slice(0, 32), "AES-GCM", false, ["encrypt", "decrypt"]);
  return { key, id: hex(bits.slice(32, 48)) };
}

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function bytesToB64(u8) {
  let s = "";
  for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode(...u8.subarray(i, i + 0x8000));
  return btoa(s);
}

/** A shared scan never unpacks to more than this; anything bigger is refused (a "zip bomb"). */
const MAX_UNPACKED = 64 * 1024 * 1024;

async function pipe(u8, stream, limit = Infinity) {
  const reader = new Blob([u8]).stream().pipeThrough(stream).getReader();
  const parts = []; let n = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    n += value.length;
    if (n > limit) { await reader.cancel(); throw new Error("This scan is too big to open."); }
    parts.push(value);
  }
  const out = new Uint8Array(n); let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}
const gzip = (u8) => pipe(u8, new CompressionStream("gzip"));
const gunzip = (u8) => pipe(u8, new DecompressionStream("gzip"), MAX_UNPACKED);

/** Opens one stored blob (or summary) and returns the parsed JSON. */
export async function openBlob(b64, keys, encrypted) {
  // Every real scan is encrypted; an unencrypted one can only be a fake.
  if (!encrypted) throw new Error("This scan isn't encrypted, so it can't be trusted.");
  let raw = b64ToBytes(b64);
  raw = new Uint8Array(await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: raw.slice(0, 12), additionalData: enc.encode(keys.id) }, keys.key, raw.slice(12)));
  return JSON.parse(dec.decode(await gunzip(raw)));
}

/** The reverse of openBlob (the apps do this in Kotlin; used by tests). */
export async function sealBlob(obj, keys, encrypted) {
  const packed = await gzip(enc.encode(JSON.stringify(obj)));
  if (!encrypted) return bytesToB64(packed);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt(
    { name: "AES-GCM", iv, additionalData: enc.encode(keys.id) }, keys.key, packed));
  const out = new Uint8Array(12 + ct.length);
  out.set(iv); out.set(ct, 12);
  return bytesToB64(out);
}
