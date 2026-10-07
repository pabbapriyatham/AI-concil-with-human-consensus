import { test } from 'node:test';
import assert from 'node:assert/strict';
import { consumeSSE } from '../src/sse.js';

test('SSE handles split JSON, delimiters and UTF-8 bytes', async () => {
  const bytes = new TextEncoder().encode('data: {"type":"stage1_complete","data":"été"}\r\n\r\ndata: {"type":"complete"}\n\n');
  let offset = 0;
  const reader = { async read() { return offset === bytes.length ? { done: true } : { done: false, value: bytes.slice(offset, ++offset) }; }, releaseLock() {} };
  const events = [];
  await consumeSSE(reader, (type, value) => events.push([type, value.data]));
  assert.deepEqual(events, [['stage1_complete', 'été'], ['complete', undefined]]);
});

test('SSE rejects incomplete execution', async () => {
  const reader = { async read() { return { done: true }; }, releaseLock() {} };
  await assert.rejects(consumeSSE(reader, () => {}), /before completion/);
});
