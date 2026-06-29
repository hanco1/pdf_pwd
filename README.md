<p align="center">
  <strong>PDF Unlocker</strong>
</p>

<p align="center">
  Remove a known password from a PDF — or add one to protect it. Local-first, or one click on the web.<br>
  移除已知 PDF 密码，或反过来给 PDF 加密码保护。本地优先，也可一键在线使用。
</p>

<p align="center">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3.x-1A1A1A">
  <img alt="pypdf" src="https://img.shields.io/badge/pypdf-6.x-CD6F47">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-6B8A6F">
  <img alt="Deploy" src="https://img.shields.io/badge/Deploy-Vercel-1A1A1A">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-E5DFD2">
</p>

<p align="center">
  <a href="#english"><b>English</b></a>
  &nbsp;|&nbsp;
  <a href="#中文"><b>中文</b></a>
</p>

<p align="center">
  <a href="https://pdf-pwd.myboringtools.top"><b>🔓 Live demo / 在线体验</b></a>
</p>

![PDF Unlocker UI](screenshots/ui-safari-windows.png)

<a id="english"></a>

## 🇬🇧 English

### What it does / Why

Many PDFs carry an owner password that blocks editing, printing, copying, or form changes even when the document can be opened. PDF Unlocker removes those restrictions using a password you already know, then returns an unlocked copy that is easier to edit.

This is not a password cracker. It does not guess, brute-force, bypass, or recover unknown passwords. If the PDF requires a password, you must provide the correct one.

The app is local-first. When you run it yourself, files stay on your machine. The hosted version processes each upload in memory for a single request and stores nothing after the response is sent.

### ✨ Features

- **Two modes:** remove a known password, or add a new one (AES-256) to protect a PDF — switch with a tab.
- In-memory, single-request flow with no files stored by the app.
- Bilingual UI (English / 中文), show/hide password, drag-and-drop upload, confirm-password check.
- Preserves form fields, outlines, and metadata where the PDF structure allows it.
- Works with encrypted PDFs and unencrypted PDFs.
- Friendly error messages for missing files, invalid PDFs, wrong passwords, and file-size limits.
- Clean responsive UI with reduced-motion support.
- Deployable to Vercel or runnable locally with Flask.

### 🚀 Live demo

Primary demo:

[https://pdf-pwd.myboringtools.top](https://pdf-pwd.myboringtools.top)

Alternate Vercel URL:

[https://pdf-pwd-eight.vercel.app](https://pdf-pwd-eight.vercel.app)

Both URLs are live.

### 🖥️ Run locally

Use Windows PowerShell:

```powershell
git clone https://github.com/hanco1/pdf_pwd.git
cd pdf_pwd
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The local upload limit defaults to 4 MB. Raise it with the `MAX_MB` environment variable:

```powershell
$env:MAX_MB = "20"
python app.py
```

### ☁️ Deploy your own to Vercel

The project is ready for Vercel's Python runtime:

```text
api/index.py       exposes the Flask app
vercel.json        rewrites all routes to api/index.py
requirements.txt   triggers dependency installation for the Python runtime
```

Deploy flow:

1. Push this repository to GitHub.
2. Import the repository on [vercel.com](https://vercel.com), or deploy with the `vercel` CLI.
3. Keep the default build settings and deploy.

Vercel's hosted request-body limit is about 4.5 MB, so larger PDFs should be unlocked locally with a higher `MAX_MB` value.

### 📖 Usage

1. Choose a mode tab: **Remove password** or **Add password**.
2. Choose the PDF file.
3. Enter the current password for **Remove password**, or enter and confirm the new password for **Add password**.
4. Press **Unlock PDF** or **Protect PDF**.
5. Download the processed PDF when it completes.

### 🔌 API

The public API is stateless and in-memory, just like the web form. `GET /api` or `GET /api/v1` returns a JSON description of the available endpoints, parameters, limits, and examples.

- `POST /api/v1/unlock` removes a known password.
- `POST /api/v1/lock` adds an AES-256 password.
- Send `multipart/form-data` with a PDF field named `file` or `pdf`, plus `password`; this defaults to a binary PDF (`application/pdf`) attachment.
- Or send `application/json` with a base64 PDF in `file_base64` (aliases: `pdf_base64`, `file`, `data`), plus `password` and optional `filename`; this defaults to a JSON base64 response.
- Use `?output=base64` or `?output=binary` (also `?format=`) to override the default response format. Errors return JSON: `{"error": "...", "code": "..."}`.
- The hosted version has a roughly 4.5 MB request-size limit; run locally with a higher `MAX_MB` for larger PDFs.

```bash
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/unlock -F "file=@locked.pdf" -F "password=secret" -o unlocked.pdf
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/lock   -F "file=@doc.pdf"    -F "password=newsecret" -o protected.pdf
```

```python
import requests

base = "https://pdf-pwd.myboringtools.top"

with open("locked.pdf", "rb") as pdf:
    response = requests.post(
        f"{base}/api/v1/unlock",
        files={"file": pdf},
        data={"password": "secret"},
    )
response.raise_for_status()
open("unlocked.pdf", "wb").write(response.content)

with open("doc.pdf", "rb") as pdf:
    response = requests.post(
        f"{base}/api/v1/lock",
        files={"file": pdf},
        data={"password": "newsecret"},
    )
response.raise_for_status()
open("protected.pdf", "wb").write(response.content)
```

#### Automation / n8n

Two call styles are supported:

- Multipart binary: send a `file` or `pdf` field plus `password`; the default response is a binary PDF attachment.
- JSON base64: send `file_base64` plus `password`; the default response is `{"filename": "...", "pdf_base64": "...", "bytes": 123, "encrypted": true}`.

```bash
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/lock \
  -H "Content-Type: application/json" \
  -d '{"file_base64":"<BASE64_OF_PDF>","password":"secret"}'
```

In n8n, use an HTTP Request node with `POST`, the endpoint URL, and a JSON body. Set `file_base64` from the incoming binary data (for many n8n binary items this is `{{$binary.data.data}}`; otherwise use a Code/Convert node to base64-encode the prior node's binary), and set `password`. The response `pdf_base64` can be converted back into binary downstream with a Code/Convert node. The hosted request body limit is about 4.5 MB; base64 inflates size by about 33%, so the practical PDF maximum is a bit smaller when using JSON.

### 🔒 Security & limits

- You must know the password. PDF Unlocker is not a cracker and does not recover unknown passwords.
- The hosted version is stateless and in-memory; it stores no uploaded PDFs or unlocked outputs.
- The web form and API are unauthenticated, stateless transforms: input PDF in, output PDF out, nothing stored. That is why there is no login or CSRF token.
- The hosted deployment is limited by Vercel's request-body size, roughly 4.5 MB.
- For sensitive documents or larger files, run the app locally so the PDF never leaves your machine.

### 🛠️ Tech stack

- Flask
- pypdf
- Vanilla HTML/CSS/JS in a single-file app
- Vercel Python serverless runtime

### 📄 License

MIT.

<p align="center"><a href="#english">English</a> | <a href="#中文">中文</a></p>

<a id="中文"></a>

## 🇨🇳 中文

### 它能做什么 / 为什么需要

很多 PDF 带有“所有者密码”，会限制编辑、打印、复制或表单修改，即使文件本身可以打开也无法顺利编辑。PDF Unlocker 使用你已经知道的密码移除这些限制，并返回一份便于编辑的解锁副本。

它不是密码破解工具。它不会猜测、暴力破解、绕过或找回未知密码。如果 PDF 需要密码，你必须输入正确密码。

这个项目本地优先。自行运行时，文件不会离开你的电脑。托管版本会在每次请求中以内存方式处理上传文件，响应结束后不保存任何文件。

### ✨ 功能

- **两种模式：** 移除已知密码，或给 PDF 添加新密码（AES-256）保护 —— 顶部一键切换。
- 单次请求内存处理流程，应用不存储任何文件。
- 中英文双语界面、密码显示/隐藏、拖拽上传、确认密码校验。
- 在 PDF 结构允许的情况下保留表单字段、书签大纲和元数据。
- 支持已加密和未加密 PDF。
- 对缺少文件、无效 PDF、密码错误、文件大小超限等情况提供友好的错误提示。
- 干净的响应式界面，并支持减少动态效果偏好。
- 可部署到 Vercel，也可用 Flask 在本地运行。

### 🚀 在线体验

主链接：

[https://pdf-pwd.myboringtools.top](https://pdf-pwd.myboringtools.top)

备用 Vercel 链接：

[https://pdf-pwd-eight.vercel.app](https://pdf-pwd-eight.vercel.app)

两个链接均已生效，可直接访问。

### 🖥️ 本地运行

使用 Windows PowerShell：

```powershell
git clone https://github.com/hanco1/pdf_pwd.git
cd pdf_pwd
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

然后打开：

```text
http://127.0.0.1:5000
```

本地上传大小默认限制为 4 MB。可以通过 `MAX_MB` 环境变量调高：

```powershell
$env:MAX_MB = "20"
python app.py
```

### ☁️ 部署到你自己的 Vercel

项目已按 Vercel Python Runtime 的方式组织：

```text
api/index.py       暴露 Flask app
vercel.json        将所有路径重写到 api/index.py
requirements.txt   触发 Python Runtime 安装依赖
```

部署步骤：

1. 将仓库推送到 GitHub。
2. 在 [vercel.com](https://vercel.com) 导入仓库，或使用 `vercel` CLI 部署。
3. 保持默认构建设置并部署。

Vercel 托管环境的请求体大小限制约为 4.5 MB，因此更大的 PDF 建议在本地解锁，并按需调高 `MAX_MB`。

### 📖 使用方法

1. 选择模式标签：**Remove password**（移除密码）或 **Add password**（添加密码）。
2. 选择 PDF 文件。
3. 移除密码模式输入当前密码；添加密码模式输入新密码并再次确认。
4. 点击 **Unlock PDF** 或 **Protect PDF**。
5. 处理完成后下载新的 PDF。

### 🔌 API

公开 API 和网页表单一样，都是无状态、纯内存处理。`GET /api` 或 `GET /api/v1` 会返回 JSON，说明可用端点、参数、限制和示例。

- `POST /api/v1/unlock`：移除已知密码。
- `POST /api/v1/lock`：添加 AES-256 密码保护。
- 使用 `multipart/form-data` 上传，PDF 字段名可以是 `file` 或 `pdf`，密码字段为 `password`；默认返回二进制 PDF（`application/pdf`）附件。
- 也可以使用 `application/json`，把 base64 PDF 放在 `file_base64`（别名：`pdf_base64`、`file`、`data`），并传入 `password` 和可选 `filename`；默认返回 JSON base64。
- 使用 `?output=base64` 或 `?output=binary`（也支持 `?format=`）覆盖默认输出格式。失败时返回 JSON：`{"error": "...", "code": "..."}`。
- 托管版本请求大小限制约为 4.5 MB；更大的 PDF 建议本地运行，并按需调高 `MAX_MB`。

```bash
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/unlock -F "file=@locked.pdf" -F "password=secret" -o unlocked.pdf
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/lock   -F "file=@doc.pdf"    -F "password=newsecret" -o protected.pdf
```

```python
import requests

base = "https://pdf-pwd.myboringtools.top"

with open("locked.pdf", "rb") as pdf:
    response = requests.post(
        f"{base}/api/v1/unlock",
        files={"file": pdf},
        data={"password": "secret"},
    )
response.raise_for_status()
open("unlocked.pdf", "wb").write(response.content)

with open("doc.pdf", "rb") as pdf:
    response = requests.post(
        f"{base}/api/v1/lock",
        files={"file": pdf},
        data={"password": "newsecret"},
    )
response.raise_for_status()
open("protected.pdf", "wb").write(response.content)
```

#### Automation / n8n

支持两种调用方式：

- multipart 二进制：发送 `file` 或 `pdf` 字段和 `password`；默认返回二进制 PDF 附件。
- JSON base64：发送 `file_base64` 和 `password`；默认返回 `{"filename": "...", "pdf_base64": "...", "bytes": 123, "encrypted": true}`。

```bash
curl -X POST https://pdf-pwd.myboringtools.top/api/v1/lock \
  -H "Content-Type: application/json" \
  -d '{"file_base64":"<BASE64_OF_PDF>","password":"secret"}'
```

在 n8n 中，用 HTTP Request 节点：方法选 `POST`，URL 填对应端点，Body 选 JSON。把 `file_base64` 设为上游节点的二进制内容（很多 n8n 二进制项可用 `{{$binary.data.data}}`；否则用 Code/Convert 节点先把上游 binary 转成 base64），并设置 `password`。响应里的 `pdf_base64` 可以在下游用 Code/Convert 节点再转回 binary。托管版请求体限制约 4.5 MB；base64 会让体积增加约 33%，所以 JSON 方式下实际可处理的 PDF 会更小一点。

### 🔒 安全与限制

- 你必须知道密码。PDF Unlocker 不是破解工具，也不会找回未知密码。
- 托管版本无状态、以内存方式处理文件；不会保存上传的 PDF 或解锁结果。
- 网页表单和 API 都是不需要登录的无状态转换：输入 PDF，输出 PDF，不存储任何内容。因此没有登录流程，也没有 CSRF token。
- 托管部署受 Vercel 请求体大小限制影响，约为 4.5 MB。
- 对于敏感文件或大文件，建议在本地运行，确保 PDF 不离开你的电脑。

### 🛠️ 技术栈

- Flask
- pypdf
- 原生 HTML/CSS/JS，单文件应用结构
- Vercel Python Serverless Runtime

### 📄 许可证

MIT。

<p align="center"><a href="#english">English</a> | <a href="#中文">中文</a></p>
