# TORN — resilient journal protocol (v0.1)

An append-only file format where any corruption — a torn
record, a flipped byte, garbage in the middle — costs at most
one record, and the reader resynchronizes and reads on.

Designed for a real pain: JSONL/CSV die entirely from a
truncated tail record or a damaged sector.

## Format

A file is a sequence of records:

```
record  := MAGIC VER TYPE LEN PAYLOAD CRC
MAGIC   := 0xC7 0x3F                    (2 bytes)
VER     := 0x01                       (1 byte, format version)
TYPE    := 0x01 json | 0x02 raw        (1 byte)
LEN     := uint32 LE, PAYLOAD length   (4 bytes)
PAYLOAD := LEN bytes of data
CRC     := crc32(VER+TYPE+LEN+PAYLOAD) (4 bytes, uint32 LE)
```

Header — 8 bytes, whole record — 12 + LEN.

TYPE 0x01: payload is a UTF-8 JSON object (self-describing:
each record carries its own schema). TYPE 0x02: raw bytes —
semantics defined by the writer.

## Writer contract

- Appends to the tail only. Existing bytes are never changed —
  no editing, no rewriting.
- A record is written atomically from the format's view: if the
  writer dies mid-record, the tail is torn and the reader
  discards it cleanly. At most a half-written record is lost.

## Reader contract

1. Scans for MAGIC; on match, reads the header and CRC.
2. CRC matches — record is valid, emit it.
3. CRC mismatch or payload runs past EOF — resume scanning from
   the byte after the found MAGIC (a magic inside a payload
   simply fails CRC — resync is safe).
4. A torn tail (header present, data short) is a torn-tail:
   silently discard — it's a normal journal state, not an
   error.
5. The reader reports: `skipped` — corrupted bytes skipped,
   `torn_tail` — bytes of the torn tail.

## What the format does NOT do

- No dedup, no indexing, no compression — it's a journal,
  not a database.
- MAGIC is a resync heuristic, not cryptography. Malicious
  corruption is out of scope; bit-rot and truncation — yes,
  attacks — no.

## Why append-only

Non-rewriting is the price of resilience. Any in-file
modification would turn old offsets into lies; the journal is
honest because it only grows. History moves forward only.
