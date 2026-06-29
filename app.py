import io
import os

from flask import Flask, render_template_string, request, send_file
from pypdf import PdfReader, PdfWriter
from pypdf.errors import EmptyFileError, PdfReadError, PdfStreamError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

MAX_MB = int(os.environ.get("MAX_MB", "4"))
# Vercel sets VERCEL=1 on its serverless runtime. Use it so the UI copy can
# describe the hosted reality (in-memory, nothing stored) vs. a local run.
IS_HOSTED = bool(os.environ.get("VERCEL"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

TEMPLATE = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>PDF Unlocker</title>
    <link rel="icon" href="data:," />
    <style>
      :root {
        --bg-1: #f8f1e8;
        --bg-2: #ead4c1;
        --bg-3: #d8e6ec;
        --ink: #1e1b18;
        --muted: #5f554c;
        --accent: #1f7a8c;
        --accent-2: #c8653a;
        --card: #fff7ef;
        --stroke: rgba(31, 122, 140, 0.2);
        --shadow: rgba(31, 60, 75, 0.18);
        --font-display: "Constantia", "Palatino Linotype", "Book Antiqua", serif;
        --font-body: "Candara", "Trebuchet MS", "Geneva", sans-serif;
      }

      * {
        box-sizing: border-box;
      }

      [hidden] {
        display: none !important;
      }

      button,
      input {
        font: inherit;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: var(--font-body);
        color: var(--ink);
        background: radial-gradient(circle at 15% 20%, rgba(200, 101, 58, 0.15), transparent 45%),
          radial-gradient(circle at 85% 15%, rgba(31, 122, 140, 0.18), transparent 50%),
          linear-gradient(135deg, var(--bg-1), var(--bg-2) 45%, var(--bg-3));
      }

      .page {
        max-width: 980px;
        margin: 0 auto;
        padding: 40px 24px 64px;
        position: relative;
      }

      .page::before,
      .page::after {
        content: "";
        position: absolute;
        border-radius: 999px;
        filter: blur(0);
        opacity: 0.6;
        z-index: 0;
        animation: float 18s ease-in-out infinite;
      }

      .page::before {
        width: 260px;
        height: 260px;
        background: rgba(31, 122, 140, 0.18);
        top: 20px;
        right: 40px;
      }

      .page::after {
        width: 200px;
        height: 200px;
        background: rgba(200, 101, 58, 0.18);
        bottom: 40px;
        left: 20px;
        animation-delay: -6s;
      }

      header {
        position: relative;
        z-index: 1;
        display: grid;
        gap: 12px;
        margin-bottom: 24px;
        animation: rise 0.7s ease-out both;
      }

      .badge {
        align-self: flex-start;
        background: rgba(31, 122, 140, 0.15);
        color: var(--accent);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 12px;
        padding: 6px 12px;
        border-radius: 999px;
      }

      h1 {
        margin: 0;
        font-family: var(--font-display);
        font-size: clamp(32px, 6vw, 56px);
        letter-spacing: 0.02em;
      }

      header p {
        margin: 0;
        color: var(--muted);
        font-size: 17px;
        max-width: 680px;
      }

      .header-top {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: flex-start;
      }

      .language-switcher {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.56);
        border: 1px solid rgba(31, 122, 140, 0.18);
      }

      .lang-button {
        min-width: 44px;
        min-height: 36px;
        border: 0;
        border-radius: 999px;
        color: var(--muted);
        background: transparent;
        cursor: pointer;
        font-weight: 800;
      }

      .lang-button[aria-pressed="true"] {
        color: white;
        background: var(--accent);
      }

      .panel {
        position: relative;
        z-index: 1;
        background: var(--card);
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 24px 60px var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.6);
        display: grid;
        gap: 24px;
        animation: rise 0.9s ease-out both;
        animation-delay: 0.1s;
      }

      .panel-grid {
        display: grid;
        gap: 24px;
        grid-template-columns: minmax(0, 0.82fr) minmax(320px, 1fr);
        align-items: start;
      }

      h2 {
        margin: 0 0 12px;
        font-family: var(--font-display);
        font-size: clamp(24px, 4vw, 34px);
      }

      .step-list {
        margin: 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.6;
      }

      .form-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(31, 122, 140, 0.18);
        display: grid;
        gap: 16px;
      }

      #unlock-form {
        display: grid;
        gap: 18px;
      }

      .mode-tabs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        padding: 6px;
        border-radius: 999px;
        background: rgba(31, 122, 140, 0.1);
        border: 1px solid rgba(31, 122, 140, 0.16);
      }

      .mode-tab {
        min-height: 46px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--accent);
        cursor: pointer;
        font-weight: 800;
        transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
      }

      .mode-tab[aria-selected="true"] {
        background: var(--accent);
        color: white;
        box-shadow: 0 12px 24px rgba(31, 122, 140, 0.26);
      }

      .field {
        display: grid;
        gap: 8px;
      }

      label {
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.02em;
        color: var(--muted);
      }

      .drop-zone {
        border: 2px dashed rgba(31, 122, 140, 0.38);
        border-radius: 18px;
        padding: 16px;
        background: rgba(248, 241, 232, 0.72);
        transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
      }

      .drop-zone.is-dragover {
        border-color: var(--accent-2);
        background: rgba(200, 101, 58, 0.12);
        transform: translateY(-1px);
      }

      .file-row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }

      input[type="file"] {
        position: absolute;
        left: -9999px;
      }

      .file-button {
        border: 2px dashed var(--accent);
        padding: 12px 18px;
        border-radius: 14px;
        cursor: pointer;
        font-weight: 700;
        color: var(--accent);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }

      .drop-zone .file-button {
        border-style: solid;
        background: white;
        min-height: 44px;
        display: inline-flex;
        align-items: center;
      }

      .file-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 20px rgba(31, 122, 140, 0.18);
      }

      .file-name {
        font-size: 14px;
        color: var(--muted);
      }

      .file-meta {
        display: grid;
        gap: 2px;
        min-width: 0;
      }

      .file-size {
        color: var(--muted);
        font-size: 12px;
      }

      .clear-file {
        min-height: 44px;
        border: 0;
        border-radius: 999px;
        background: rgba(200, 101, 58, 0.12);
        color: var(--accent-2);
        cursor: pointer;
        font-weight: 800;
        padding: 0 14px;
      }

      .password-shell {
        position: relative;
      }

      .password-input,
      input[type="password"] {
        width: 100%;
        min-height: 48px;
        padding: 12px 52px 12px 14px;
        border-radius: 12px;
        border: 1px solid rgba(31, 122, 140, 0.3);
        font-family: var(--font-body);
        font-size: 16px; /* >=16px stops iOS Safari from auto-zooming on focus */
      }

      .password-toggle {
        position: absolute;
        top: 50%;
        right: 6px;
        width: 40px;
        height: 40px;
        transform: translateY(-50%);
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--accent);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }

      .password-toggle svg {
        width: 20px;
        height: 20px;
        stroke: currentColor;
        stroke-width: 1.8;
        fill: none;
      }

      .helper,
      .field-error {
        margin: 0;
        font-size: 13px;
        line-height: 1.4;
      }

      .helper {
        color: var(--muted);
      }

      .field-error {
        color: #9b3f23;
        font-weight: 800;
      }

      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 6px;
      }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 46px;
        padding: 12px 20px;
        border-radius: 999px;
        border: none;
        font-weight: 700;
        text-decoration: none;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        font-family: var(--font-body);
      }

      .btn.primary {
        background: var(--accent);
        color: white;
        box-shadow: 0 14px 26px rgba(31, 122, 140, 0.28);
      }

      .btn.secondary {
        background: rgba(31, 122, 140, 0.1);
        color: var(--accent);
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        box-shadow: none;
      }

      .btn:hover:not(:disabled) {
        transform: translateY(-1px);
      }

      .btn:focus-visible,
      .clear-file:focus-visible,
      .file-button:focus-visible,
      .lang-button:focus-visible,
      .mode-tab:focus-visible,
      .password-toggle:focus-visible,
      input:focus-visible {
        outline: 3px solid rgba(200, 101, 58, 0.55);
        outline-offset: 3px;
      }

      .status {
        border-radius: 16px;
        padding: 16px;
        border: 1px solid transparent;
        display: grid;
        gap: 8px;
      }

      .status.success {
        background: rgba(31, 122, 140, 0.12);
        border-color: rgba(31, 122, 140, 0.3);
      }

      .status.error {
        background: rgba(200, 101, 58, 0.16);
        border-color: rgba(200, 101, 58, 0.4);
      }

      .status.info {
        background: rgba(52, 67, 88, 0.12);
        border-color: rgba(52, 67, 88, 0.3);
      }

      .status-title {
        font-weight: 800;
        letter-spacing: 0.02em;
      }

      .note {
        font-size: 13px;
        color: var(--muted);
        margin: 0;
      }

      footer {
        margin-top: 20px;
        color: var(--muted);
        font-size: 13px;
      }

      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }

      .loading .btn.primary {
        opacity: 0.7;
      }

      .loading .btn.primary::after {
        content: "  ";
      }

      .loading .btn.primary span::after {
        content: "";
        font-weight: 600;
      }

      @keyframes rise {
        from {
          opacity: 0;
          transform: translateY(18px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes float {
        0%,
        100% {
          transform: translateY(0) translateX(0);
        }
        50% {
          transform: translateY(-14px) translateX(6px);
        }
      }

      @media (max-width: 600px) {
        .page {
          padding: calc(18px + env(safe-area-inset-top)) calc(16px + env(safe-area-inset-right))
            calc(40px + env(safe-area-inset-bottom)) calc(16px + env(safe-area-inset-left));
        }

        h1 {
          font-size: clamp(30px, 9vw, 44px);
        }

        .header-top {
          flex-direction: row;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 10px;
        }

        .panel {
          padding: 18px;
          border-radius: 22px;
        }

        .panel-grid,
        .mode-tabs {
          grid-template-columns: 1fr;
        }

        .file-row {
          flex-direction: column;
          align-items: flex-start;
        }

        .actions {
          flex-direction: column;
          align-items: stretch;
        }

        .actions .btn {
          width: 100%;
        }
      }

      /* Touch devices — iPhone, iPad, Android (works even when iPad sends a desktop UA) */
      @media (pointer: coarse) {
        .lang-button,
        .password-toggle,
        .file-button,
        .clear-file,
        .mode-tab,
        .btn {
          min-height: 44px;
        }

        .password-toggle {
          width: 44px;
        }

        .btn:hover:not(:disabled),
        .file-button:hover,
        .mode-tab:hover {
          transform: none;
        }
      }

      /* Server-detected mobile (iPhone/Android UA): drop the heavy decorative blobs */
      body.is-mobile .page::before,
      body.is-mobile .page::after {
        display: none;
      }

      @media (prefers-reduced-motion: reduce) {
        * {
          animation: none !important;
          transition: none !important;
        }
      }
    </style>
      </head>
  <body class="{{ 'is-mobile' if is_mobile else '' }}">
    <div class="page">
      <header>
        <div class="header-top">
          <div class="badge" data-i18n="badge">{{ "Online · in-memory" if is_hosted else "Local · private" }}</div>
          <div class="language-switcher" aria-label="Language">
            <button class="lang-button" type="button" data-lang="en" aria-pressed="true">EN</button>
            <button class="lang-button" type="button" data-lang="zh" aria-pressed="false">中文</button>
          </div>
        </div>
        <h1>PDF Unlocker</h1>
        <p data-i18n="intro">Remove a known PDF password, or add a new one, without storing files on disk.</p>
      </header>

      <section class="panel">
        <div class="panel-grid">
          <div>
            <h2 data-i18n="howTitle">How it works</h2>
            <ol class="step-list" id="steps-list">
              <li data-step="0">Choose the locked PDF.</li>
              <li data-step="1">Enter the current password if it has one.</li>
              <li data-step="2">Download the unlocked copy.</li>
            </ol>
          </div>
          <div class="form-card">
            <form id="unlock-form" method="post" action="/process" enctype="multipart/form-data" novalidate>
              <input id="mode-field" name="mode" type="hidden" value="{{ initial_mode }}" />

              <div class="mode-tabs" role="tablist" aria-label="PDF mode">
                <button class="mode-tab" id="tab-unlock" type="button" role="tab" data-mode="unlock" aria-selected="{{ 'true' if initial_mode == 'unlock' else 'false' }}" aria-controls="mode-panel" data-i18n="modeUnlock">🔓 Remove password</button>
                <button class="mode-tab" id="tab-lock" type="button" role="tab" data-mode="lock" aria-selected="{{ 'true' if initial_mode == 'lock' else 'false' }}" aria-controls="mode-panel" data-i18n="modeLock">🔒 Add password</button>
              </div>
              <div class="sr-only" id="mode-announcer" aria-live="polite"></div>

              <div class="field">
                <label for="pdf" data-i18n="fileLabel">PDF file</label>
                <div class="drop-zone" id="drop-zone">
                  <input id="pdf" name="pdf" type="file" accept="application/pdf" required />
                  <div class="file-row">
                    <button class="file-button" id="file-button" type="button" data-i18n="upload">Upload PDF</button>
                    <div class="file-meta">
                      <span class="file-name" id="file-name" data-i18n="noFile">No file selected</span>
                      <span class="file-size" id="file-size"></span>
                    </div>
                    <button class="clear-file" id="clear-file" type="button" hidden data-i18n="clearFile">Clear file</button>
                  </div>
                </div>
              </div>

              <div class="field" id="mode-panel">
                <label for="password" id="password-label">PDF password</label>
                <div class="password-shell">
                  <input class="password-input" id="password" name="password" type="password" placeholder="Enter the current PDF password" autocomplete="current-password" aria-describedby="password-helper mismatch-message" />
                  <button class="password-toggle" type="button" data-toggle-password="password" aria-label="Show password" aria-pressed="false">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  </button>
                </div>
                <p class="helper" id="password-helper">Leave blank if the PDF opens without a password.</p>
              </div>

              <div class="field" id="confirm-field" {% if initial_mode != "lock" %}hidden{% endif %}>
                <label for="confirm-password" id="confirm-label">Confirm password</label>
                <div class="password-shell">
                  <input class="password-input" id="confirm-password" name="confirm_password" type="password" placeholder="Re-enter the new password" autocomplete="new-password" aria-describedby="confirm-helper mismatch-message" />
                  <button class="password-toggle" type="button" data-toggle-password="confirm-password" aria-label="Show password" aria-pressed="false">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  </button>
                </div>
                <p class="helper" id="confirm-helper">Both entries must match before protecting the PDF.</p>
              </div>
              <p class="field-error" id="mismatch-message" role="alert" aria-live="polite" hidden>Passwords do not match.</p>

              <div class="actions">
                <button class="btn primary" id="process-btn" type="submit" disabled><span id="process-label">Unlock PDF</span></button>
                <button class="btn secondary" type="button" id="reset-btn" data-i18n="clear">Clear</button>
              </div>
              <p class="note" id="limit-note" data-i18n="limitNote">{% if is_hosted %}Processed in memory and never stored. Up to {{ max_mb }} MB per file — run it locally for bigger ones. Only process PDFs you own or have rights to edit.{% else %}Files stay on your computer and are never uploaded. Only process PDFs you own or have rights to edit.{% endif %}</p>
            </form>
          </div>
        </div>

        {% if message %}
        <div class="status {{ status }}">
          <div class="status-title">{{ status_title }}</div>
          <div>{{ message }}</div>
        </div>
        {% endif %}
      </section>

      <footer data-i18n="footer">{% if is_hosted %}Hosted on Vercel · your PDF is processed in memory and never stored. Open source — run it locally to keep files fully offline.{% else %}Running locally · your PDFs never leave this computer. Built with Flask + pypdf.{% endif %}</footer>
    </div>
    <script>
      const fileInput = document.getElementById("pdf");
      const fileName = document.getElementById("file-name");
      const fileSize = document.getElementById("file-size");
      const fileButton = document.getElementById("file-button");
      const clearFileButton = document.getElementById("clear-file");
      const dropZone = document.getElementById("drop-zone");
      const modeInput = document.getElementById("mode-field");
      const modeTabs = Array.from(document.querySelectorAll(".mode-tab"));
      const modeAnnouncer = document.getElementById("mode-announcer");
      const passwordInput = document.getElementById("password");
      const confirmField = document.getElementById("confirm-field");
      const confirmInput = document.getElementById("confirm-password");
      const passwordLabel = document.getElementById("password-label");
      const passwordHelper = document.getElementById("password-helper");
      const confirmLabel = document.getElementById("confirm-label");
      const confirmHelper = document.getElementById("confirm-helper");
      const mismatchMessage = document.getElementById("mismatch-message");
      const processButton = document.getElementById("process-btn");
      const processLabel = document.getElementById("process-label");
      const resetButton = document.getElementById("reset-btn");
      const form = document.getElementById("unlock-form");
      const maxMb = "{{ max_mb }}";
      const initialMode = "{{ initial_mode }}";
      let currentMode = initialMode === "lock" ? "lock" : "unlock";
      let currentLang = "en";
      let loadingTimer = null;

      const IS_HOSTED = {{ 'true' if is_hosted else 'false' }};
      const copy = {
        en: {
          static: {
            badge: IS_HOSTED ? "Online · in-memory" : "Local · private",
            intro: "Remove a known PDF password, or add a new one, without storing files on disk.",
            howTitle: "How it works",
            modeUnlock: "🔓 Remove password",
            modeLock: "🔒 Add password",
            fileLabel: "PDF file",
            upload: "Upload PDF",
            noFile: "No file selected",
            clearFile: "Clear file",
            clear: "Clear",
            limitNote: IS_HOSTED
              ? `Processed in memory and never stored. Up to ${maxMb} MB per file — run it locally for bigger ones. Only process PDFs you own or have rights to edit.`
              : "Files stay on your computer and are never uploaded. Only process PDFs you own or have rights to edit.",
            footer: IS_HOSTED
              ? "Hosted on Vercel · your PDF is processed in memory and never stored. Open source — run it locally to keep files fully offline."
              : "Running locally · your PDFs never leave this computer. Built with Flask + pypdf.",
            showPassword: "Show password",
            hidePassword: "Hide password",
            mismatch: "Passwords do not match.",
            processing: "Processing..."
          },
          modes: {
            unlock: {
              passwordLabel: "PDF password",
              passwordPlaceholder: "Enter the current PDF password",
              passwordHelper: "Leave blank if the PDF opens without a password.",
              submit: "Unlock PDF",
              announce: "Remove password mode selected.",
              steps: [
                "Choose the locked PDF.",
                "Enter the current password if it has one.",
                "Download the unlocked copy."
              ]
            },
            lock: {
              passwordLabel: "New password",
              passwordPlaceholder: "Enter a new password",
              passwordHelper: "This password will be required to open the protected PDF.",
              confirmLabel: "Confirm password",
              confirmPlaceholder: "Re-enter the new password",
              confirmHelper: "Both entries must match before protecting the PDF.",
              submit: "Protect PDF",
              announce: "Add password mode selected.",
              steps: [
                "Choose the PDF you want to protect.",
                "Enter and confirm the new password.",
                "Download the protected copy."
              ]
            }
          }
        },
        zh: {
          static: {
            badge: IS_HOSTED ? "在线 · 内存处理" : "本地 · 私密",
            intro: "移除已知 PDF 密码，或添加新密码；文件不会写入磁盘。",
            howTitle: "工作方式",
            modeUnlock: "🔓 移除密码",
            modeLock: "🔒 添加密码",
            fileLabel: "PDF 文件",
            upload: "上传 PDF",
            noFile: "未选择文件",
            clearFile: "清除文件",
            clear: "清空",
            limitNote: IS_HOSTED
              ? `在内存中处理，不会存储。单个文件最大 ${maxMb} MB，更大的文件请本地运行。仅处理你拥有或有权编辑的 PDF。`
              : "文件保留在你的电脑上，不会上传。仅处理你拥有或有权编辑的 PDF。",
            footer: IS_HOSTED
              ? "托管在 Vercel · 你的 PDF 仅在内存中处理，不会存储。开源项目 —— 想完全离线可在本地运行。"
              : "本地运行 · 你的 PDF 不会离开这台电脑。基于 Flask + pypdf 构建。",
            showPassword: "显示密码",
            hidePassword: "隐藏密码",
            mismatch: "两次输入的密码不一致。",
            processing: "处理中..."
          },
          modes: {
            unlock: {
              passwordLabel: "PDF 密码",
              passwordPlaceholder: "输入当前 PDF 密码",
              passwordHelper: "如果这个 PDF 不需要密码即可打开，可以留空。",
              submit: "解锁 PDF",
              announce: "已选择移除密码模式。",
              steps: [
                "选择需要移除密码的 PDF。",
                "输入当前密码；如果不需要密码可留空。",
                "下载已解锁的副本。"
              ]
            },
            lock: {
              passwordLabel: "新密码",
              passwordPlaceholder: "输入新密码",
              passwordHelper: "之后打开受保护 PDF 时需要这个密码。",
              confirmLabel: "确认密码",
              confirmPlaceholder: "再次输入新密码",
              confirmHelper: "两次输入一致后才能保护 PDF。",
              submit: "保护 PDF",
              announce: "已选择添加密码模式。",
              steps: [
                "选择需要保护的 PDF。",
                "输入并确认新密码。",
                "下载已加密保护的副本。"
              ]
            }
          }
        }
      };

      function formatBytes(bytes) {
        if (!bytes && bytes !== 0) return "";
        if (bytes < 1024) return `${bytes} B`;
        const units = ["KB", "MB", "GB"];
        let value = bytes / 1024;
        let unitIndex = 0;
        while (value >= 1024 && unitIndex < units.length - 1) {
          value = value / 1024;
          unitIndex += 1;
        }
        return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
      }

      function setLoading(isLoading) {
        form.classList.toggle("loading", isLoading);
        if (isLoading) {
          processLabel.textContent = copy[currentLang].static.processing;
          processButton.disabled = true;
          return;
        }
        applyModeCopy();
        updateState();
      }

      function activeModeCopy() {
        return copy[currentLang].modes[currentMode];
      }

      function applyLanguage() {
        const strings = copy[currentLang].static;
        document.documentElement.lang = currentLang === "zh" ? "zh-Hans" : "en";
        document.querySelectorAll("[data-i18n]").forEach((node) => {
          const key = node.getAttribute("data-i18n");
          if (strings[key]) node.textContent = strings[key];
        });
        document.querySelectorAll(".lang-button").forEach((button) => {
          button.setAttribute("aria-pressed", String(button.dataset.lang === currentLang));
        });
        mismatchMessage.textContent = strings.mismatch;
        document.querySelectorAll("[data-toggle-password]").forEach((button) => {
          const target = document.getElementById(button.dataset.togglePassword);
          const label = target.type === "text" ? strings.hidePassword : strings.showPassword;
          button.setAttribute("aria-label", label);
        });
        applyModeCopy();
        updateState();
      }

      function applyModeCopy() {
        const modeCopy = activeModeCopy();
        passwordLabel.textContent = modeCopy.passwordLabel;
        passwordInput.placeholder = modeCopy.passwordPlaceholder;
        passwordHelper.textContent = modeCopy.passwordHelper;
        processLabel.textContent = modeCopy.submit;
        document.querySelectorAll("[data-step]").forEach((step, index) => {
          step.textContent = modeCopy.steps[index];
        });
        confirmLabel.textContent = modeCopy.confirmLabel || "";
        confirmInput.placeholder = modeCopy.confirmPlaceholder || "";
        confirmHelper.textContent = modeCopy.confirmHelper || "";
        modeAnnouncer.textContent = modeCopy.announce;
      }

      function validatePasswords() {
        if (currentMode !== "lock") {
          mismatchMessage.hidden = true;
          confirmInput.setCustomValidity("");
          return true;
        }
        const password = passwordInput.value;
        const confirmation = confirmInput.value;
        const matches = password.length > 0 && password === confirmation;
        const showMismatch = confirmation.length > 0 && password !== confirmation;
        mismatchMessage.hidden = !showMismatch;
        confirmInput.setCustomValidity(showMismatch ? copy[currentLang].static.mismatch : "");
        return matches;
      }

      function updateFileText() {
        const file = fileInput.files[0];
        if (!file) {
          fileName.textContent = copy[currentLang].static.noFile;
          fileSize.textContent = "";
          clearFileButton.hidden = true;
          return;
        }
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        clearFileButton.hidden = false;
      }

      function updateState() {
        updateFileText();
        const hasFile = fileInput.files.length > 0;
        const passwordsValid = validatePasswords();
        processButton.disabled = !hasFile || !passwordsValid || form.classList.contains("loading");
      }

      function setMode(mode) {
        currentMode = mode === "lock" ? "lock" : "unlock";
        modeInput.value = currentMode;
        modeTabs.forEach((tab) => {
          const selected = tab.dataset.mode === currentMode;
          tab.setAttribute("aria-selected", String(selected));
          tab.tabIndex = selected ? 0 : -1;
        });
        const locking = currentMode === "lock";
        confirmField.hidden = !locking;
        confirmInput.disabled = !locking;
        passwordInput.required = locking;
        confirmInput.required = locking;
        passwordInput.autocomplete = locking ? "new-password" : "current-password";
        applyModeCopy();
        updateState();
      }

      function setDroppedFile(files) {
        if (!files.length) return;
        try {
          const transfer = new DataTransfer();
          transfer.items.add(files[0]);
          fileInput.files = transfer.files;
        } catch (error) {
          try {
            fileInput.files = files;
          } catch (ignored) {
            return;
          }
        }
        updateState();
      }

      modeTabs.forEach((tab) => {
        tab.addEventListener("click", () => setMode(tab.dataset.mode));
        tab.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setMode(tab.dataset.mode);
          }
        });
      });

      document.querySelectorAll(".lang-button").forEach((button) => {
        button.addEventListener("click", () => {
          currentLang = button.dataset.lang === "zh" ? "zh" : "en";
          applyLanguage();
        });
      });

      document.querySelectorAll("[data-toggle-password]").forEach((button) => {
        const target = document.getElementById(button.dataset.togglePassword);
        button.addEventListener("click", () => {
          const currentlyVisible = target.type === "text";
          target.type = currentlyVisible ? "password" : "text";
          button.setAttribute("aria-pressed", String(!currentlyVisible));
          const label = currentlyVisible
            ? copy[currentLang].static.showPassword
            : copy[currentLang].static.hidePassword;
          button.setAttribute("aria-label", label);
        });
      });

      fileButton.addEventListener("click", () => fileInput.click());
      fileInput.addEventListener("change", updateState);
      passwordInput.addEventListener("input", updateState);
      confirmInput.addEventListener("input", updateState);
      clearFileButton.addEventListener("click", () => {
        fileInput.value = "";
        updateState();
      });
      resetButton.addEventListener("click", () => {
        fileInput.value = "";
        passwordInput.value = "";
        confirmInput.value = "";
        setLoading(false);
      });

      ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropZone.classList.add("is-dragover");
        });
      });
      ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropZone.classList.remove("is-dragover");
        });
      });
      dropZone.addEventListener("drop", (event) => {
        setDroppedFile(event.dataTransfer.files);
      });

      form.addEventListener("submit", (event) => {
        updateState();
        if (processButton.disabled) {
          event.preventDefault();
          if (currentMode === "lock" && !validatePasswords()) {
            (confirmInput.value ? confirmInput : passwordInput).focus();
          }
          return;
        }
        setLoading(true);
        window.clearTimeout(loadingTimer);
        loadingTimer = window.setTimeout(() => setLoading(false), 1800);
      });
      window.addEventListener("pageshow", () => {
        window.clearTimeout(loadingTimer);
        setLoading(false);
      });
      applyLanguage();
      setMode(currentMode);
    </script>
  </body>
</html>
"""


def normalize_mode(mode):
    return mode if mode in {"unlock", "lock"} else "unlock"


def render_page(status=None, message=None, mode="unlock"):
    mode = normalize_mode(mode)
    try:
        ua = (request.user_agent.string or "").lower()
    except Exception:
        ua = ""
    is_mobile = any(token in ua for token in ("iphone", "ipad", "ipod", "android", "mobile"))
    status_title = None
    if status == "success":
        status_title = "Protected" if mode == "lock" else "Unlocked"
    elif status == "error":
        status_title = "Could not protect" if mode == "lock" else "Could not unlock"
    elif status == "info":
        status_title = "Note"
    return render_template_string(
        TEMPLATE,
        status=status,
        status_title=status_title,
        message=message,
        max_mb=MAX_MB,
        initial_mode=mode,
        is_hosted=IS_HOSTED,
        is_mobile=is_mobile,
    )


def writer_from_reader(reader):
    writer = PdfWriter()
    try:
        writer.append(reader)
    except Exception:
        app.logger.warning("Falling back to page-by-page PDF copy.", exc_info=True)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
    return writer


def pdf_buffer_from_writer(writer):
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def encrypted_pdf_buffer(reader, password):
    writer = writer_from_reader(reader)
    try:
        writer.encrypt(
            user_password=password,
            owner_password=password,
            algorithm="AES-256",
        )
    except Exception:
        app.logger.debug("Falling back to default PDF encryption algorithm.")
        writer = writer_from_reader(reader)
        writer.encrypt(user_password=password, owner_password=password)
    return pdf_buffer_from_writer(writer)


@app.route("/", methods=["GET"])
def index():
    return render_page()


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return (
        render_page(
            "error",
            f"That PDF is larger than the {MAX_MB} MB limit for the hosted version. Run it locally for bigger files.",
        ),
        413,
    )


@app.route("/process", methods=["POST"])
def process():
    mode = normalize_mode(request.form.get("mode", "unlock"))
    upload = request.files.get("pdf")
    if not upload or upload.filename == "":
        return render_page("error", "Please choose a PDF file.", mode), 400

    password = request.form.get("password", "")
    if mode == "lock" and not password:
        return render_page("error", "Enter a password to protect the PDF.", mode), 400

    original_name = secure_filename(upload.filename)
    base_name = os.path.splitext(original_name)[0] if original_name else ""
    base_name = secure_filename(base_name) or "document"

    try:
        data = upload.read()
        reader = PdfReader(io.BytesIO(data))
    except (EmptyFileError, PdfReadError, PdfStreamError):
        return render_page("error", "That file does not appear to be a valid PDF.", mode), 400
    except Exception:
        return render_page("error", "That file does not appear to be a valid PDF.", mode), 400

    try:
        if mode == "lock":
            if reader.is_encrypted and reader.decrypt("") == 0:
                return (
                    render_page(
                        "error",
                        "This PDF is already password-protected. Switch to “Remove password” first.",
                        mode,
                    ),
                    400,
                )

            output = encrypted_pdf_buffer(reader, password)
            return send_file(
                output,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"{base_name}_protected.pdf",
            )

        if reader.is_encrypted and reader.decrypt(password or "") == 0:
            return render_page("error", "That password did not unlock this PDF.", mode), 400

        output = pdf_buffer_from_writer(writer_from_reader(reader))
        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{base_name}_unlocked.pdf",
        )
    except PdfReadError:
        return render_page("error", "That file does not appear to be a valid PDF.", mode), 400
    except Exception:
        app.logger.exception("Something went wrong while processing the PDF.")
        return render_page("error", "Something went wrong while processing the PDF.", mode), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
