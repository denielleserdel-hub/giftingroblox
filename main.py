from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import re
import traceback

app = FastAPI(title="Dr. Bytevoid's Cookie Refresher")
templates = Jinja2Templates(directory="templates")

DISCORD_WEBHOOK = ""  # leave empty or put your webhook

async def refresh_roblox_cookie(old_cookie: str):
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # Get X-CSRF-Token
            xsrf_resp = await client.post(
                "https://auth.roblox.com/v2/logout",
                headers={"Cookie": f".ROBLOSECURITY={old_cookie}"}
            )

            if "x-csrf-token" not in xsrf_resp.headers:
                return "❌ Invalid or expired cookie. Roblox rejected X-CSRF request."

            xcsrf = xsrf_resp.headers["x-csrf-token"]

            # Refresh
            refresh_resp = await client.post(
                "https://www.roblox.com/authentication/signoutfromallsessionsandreauthenticate",
                headers={
                    "X-CSRF-TOKEN": xcsrf,
                    "Cookie": f".ROBLOSECURITY={old_cookie}"
                }
            )

            if refresh_resp.status_code != 200:
                return f"❌ Roblox returned status {refresh_resp.status_code}. The cookie may be invalid or blocked."

            # Extract new cookie
            new_cookie = None
            for header in refresh_resp.headers.get_list("set-cookie") or [refresh_resp.headers.get("set-cookie")]:
                if header:
                    match = re.search(r'\.ROBLOSECURITY=([^;]+)', str(header))
                    if match:
                        new_cookie = match.group(1)
                        break

            if new_cookie:
                return f"✅ SUCCESS!\n\nAll other sessions logged out.\n\nNew .ROBLOSECURITY:\n\n{new_cookie}\n\nCopy it quickly!"

            return "⚠️ Refresh done but no new cookie returned (common in 2026).\nLog out completely on Roblox website, log back in, and grab a fresh cookie."

    except Exception as e:
        error_trace = traceback.format_exc()
        print("=== REFRESH ERROR ===")
        print(error_trace)
        return f"❌ Unexpected error: {str(e)}\n\nCheck the terminal below for full details."

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post("/refresh", response_class=HTMLResponse)
async def refresh(request: Request, cookie: str = Form(...)):
    result = await refresh_roblox_cookie(cookie.strip())
    return templates.TemplateResponse("index.html", {"request": request, "result": result})

if __name__ == "__main__":
    import uvicorn
    print("🚀 Dr. Bytevoid's Cookie Refresher running at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)