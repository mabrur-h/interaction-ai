const serverBase = process.env.PY_SERVER_URL || 'http://localhost:8001';
// Use V2 API endpoint with authentication
const historyPath = `${serverBase.replace(/\/$/, '')}/api/v2/chat/history`;

async function forward(method: 'GET' | 'DELETE', req: Request) {
  // Forward authorization header from client
  const authHeader = req.headers.get('Authorization');
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (authHeader) {
    headers['Authorization'] = authHeader;
  }

  try {
    const res = await fetch(historyPath, {
      method,
      headers,
      cache: 'no-store',
    });

    const bodyText = await res.text();
    const responseHeaders = new Headers({ 'Content-Type': 'application/json; charset=utf-8' });
    return new Response(bodyText || '{}', { status: res.status, headers: responseHeaders });
  } catch (error: any) {
    const message = error?.message || 'Failed to reach Python server';
    return new Response(JSON.stringify({ error: message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    });
  }
}

export async function GET(req: Request) {
  return forward('GET', req);
}

export async function DELETE(req: Request) {
  return forward('DELETE', req);
}
