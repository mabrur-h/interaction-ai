export const runtime = 'nodejs';

type UIMsgPart = { type: string; text?: string };
type UIMessage = { role: string; parts?: UIMsgPart[]; content?: string };

function uiToOpenAIContent(messages: UIMessage[]): { role: string; content: string }[] {
  const out: { role: string; content: string }[] = [];
  for (const m of messages || []) {
    const role = m?.role;
    if (!role) continue;
    let content = '';
    if (Array.isArray(m.parts)) {
      content = m.parts.filter((p) => p?.type === 'text').map((p) => p.text || '').join('');
    } else if (typeof m.content === 'string') {
      content = m.content;
    }
    out.push({ role, content });
  }
  return out;
}

export async function POST(req: Request) {
  let body: any;
  try {
    body = await req.json();
  } catch (e) {
    console.error('[chat-proxy] invalid json', e);
    return new Response('Invalid JSON', { status: 400 });
  }

  const { messages } = body || {};
  if (!Array.isArray(messages) || messages.length === 0) {
    return new Response('Missing messages', { status: 400 });
  }

  const serverBase = process.env.PY_SERVER_URL || 'http://localhost:8001';
  // Use V2 API endpoint with authentication
  const serverPath = '/api/v2/chat/send';
  const url = `${serverBase.replace(/\/$/, '')}${serverPath}`;

  const payload = {
    system: '',
    messages: uiToOpenAIContent(messages),
    stream: false,
  };

  // Forward authorization header from client
  const authHeader = req.headers.get('Authorization');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/plain, */*',
  };
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }

  try {
    const upstream = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  } catch (e: any) {
    console.error('[chat-proxy] upstream error', e);
    return new Response(e?.message || 'Upstream error', { status: 502 });
  }
}
