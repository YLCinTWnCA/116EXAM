# NVIDIA NIM CORS Proxy (Cloudflare Worker)

把 NVIDIA NIM (`integrate.api.nvidia.com/v1/chat/completions`) 包一層 CORS,
讓 GitHub Pages 上的靜態 web app(116EXAM)能直接從瀏覽器呼叫。

## 部署方式

### 在 Cloudflare 端

1. 登入 https://dash.cloudflare.com → Workers & Pages → **Create**
2. 點 **Connect to Git** → 授權 GitHub → 選 `YLCinTWnCA/116EXAM`
3. 設定:
   - **Project name:** `nvidia-nim-proxy`(會變成 `https://nvidia-nim-proxy.<your-user>.workers.dev`)
   - **Production branch:** `main`
   - **Build command:** 留空
   - **Deploy command:** 留空(或 `npx wrangler deploy`)
   - **Root directory:** `worker`
4. **Save and Deploy**

部署完成後會給你一個 URL。

### 在 116EXAM app 端

1. 打開 https://ylcintwnca.github.io/116EXAM/
2. 「📝 題目練習」→「⚙️ AI 設定」
3. **Endpoint** 選「其他...」→ 貼上 Worker 部署 URL(例如 `https://nvidia-nim-proxy.foo.workers.dev`)
4. **Model** 選「其他...」→ 輸入 `nvidia/llama-3.1-nemotron-70b-instruct`(或其他 NVIDIA NIM 模型 id)
5. **Key** 貼 NVIDIA 的 `nvapi-...`(到 build.nvidia.com → API Keys 取得)
6. 儲存

## 安全注意

- Worker 不會記錄你的 key,但 Cloudflare 平台本身可能有 access log
- key 只在瀏覽器 → Worker → NVIDIA 的傳輸過程中經過 Cloudflare 邊緣節點
- 個人用沒問題,正式產品建議把 key 設成 Worker secret,不要從 client header 帶
