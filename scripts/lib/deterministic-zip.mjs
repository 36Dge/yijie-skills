const DOS_DATE_1980_01_01 = 0x0021;
const UTF8_FLAG = 0x0800;

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function localHeader(name, content) {
  const nameBytes = Buffer.from(name, "utf8");
  const header = Buffer.alloc(30);
  header.writeUInt32LE(0x04034b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(UTF8_FLAG, 6);
  header.writeUInt16LE(0, 8);
  header.writeUInt16LE(0, 10);
  header.writeUInt16LE(DOS_DATE_1980_01_01, 12);
  header.writeUInt32LE(crc32(content), 14);
  header.writeUInt32LE(content.length, 18);
  header.writeUInt32LE(content.length, 22);
  header.writeUInt16LE(nameBytes.length, 26);
  return Buffer.concat([header, nameBytes, content]);
}

function centralHeader(name, content, offset) {
  const nameBytes = Buffer.from(name, "utf8");
  const header = Buffer.alloc(46);
  header.writeUInt32LE(0x02014b50, 0);
  header.writeUInt16LE(0x0314, 4);
  header.writeUInt16LE(20, 6);
  header.writeUInt16LE(UTF8_FLAG, 8);
  header.writeUInt16LE(0, 10);
  header.writeUInt16LE(0, 12);
  header.writeUInt16LE(DOS_DATE_1980_01_01, 14);
  header.writeUInt32LE(crc32(content), 16);
  header.writeUInt32LE(content.length, 20);
  header.writeUInt32LE(content.length, 24);
  header.writeUInt16LE(nameBytes.length, 28);
  header.writeUInt32LE(0x81a40000, 38);
  header.writeUInt32LE(offset, 42);
  return Buffer.concat([header, nameBytes]);
}

function endOfCentralDirectory(entryCount, centralSize, centralOffset) {
  const record = Buffer.alloc(22);
  record.writeUInt32LE(0x06054b50, 0);
  record.writeUInt16LE(entryCount, 8);
  record.writeUInt16LE(entryCount, 10);
  record.writeUInt32LE(centralSize, 12);
  record.writeUInt32LE(centralOffset, 16);
  return record;
}

export function createStoredZip(entries) {
  const normalized = [...entries]
    .map(({ name, content }) => ({ name, content: Buffer.from(content) }))
    .sort((left, right) => Buffer.from(left.name).compare(Buffer.from(right.name)));
  const seen = new Set();
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const entry of normalized) {
    if (!isSafeRelativePath(entry.name)) throw new Error(`Unsafe archive entry: ${entry.name}`);
    const folded = entry.name.toLocaleLowerCase("en-US");
    if (seen.has(folded)) throw new Error(`Duplicate archive entry: ${entry.name}`);
    seen.add(folded);
    const local = localHeader(entry.name, entry.content);
    localParts.push(local);
    centralParts.push(centralHeader(entry.name, entry.content, offset));
    offset += local.length;
  }
  if (normalized.length === 0) throw new Error("Cannot create an empty Skill archive");

  const central = Buffer.concat(centralParts);
  return Buffer.concat([
    ...localParts,
    central,
    endOfCentralDirectory(normalized.length, central.length, offset),
  ]);
}

export function isSafeRelativePath(name) {
  if (name.length === 0 || name.startsWith("/") || name.includes("\\") || name.includes("\0")) {
    return false;
  }
  return !name.split("/").some((segment) => segment === "" || segment === "." || segment === "..");
}
