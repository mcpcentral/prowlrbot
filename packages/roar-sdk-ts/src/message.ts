import * as crypto from "crypto";
import { AgentIdentity, MessageIntent, ROARMessage } from "./types";

/**
 * Create a new ROAR message.
 *
 * Matches Python's ROARMessage construction exactly.
 *
 * @param from - The sender's identity.
 * @param to - The recipient's identity.
 * @param intent - The semantic intent of the message.
 * @param payload - The message payload.
 * @param context - Optional context metadata.
 * @returns A new ROARMessage with a unique ID and timestamp.
 */
export function createMessage(
  from: AgentIdentity,
  to: AgentIdentity,
  intent: MessageIntent,
  payload: Record<string, unknown> = {},
  context: Record<string, unknown> = {},
): ROARMessage {
  return {
    roar: "1.0",
    id: `msg_${crypto.randomBytes(5).toString("hex")}`,
    from_identity: from,
    to_identity: to,
    intent,
    payload,
    context,
    auth: {},
    timestamp: Date.now() / 1000, // Unix epoch (seconds), matches Python's time.time()
  };
}

/**
 * Compute the canonical string for signing.
 *
 * MUST match Python's signing canonical body exactly:
 *   json.dumps({context, from, id, intent, payload, timestamp, to}, sort_keys=True)
 *
 * - "from" and "to" are DID strings, not identity objects.
 * - "timestamp" is the auth.timestamp value set during signing.
 * - All keys sorted alphabetically (Python sort_keys=True).
 *
 * The golden fixture at tests/conformance/golden/signature.json defines
 * the expected HMAC for fixed inputs — any compliant SDK must match it.
 */
function canonicalize(message: ROARMessage, authTimestamp: number): string {
  const obj = {
    context: message.context,
    from: message.from_identity.did,
    id: message.id,
    intent: message.intent,
    payload: message.payload,
    timestamp: authTimestamp,
    to: message.to_identity.did,
  };
  return pythonJsonDumps(obj);
}

/**
 * Python-compatible JSON serializer.
 *
 * Replicates `json.dumps(obj, sort_keys=True)` from Python's stdlib:
 * - Keys sorted alphabetically (recursive)
 * - Separator convention: `", "` between items, `": "` between key and value
 * - Numbers: integer-valued numbers get ".0" suffix to match Python float repr
 *
 * Limitation: Python distinguishes int (no decimal) from float (with .0).
 * TypeScript has only Number. We treat all numbers as Python floats — if a
 * payload contains Python int values, they will differ. For the signing body
 * this only matters for `timestamp`, which is always a float.
 */
function pythonJsonDumps(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "null";
    // Replicate Python float serialization: e.g. 1710000000.0 → "1710000000.0"
    if (Number.isInteger(value)) return `${value}.0`;
    return String(value);
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    return "[" + value.map(pythonJsonDumps).join(", ") + "]";
  }
  if (typeof value === "object" && value !== null) {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj).sort();
    if (keys.length === 0) return "{}";
    const pairs = keys.map(
      (k) => `${JSON.stringify(k)}: ${pythonJsonDumps(obj[k])}`,
    );
    return "{" + pairs.join(", ") + "}";
  }
  return String(value);
}

/**
 * Sign a ROAR message using HMAC-SHA256.
 *
 * Signature format: "hmac-sha256:<hex>" — matches Python exactly.
 *
 * @param message - The message to sign.
 * @param secret - The shared secret key.
 * @returns A new ROARMessage with the auth field populated.
 */
export function signMessage(message: ROARMessage, secret: string): ROARMessage {
  // auth.timestamp is part of the canonical body — set it before hashing.
  const authTimestamp = Date.now() / 1000;
  const body = canonicalize(message, authTimestamp);
  const hmac = crypto.createHmac("sha256", secret);
  hmac.update(body);
  const sig = hmac.digest("hex");
  return {
    ...message,
    auth: {
      signature: `hmac-sha256:${sig}`,
      signer: message.from_identity.did,
      timestamp: authTimestamp,
    },
  };
}

/**
 * Verify the HMAC-SHA256 signature on a ROAR message.
 *
 * @param message - The message to verify (must include auth.signature).
 * @param secret - The shared secret key.
 * @returns true if the signature is valid, false otherwise.
 */
export function verifyMessage(message: ROARMessage, secret: string): boolean {
  const sigValue = message.auth?.signature;
  if (typeof sigValue !== "string" || !sigValue.startsWith("hmac-sha256:")) {
    return false;
  }
  const authTimestamp = message.auth?.timestamp;
  if (typeof authTimestamp !== "number") {
    return false;
  }
  const expectedSig = (sigValue as string).split(":")[1];
  const body = canonicalize(message, authTimestamp);
  const hmac = crypto.createHmac("sha256", secret);
  hmac.update(body);
  const actualSig = hmac.digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(expectedSig, "hex"),
    Buffer.from(actualSig, "hex"),
  );
}
