// NVIDIA NIM CORS Proxy — Cloudflare Worker
// 把瀏覽器叫不到的 NVIDIA NIM endpoint 轉一層,加上 CORS headers。
// 部署後 URL 長這樣:https://nvidia-nim-proxy.<你的cf-username>.workers.dev

const UPSTREAM = "https://integrate.api.nvidia.com/v1/chat/completions";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Max-Age": "86400"
};

export default {
  async fetch(request) {
    // 處理 preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (request.method !== "POST") {
      return new Response("Only POST allowed", { status: 405, headers: CORS_HEADERS });
    }

    // 把瀏覽器送來的 Authorization 跟 body 原樣轉給 NVIDIA NIM
    const auth = request.headers.get("Authorization") || "";
    if (!auth) {
      return new Response(JSON.stringify({ error: "Missing Authorization header" }),
        { status: 401, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } });
    }

    const body = await request.text();

    try {
      const upstream = await fetch(UPSTREAM, {
        method: "POST",
        headers: {
          "Authorization": auth,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body
      });

      const respBody = await upstream.text();
      return new Response(respBody, {
        status: upstream.status,
        headers: {
          ...CORS_HEADERS,
          "Content-Type": "application/json"
        }
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: "Upstream fetch failed", detail: err.message }),
        { status: 502, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } });
    }
  }
};
