export const runtime = 'nodejs';

export async function POST(req: Request) {
  let body: any = {};
  try {
    body = await req.json();
  } catch {}
  const connectionRequestId = body?.connectionRequestId || '';

  const serverBase = process.env.PY_SERVER_URL || 'http://localhost:8001';
  const url = `${serverBase.replace(/\/$/, '')}/api/v2/gmail/status`;

  // Forward Authorization header from client
  const authHeader = req.headers.get('Authorization');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }

  const payload: any = {};
  if (connectionRequestId) payload.connection_request_id = connectionRequestId;

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    const data = await resp.json().catch(() => ({}));
    return new Response(JSON.stringify(data), {
      status: resp.status,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    });
  } catch (e: any) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Upstream error', detail: e?.message || String(e) }),
      { status: 502, headers: { 'Content-Type': 'application/json; charset=utf-8' } }
    );
  }
}

export async function GET(req: Request) {
  const serverBase = process.env.PY_SERVER_URL || 'http://localhost:8001';
  const url = `${serverBase.replace(/\/$/, '')}/api/v2/gmail/status`;

  // Forward Authorization header from client
  const authHeader = req.headers.get('Authorization');
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }

  try {
    const resp = await fetch(url, { method: 'GET', headers });
    const data = await resp.json().catch(() => ({}));
    return new Response(JSON.stringify(data), {
      status: resp.status,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    });
  } catch (e: any) {
    return new Response(
      JSON.stringify({ ok: false, error: 'Upstream error', detail: e?.message || String(e) }),
      { status: 502, headers: { 'Content-Type': 'application/json; charset=utf-8' } }
    );
  }
}
