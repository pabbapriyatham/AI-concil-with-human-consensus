/** Preserve UTF-8 and frames split across network chunks. */
export async function consumeSSE(reader, onEvent) {
  const decoder = new TextDecoder();
  let buffer = '';
  let completed = false;
  function dispatch(frame) {
    const data = frame.split('\n').filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).trimStart()).join('\n');
    if (!data) return;
    const event = JSON.parse(data);
    onEvent(event.type, event);
    if (event.type === 'error') throw new Error(event.message || 'Stream failed');
    if (event.type === 'complete') completed = true;
  }
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, '\n');
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        dispatch(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
      }
      if (done) {
        if (buffer.trim()) dispatch(buffer);
        break;
      }
    }
    if (!completed) throw new Error('Stream ended before completion');
  } finally {
    reader.releaseLock();
  }
}
