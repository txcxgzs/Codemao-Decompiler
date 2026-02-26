#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编程猫作品反编译器 (Codemao Decompiler) - Web 服务版

================================================================================
版权与开源协议声明 / Copyright & License Notice
================================================================================

本项目是一个基于以下开源项目进行二次开发和界面优化的作品：
原项目名称: Kitten-4-Decompiler (源码反编译器4)
原作者: SLIGHTNING
原项目地址: https://gitee.com/slightning/Kitten-4-Decompiler

本项目严格遵守 GNU Affero General Public License Version 3 (AGPLv3) 开源协议。
根据协议要求，本项目及其衍生作品必须保持开源，并保留原始版权声明。

Copyright (C) 2026 Codemao Decompiler Contributors
Copyright (C) SLIGHTNING (Original Kitten-4-Decompiler author)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
================================================================================
"""

import json
import os
import random
from datetime import datetime, timedelta
from xml.etree import ElementTree
from functools import wraps

import requests
import threading
import time
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ==================== 配置 ====================

app = Flask(__name__)
CORS(app)  # 允许跨域调用
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'files')
app.config['FILE_EXPIRE_MINUTES'] = int(os.environ.get('FILE_EXPIRE_MINUTES', 20))
app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin123')

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)


# ==================== HTML模板 ====================

INDEX_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>编程猫作品反编译平台</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-light: #818cf8;
            --secondary: #6366f1;
            --accent: #f43f5e;
            --bg: #f8fafc;
            --gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        }
        body {
            background-color: var(--bg);
            min-height: 100vh;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            display: flex;
            flex-direction: column;
            margin: 0;
            color: #1e293b;
        }
        .navbar {
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(0,0,0,0.05);
            padding: 18px 0;
        }
        .navbar-brand {
            color: #0f172a !important;
            font-weight: 800;
            letter-spacing: -0.025em;
            display: flex;
            align-items: center;
        }
        .hero {
            background: var(--gradient);
            color: white;
            padding: 100px 0 140px;
            margin-bottom: -60px;
            clip-path: ellipse(150% 100% at 50% 0%);
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 1.5rem;
            text-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        .hero p {
            opacity: 0.9;
            font-size: 1.25rem;
            max-width: 600px;
            margin: 0 auto;
            font-weight: 500;
        }
        .card {
            border: none;
            border-radius: 24px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: white;
            border: 1px solid rgba(0,0,0,0.05);
            overflow: hidden;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 30px -5px rgba(0,0,0,0.08);
        }
        .card-header {
            background: white;
            border-bottom: 1px solid #f1f5f9;
            padding: 24px 30px;
            font-weight: 700;
            color: #0f172a;
            display: flex;
            align-items: center;
        }
        .btn-primary {
            background: var(--gradient);
            border: none;
            border-radius: 14px;
            padding: 14px 28px;
            font-weight: 700;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
        }
        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
            background: var(--gradient);
        }
        .form-control {
            border-radius: 14px;
            padding: 14px 20px;
            border: 2px solid #e2e8f0;
            font-weight: 500;
            transition: all 0.2s;
        }
        .form-control:focus {
            border-color: var(--primary-light);
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
        }
        .download-box {
            background: #f0fdf4;
            border: 2px dashed #bbf7d0;
            border-radius: 18px;
            padding: 30px;
            text-align: center;
        }
        .btn-download {
            background: #10b981;
            border: none;
            color: white;
            border-radius: 14px;
            padding: 16px 35px;
            font-weight: 800;
            font-size: 1.1rem;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);
        }
        .info-box {
             background: #f8fafc;
             border-radius: 18px;
             padding: 24px;
             margin-bottom: 24px;
             border: 1px solid rgba(0,0,0,0.03);
         }
         .rounded-18 { border-radius: 18px !important; }
         .rounded-14 { border-radius: 14px !important; }
         .rounded-10 { border-radius: 10px !important; }
        .btn-download:hover {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
        }
        .badge-type {
            padding: 6px 14px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .badge-kitten4 { background: #eff6ff; color: #1d4ed8; }
        .badge-kitten3 { background: #fdf2f8; color: #be185d; }
        .badge-coco { background: #ecfeff; color: #0e7490; }
        
        .main-content { flex: 1; position: relative; z-index: 10; }
        footer {
            background: #0f172a;
            color: #94a3b8;
            padding: 60px 0;
            margin-top: 80px;
        }
        .table thead th {
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 20px 24px;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }
        .table td {
            padding: 18px 24px;
            vertical-align: middle;
        }
        .spinner-grow { width: 3rem; height: 3rem; }
        
        /* Animations */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.4s ease-out forwards; }
    </style>
</head>
<body>
    <nav class="navbar sticky-top">
        <div class="container">
            <a class="navbar-brand" href="/">
                <div class="bg-primary text-white rounded-10 p-2 me-3 d-inline-flex">
                    <i class="bi bi-cpu-fill"></i>
                </div>
                编程猫作品反编译平台
            </a>
        </div>
    </nav>
    
    <div class="main-content">
        <div class="hero">
            <div class="container text-center">
                <h1 class="fade-in">作品源码反编译器</h1>
                <p class="fade-in" style="animation-delay: 0.1s;">一键获取编程猫作品源码，支持 Kitten 3/4 和 CoCo，助您深度学习优秀案例</p>
            </div>
        </div>
        
        <div class="container">
            <div class="row g-4">
                <!-- Left: Decompile Tool -->
                <div class="col-lg-5">
                    <div class="card fade-in" style="animation-delay: 0.2s;">
                        <div class="card-header">
                            <i class="bi bi-magic text-primary me-2 fs-5"></i> 立即开始转换
                        </div>
                        <div class="card-body p-4">
                            <div class="mb-4">
                                <label class="form-label small fw-bold text-muted text-uppercase mb-2">作品 ID</label>
                                <div class="input-group">
                                    <input type="number" class="form-control" id="workId" placeholder="输入 8 位作品 ID (如: 14526378)">
                                    <button class="btn btn-primary px-4" id="decompileBtn" title="点击开始反编译">
                                        <i class="bi bi-lightning-charge-fill"></i>
                                    </button>
                                </div>
                                <div class="form-text mt-2">作品 ID 可以在编程猫作品详情页 URL 中找到</div>
                            </div>
                            
                            <!-- Loading State -->
                            <div id="loading" class="text-center py-5" style="display:none;">
                                <div class="spinner-grow text-primary mb-3"></div>
                                <h5 class="fw-bold text-dark">正在深度解析...</h5>
                                <p class="text-muted small">正在从云端获取作品资源包并进行解压</p>
                            </div>
                            
                            <!-- Result Display -->
                            <div id="result" style="display:none;" class="fade-in">
                                <div class="info-box">
                                    <h6 class="text-uppercase small fw-bold text-muted mb-3 border-bottom pb-2">作品元数据</h6>
                                    <div class="d-flex justify-content-between mb-3 align-items-center">
                                        <span class="text-muted">作品名称</span>
                                        <span id="workName" class="fw-bold text-dark"></span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-3 align-items-center">
                                        <span class="text-muted">创作者</span>
                                        <span id="authorName" class="fw-bold text-dark"></span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-3 align-items-center">
                                        <span class="text-muted">引擎版本</span>
                                        <span id="workType" class="badge-type"></span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-4 align-items-center">
                                        <span class="text-muted">包体大小</span>
                                        <span id="fileSize" class="fw-bold"></span>
                                    </div>
                                    <div class="row g-2">
                                        <div class="col-6">
                                            <button class="btn btn-light w-100 rounded-14 border fw-bold" id="copyBtn">
                                                <i class="bi bi-clipboard me-2"></i>复制 ID
                                            </button>
                                        </div>
                                        <div class="col-6">
                                            <a id="viewWork" href="#" target="_blank" class="btn btn-light w-100 rounded-14 border fw-bold">
                                                <i class="bi bi-eye me-2"></i>在线预览
                                            </a>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="download-box">
                                    <div class="bg-success bg-opacity-10 text-success d-inline-flex p-3 rounded-circle mb-3">
                                        <i class="bi bi-check2-circle fs-2"></i>
                                    </div>
                                    <h5 class="fw-800 text-dark mb-1">反编译已完成</h5>
                                    <p class="text-muted small mb-4">下载链接将在 <span id="expires" class="text-danger fw-bold"></span> 后失效</p>
                                    <button class="btn btn-download w-100" id="downloadBtn">
                                        <i class="bi bi-cloud-arrow-down-fill me-2"></i>下载源代码包 (.zip)
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Error State -->
                            <div id="error" class="alert alert-danger mt-3 rounded-18 border-0 shadow-sm fade-in" style="display:none;">
                                <div class="d-flex align-items-center">
                                    <i class="bi bi-exclamation-triangle-fill me-3 fs-4"></i>
                                    <div id="errorMsg"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Right: Recent Activity -->
                <div class="col-lg-7">
                    <div class="card fade-in" style="animation-delay: 0.3s;">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span><i class="bi bi-clock-history text-primary me-2 fs-5"></i> 公共反编译记录</span>
                            <button class="btn btn-light btn-sm rounded-10 border" id="refreshRecordsBtn">
                                <i class="bi bi-arrow-repeat me-1"></i> 刷新
                            </button>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-hover align-middle mb-0">
                                    <thead>
                                        <tr>
                                            <th class="ps-4">作品详情</th>
                                            <th>类型</th>
                                            <th>转换时间</th>
                                            <th class="text-end pe-4">下载</th>
                                        </tr>
                                    </thead>
                                    <tbody id="records">
                                        <tr><td colspan="4" class="text-center py-5 text-muted">正在同步云端记录...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-6 text-center text-md-start mb-4 mb-md-0">
                    <h5 class="text-white fw-bold mb-3">Codemao Decompiler</h5>
                    <p class="mb-0 text-white-50 small">本工具仅供技术交流与学习研究使用，严禁用于任何侵犯版权的行为。</p>
                    <p class="text-white-50 small">请尊重创作者劳动成果。</p>
                </div>
                <div class="col-md-6 text-center text-md-end">
                    <a href="https://github.com/txcxgzs/Codemao-Decompiler" target="_blank" class="btn btn-outline-light rounded-pill px-4 btn-sm">
                        <i class="bi bi-github me-2"></i> GitHub 开源仓库
                    </a>
                </div>
            </div>
            <hr class="my-4 opacity-10">
            <div class="text-center">
                <p class="small mb-0 text-white-50">&copy; 2026 编程猫作品反编译平台. All Rights Reserved.</p>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        (function() {
            let recordId = null, downloadUrl = null;
            const formatSize = b => b < 1024 ? b + ' B' : b < 1048576 ? (b/1024).toFixed(1) + ' KB' : (b/1048576).toFixed(1) + ' MB';
            const formatTime = s => { const d = new Date(s); return d.toLocaleDateString() + ' ' + d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0'); };
            const formatRemaining = exp => { const d = new Date(exp) - new Date(); return d <= 0 ? '已过期' : Math.floor(d/60000) + '分' + Math.floor((d%60000)/1000) + '秒'; };
            const getTypeBadge = t => ({KITTEN4:'badge-kitten4',KITTEN3:'badge-kitten3',COCO:'badge-coco'}[t] || 'bg-secondary');
            
            async function api(url, opts = {}) { 
                opts.headers = {...opts.headers, 'Content-Type': 'application/json'}; 
                if (opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body); 
                const res = await fetch(url, opts); 
                return res.json(); 
            }
            
            async function decompile() {
                const idInput = document.getElementById('workId');
                const id = idInput.value.trim();
                if (!id) return;
                
                const btn = document.getElementById('decompileBtn');
                const originalText = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
                
                document.getElementById('loading').style.display = 'block'; 
                document.getElementById('result').style.display = 'none'; 
                document.getElementById('error').style.display = 'none';
                
                try {
                    const data = await api('/api/decompile', { method: 'POST', body: {work_id: parseInt(id)} });
                    if (data.success) {
                        recordId = data.data.record_id; 
                        downloadUrl = data.data.download_url;
                        
                        document.getElementById('workName').textContent = data.data.work_name || '未命名作品'; 
                        document.getElementById('authorName').textContent = data.data.author_name || '匿名作者';
                        document.getElementById('workType').textContent = data.data.work_type; 
                        document.getElementById('workType').className = 'badge-type ' + getTypeBadge(data.data.work_type);
                        document.getElementById('fileSize').textContent = formatSize(data.data.file_size); 
                        document.getElementById('expires').textContent = formatRemaining(data.data.expires_at);
                        
                        document.getElementById('viewWork').href = data.data.work_type === 'COCO' ? `https://coco.codemao.cn/work/${id}` : `https://kitten4.codemao.cn/#${id}`;
                        
                        document.getElementById('result').style.display = 'block';
                        
                        if (window.expireTimer) clearInterval(window.expireTimer);
                        window.expireTimer = setInterval(() => { 
                            document.getElementById('expires').textContent = formatRemaining(data.data.expires_at); 
                        }, 1000);
                        
                        loadRecords();
                    } else { 
                        document.getElementById('errorMsg').textContent = data.error; 
                        document.getElementById('error').style.display = 'block'; 
                    }
                } catch(e) { 
                    document.getElementById('errorMsg').textContent = '无法连接到服务器，请稍后重试'; 
                    document.getElementById('error').style.display = 'block'; 
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    document.getElementById('loading').style.display = 'none';
                }
            }

            async function loadRecords() {
                const data = await api('/api/records?per_page=10');
                if (data.success) {
                    const html = data.data.records.length ? data.data.records.map(r => `
                        <tr>
                            <td class="ps-4">
                                <div class="fw-bold text-dark">${r.work_name||'未知作品'}</div>
                                <small class="text-muted">ID: ${r.work_id}</small>
                            </td>
                            <td><span class="badge-type ${getTypeBadge(r.work_type)}">${r.work_type}</span></td>
                            <td><small class="text-muted">${formatTime(r.created_at)}</small></td>
                            <td class="text-end pe-4">
                                <a href="/api/download/${r.id}" class="btn btn-sm btn-light border rounded-circle" title="立即下载">
                                    <i class="bi bi-download text-primary"></i>
                                </a>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="4" class="text-center text-muted py-5">暂无反编译记录</td></tr>';
                    document.getElementById('records').innerHTML = html;
                }
            }

            function copyId() {
                const id = document.getElementById('workId').value.trim();
                if (id) { 
                    navigator.clipboard.writeText(id); 
                    const btn = document.getElementById('copyBtn');
                    const old = btn.innerHTML; 
                    btn.innerHTML = '<i class="bi bi-check2"></i> 已复制'; 
                    btn.classList.replace('btn-light', 'btn-success');
                    setTimeout(() => {
                        btn.innerHTML = old;
                        btn.classList.replace('btn-success', 'btn-light');
                    }, 2000); 
                }
            }

            document.addEventListener('DOMContentLoaded', () => {
                document.getElementById('decompileBtn').addEventListener('click', decompile);
                document.getElementById('copyBtn')?.addEventListener('click', copyId);
                document.getElementById('workId').addEventListener('keypress', e => e.key === 'Enter' && decompile());
                document.getElementById('refreshRecordsBtn')?.addEventListener('click', loadRecords);

                document.addEventListener('click', (e) => {
                    if (e.target.closest('#downloadBtn')) {
                        if (downloadUrl) window.location.href = downloadUrl;
                    }
                });

                loadRecords();
            });
        })();
    </script>
</body>
</html>'''

ADMIN_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统管理 - 编程猫反编译平台</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-dark: #4338ca;
            --secondary: #64748b;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --sidebar-width: 280px;
            --header-height: 70px;
        }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f1f5f9;
            color: #0f172a;
            overflow-x: hidden;
        }
        
        /* Login Page */
        .login-page {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%);
            position: relative;
            overflow: hidden;
        }
        .login-page::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 48px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.5);
            transform: translateY(0);
            transition: all 0.3s ease;
        }
        .login-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.3);
        }
        
        /* Dashboard Layout */
        .dashboard-container {
            display: flex;
            min-height: 100vh;
        }
        .sidebar {
            width: var(--sidebar-width);
            background: white;
            border-right: 1px solid #e2e8f0;
            position: fixed;
            height: 100vh;
            z-index: 1000;
            transition: transform 0.3s ease;
        }
        .main-content {
            flex: 1;
            margin-left: var(--sidebar-width);
            padding: 30px;
            min-height: 100vh;
        }
        
        /* Components */
        .nav-link {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            color: var(--secondary);
            border-radius: 12px;
            margin-bottom: 5px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .nav-link:hover, .nav-link.active {
            background: #eff6ff;
            color: var(--primary);
        }
        .nav-link i {
            font-size: 1.2rem;
            margin-right: 12px;
        }
        
        .stat-card {
            background: white;
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border: 1px solid #f1f5f9;
            height: 100%;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        }
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 16px;
        }
        
        .content-card {
            background: white;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            overflow: hidden;
        }
        .content-header {
            padding: 20px 24px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .table th {
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            color: var(--secondary);
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            padding: 16px 24px;
        }
        .table td {
            padding: 16px 24px;
            vertical-align: middle;
            color: #334155;
            border-bottom: 1px solid #f1f5f9;
        }
        .table tr:last-child td { border-bottom: none; }
        
        .btn-primary {
            background: var(--primary);
            border-color: var(--primary);
            padding: 10px 24px;
            border-radius: 10px;
            font-weight: 500;
        }
        .btn-primary:hover {
            background: var(--primary-dark);
            border-color: var(--primary-dark);
        }
        
        .badge-custom {
            padding: 6px 12px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 0.75rem;
        }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-danger { background: #fee2e2; color: #991b1b; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.show { transform: translateX(0); }
            .main-content { margin-left: 0; padding: 20px; }
            .mobile-toggle { display: block !important; }
        }
        .mobile-toggle { display: none; position: fixed; bottom: 20px; right: 20px; z-index: 1050; width: 50px; height: 50px; border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    </style>
</head>
<body>
    <!-- Login Page -->
    <div id="loginPage" class="login-page">
        <div class="login-card">
            <div class="text-center mb-5">
                <div class="d-inline-flex bg-primary bg-opacity-10 p-3 rounded-4 mb-3 text-primary">
                    <i class="bi bi-shield-lock-fill fs-2"></i>
                </div>
                <h3 class="fw-bold mb-1">管理员后台</h3>
                <p class="text-muted">Codemao Decompiler Admin</p>
            </div>
            
            <div id="loginError" class="alert alert-danger border-0 bg-danger bg-opacity-10 text-danger mb-4" style="display:none;">
                <i class="bi bi-exclamation-circle me-2"></i><span id="loginErrorText"></span>
            </div>
            
            <div class="mb-3">
                <label class="form-label small fw-bold text-uppercase text-muted">Username</label>
                <div class="input-group">
                    <span class="input-group-text bg-light border-end-0 border"><i class="bi bi-person text-muted"></i></span>
                    <input type="text" class="form-control bg-light border-start-0 border py-3" id="username" placeholder="请输入管理员账号">
                </div>
            </div>
            
            <div class="mb-4">
                <label class="form-label small fw-bold text-uppercase text-muted">Password</label>
                <div class="input-group">
                    <span class="input-group-text bg-light border-end-0 border"><i class="bi bi-key text-muted"></i></span>
                    <input type="password" class="form-control bg-light border-start-0 border py-3" id="password" placeholder="请输入密码">
                </div>
            </div>
            
            <button class="btn btn-primary w-100 py-3 mb-3 shadow-sm" id="loginBtn">
                <span class="d-inline-block">安全登录</span>
            </button>
            <a href="/" class="btn btn-link w-100 text-decoration-none text-muted small">返回首页</a>
        </div>
    </div>

    <!-- Admin Panel -->
    <div id="adminPanel" class="dashboard-container" style="display:none;">
        <!-- Sidebar -->
        <div class="sidebar d-flex flex-column p-4" id="sidebar">
            <div class="d-flex align-items-center mb-5 px-2">
                <div class="bg-primary text-white rounded-3 p-2 me-3"><i class="bi bi-cpu-fill"></i></div>
                <div><h6 class="fw-bold mb-0">Decompiler</h6><small class="text-muted">Admin Panel</small></div>
            </div>
            
            <ul class="nav flex-column mb-auto">
                <li class="nav-item">
                    <a href="#" class="nav-link active" id="navDashboard" onclick="switchTab('dashboard')">
                        <i class="bi bi-grid-1x2"></i> 仪表盘
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" id="navBanned" onclick="switchTab('banned')">
                        <i class="bi bi-shield-slash"></i> 黑名单管理
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" data-bs-toggle="modal" data-bs-target="#modalChangePassword">
                        <i class="bi bi-key"></i> 修改密码
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/" class="nav-link" target="_blank">
                        <i class="bi bi-box-arrow-up-right"></i> 前台首页
                    </a>
                </li>
            </ul>
            
            <div class="mt-auto pt-4 border-top">
                <div class="d-flex align-items-center justify-content-between px-2">
                    <div class="d-flex align-items-center">
                        <div class="bg-light rounded-circle p-2 me-2"><i class="bi bi-person-circle text-muted"></i></div>
                        <div class="small fw-bold">Admin</div>
                    </div>
                    <button class="btn btn-sm btn-light text-danger" id="logoutBtn" title="退出登录"><i class="bi bi-box-arrow-right"></i></button>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Mobile Toggle -->
            <button class="btn btn-primary mobile-toggle rounded-circle" onclick="document.getElementById('sidebar').classList.toggle('show')">
                <i class="bi bi-list"></i>
            </button>

            <!-- Dashboard View -->
            <div id="viewDashboard" class="fade-in">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h4 class="fw-bold mb-0">系统概览</h4>
                    <button class="btn btn-light border bg-white text-muted btn-sm" onclick="loadStats();loadRecords();"><i class="bi bi-arrow-clockwise me-1"></i> 刷新数据</button>
                </div>
                
                <div class="row g-4 mb-5">
                    <div class="col-xl-3 col-md-6">
                        <div class="stat-card">
                            <div class="stat-icon bg-primary bg-opacity-10 text-primary"><i class="bi bi-database"></i></div>
                            <h2 class="fw-bold mb-1" id="statTotal">...</h2>
                            <p class="text-muted small mb-0">总反编译记录</p>
                        </div>
                    </div>
                    <div class="col-xl-3 col-md-6">
                        <div class="stat-card">
                            <div class="stat-icon bg-success bg-opacity-10 text-success"><i class="bi bi-check-circle"></i></div>
                            <h2 class="fw-bold mb-1" id="statSuccess">...</h2>
                            <p class="text-muted small mb-0">成功记录</p>
                        </div>
                    </div>
                    <div class="col-xl-3 col-md-6">
                        <div class="stat-card">
                            <div class="stat-icon bg-info bg-opacity-10 text-info"><i class="bi bi-lightning"></i></div>
                            <h2 class="fw-bold mb-1" id="statToday">...</h2>
                            <p class="text-muted small mb-0">今日新增</p>
                        </div>
                    </div>
                    <div class="col-xl-3 col-md-6">
                        <div class="stat-card">
                            <div class="stat-icon bg-danger bg-opacity-10 text-danger"><i class="bi bi-shield-x"></i></div>
                            <h2 class="fw-bold mb-1" id="statBanned">...</h2>
                            <p class="text-muted small mb-0">封禁对象</p>
                        </div>
                    </div>
                </div>
                
                <div class="content-card">
                    <div class="content-header">
                        <h6 class="fw-bold mb-0">最近反编译活动</h6>
                        <div class="input-group input-group-sm" style="width: 200px;">
                            <span class="input-group-text bg-light border-end-0"><i class="bi bi-search"></i></span>
                            <input type="text" class="form-control bg-light border-start-0" placeholder="搜索ID..." id="searchRecord">
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead>
                                <tr>
                                    <th class="ps-4">Record ID</th>
                                    <th>作品信息</th>
                                    <th>来源 IP</th>
                                    <th>状态</th>
                                    <th>时间</th>
                                    <th class="text-end pe-4">操作</th>
                                </tr>
                            </thead>
                            <tbody id="allRecords">
                                <tr><td colspan="6" class="text-center py-5 text-muted">正在加载数据...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Banned View -->
            <div id="viewBanned" style="display:none;" class="fade-in">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h4 class="fw-bold mb-0">黑名单管理</h4>
                </div>
                
                <div class="row g-4">
                    <div class="col-lg-6">
                        <div class="content-card h-100">
                            <div class="content-header bg-danger bg-opacity-10 border-bottom border-danger border-opacity-10">
                                <h6 class="fw-bold mb-0 text-danger"><i class="bi bi-file-earmark-x me-2"></i>封禁作品 ID</h6>
                                <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#modalBanWork"><i class="bi bi-plus-lg"></i> 添加</button>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-hover align-middle mb-0">
                                    <thead><tr><th class="ps-4">作品 ID</th><th class="text-end pe-4">操作</th></tr></thead>
                                    <tbody id="bannedWorksList"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="content-card h-100">
                            <div class="content-header bg-danger bg-opacity-10 border-bottom border-danger border-opacity-10">
                                <h6 class="fw-bold mb-0 text-danger"><i class="bi bi-globe me-2"></i>封禁 IP 地址</h6>
                                <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#modalBanIp"><i class="bi bi-plus-lg"></i> 添加</button>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-hover align-middle mb-0">
                                    <thead><tr><th class="ps-4">IP 地址</th><th class="text-end pe-4">操作</th></tr></thead>
                                    <tbody id="bannedIpsList"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div class="modal fade" id="modalBanWork" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg rounded-4">
                <div class="modal-header border-0 pb-0">
                    <h5 class="modal-title fw-bold">添加封禁作品</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">作品 ID</label>
                        <input type="number" class="form-control form-control-lg bg-light" id="inputBanWorkId" placeholder="例如: 12345678">
                    </div>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-light rounded-3" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger rounded-3 px-4" id="confirmBanWork">确认封禁</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="modalBanIp" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg rounded-4">
                <div class="modal-header border-0 pb-0">
                    <h5 class="modal-title fw-bold">添加封禁 IP</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">IP 地址</label>
                        <input type="text" class="form-control form-control-lg bg-light" id="inputBanIp" placeholder="例如: 192.168.1.1">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">封禁时长 (小时)</label>
                        <input type="number" class="form-control bg-light" id="inputBanDuration" value="24">
                    </div>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-light rounded-3" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger rounded-3 px-4" id="confirmBanIp">确认封禁</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="modalChangePassword" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content border-0 shadow-lg rounded-4">
                <div class="modal-header border-0 pb-0">
                    <h5 class="modal-title fw-bold">修改管理员密码</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="changePwdError" class="alert alert-danger py-2 small" style="display:none;"></div>
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">旧密码</label>
                        <input type="password" class="form-control bg-light" id="inputOldPassword">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">新密码</label>
                        <input type="password" class="form-control bg-light" id="inputNewPassword">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted small fw-bold">确认新密码</label>
                        <input type="password" class="form-control bg-light" id="inputConfirmPassword">
                    </div>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-light rounded-3" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary rounded-3 px-4" id="confirmChangePassword">确认修改</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        (function() {
            // State & Helpers
            let currentTab = 'dashboard';
            
            async function api(url, opts = {}) { 
                opts.headers = {...opts.headers, 'Content-Type': 'application/json'}; 
                if (opts.body && typeof opts.body === 'object') opts.body = JSON.stringify(opts.body); 
                
                try {
                    const res = await fetch(url, opts);
                    if (res.status === 401 && !url.includes('login')) { 
                        if (document.getElementById('adminPanel').style.display !== 'none') {
                            location.reload(); 
                        }
                        return {success: false, error: '未登录'}; 
                    }
                    return await res.json();
                } catch (e) {
                    console.error(e);
                    return {success: false, error: '网络请求失败'};
                }
            }
            
            // Core Functions
            async function login() {
                const btn = document.getElementById('loginBtn');
                const usernameInput = document.getElementById('username');
                const passwordInput = document.getElementById('password');
                const errorDiv = document.getElementById('loginError');
                
                if (!usernameInput.value || !passwordInput.value) {
                    document.getElementById('loginErrorText').textContent = '请输入用户名和密码';
                    errorDiv.style.display = 'block';
                    return;
                }

                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>登录中...';
                btn.disabled = true;
                errorDiv.style.display = 'none';

                const res = await api('/api/admin/login', {
                    method: 'POST', 
                    body: {
                        username: usernameInput.value, 
                        password: passwordInput.value
                    }
                });

                if (res.success) { 
                    showPanel(); 
                } else { 
                    document.getElementById('loginErrorText').textContent = res.error || '用户名或密码错误'; 
                    errorDiv.style.display = 'block'; 
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }
            }

            function logout() { 
                api('/api/admin/logout', {method: 'POST'}).then(() => location.reload()); 
            }

            function showPanel() { 
                document.getElementById('loginPage').style.display = 'none'; 
                document.getElementById('adminPanel').style.display = 'flex'; 
                loadStats(); 
                loadRecords();
                // 默认选中 Dashboard
                switchTab('dashboard');
            }
            
            window.switchTab = function(tab) {
                currentTab = tab;
                // UI Toggles
                document.getElementById('viewDashboard').style.display = tab === 'dashboard' ? 'block' : 'none';
                document.getElementById('viewBanned').style.display = tab === 'banned' ? 'block' : 'none';
                
                // Nav Active States
                document.getElementById('navDashboard').classList.toggle('active', tab === 'dashboard');
                document.getElementById('navBanned').classList.toggle('active', tab === 'banned');
                
                // Load Data
                if (tab === 'banned') { loadBannedWorks(); loadBannedIps(); }
                if (tab === 'dashboard') { loadStats(); loadRecords(); }
            }

            // Data Loading
            async function loadStats() {
                const res = await api('/api/admin/stats');
                if (res.success) {
                    document.getElementById('statTotal').textContent = res.data.total_records;
                    document.getElementById('statSuccess').textContent = res.data.success_records;
                    document.getElementById('statToday').textContent = res.data.today_records;
                    document.getElementById('statBanned').textContent = res.data.banned_works + res.data.banned_ips;
                }
            }

            async function loadRecords() {
                const res = await api('/api/admin/records?per_page=50');
                if (res.success) {
                    const html = res.data.records.length ? res.data.records.map(r => `
                        <tr>
                            <td class="ps-4"><code>#${r.id}</code></td>
                            <td>
                                <div class="fw-bold text-dark">${r.work_name||'未知作品'}</div>
                                <div class="small text-muted"><i class="bi bi-hash"></i> ${r.work_id}</div>
                            </td>
                            <td>
                                <div class="d-flex align-items-center">
                                    <span class="badge bg-light text-dark border me-2"><i class="bi bi-hdd-network"></i></span>
                                    <code>${r.client_ip||'Unknown'}</code>
                                </div>
                            </td>
                            <td>
                                <span class="badge-custom ${r.status==='success'?'badge-success':'badge-danger'}">
                                    ${r.status==='success' ? '<i class="bi bi-check-circle me-1"></i>成功' : '<i class="bi bi-x-circle me-1"></i>失败'}
                                </span>
                            </td>
                            <td><small class="text-muted">${new Date(r.created_at).toLocaleString()}</small></td>
                            <td class="text-end pe-4">
                                <button class="btn btn-sm btn-outline-danger border-0 rounded-circle del-record-btn" data-id="${r.id}" title="删除记录">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="6" class="text-center py-5 text-muted">暂无数据</td></tr>';
                    document.getElementById('allRecords').innerHTML = html;
                }
            }
            
            async function loadBannedWorks() {
                const res = await api('/api/admin/banned-works');
                if (res.success) {
                    const html = res.data.works.length ? res.data.works.map(w => `
                        <tr>
                            <td class="ps-4">
                                <span class="fw-bold text-dark">ID: ${w.work_id}</span>
                            </td>
                            <td class="text-end pe-4">
                                <button class="btn btn-sm btn-outline-danger border-0 rounded-circle del-banned-work-btn" data-id="${w.work_id}">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="2" class="text-center py-4 text-muted">暂无封禁作品</td></tr>';
                    document.getElementById('bannedWorksList').innerHTML = html;
                }
            }

            async function loadBannedIps() {
                const res = await api('/api/admin/banned-ips');
                if (res.success) {
                    const html = res.data.ips.length ? res.data.ips.map(ip => `
                        <tr>
                            <td class="ps-4">
                                <code class="text-primary">${ip.ip_address}</code>
                                <div class="small text-muted">到期: ${new Date(ip.expires_at).toLocaleDateString()}</div>
                            </td>
                            <td class="text-end pe-4">
                                <button class="btn btn-sm btn-outline-danger border-0 rounded-circle del-banned-ip-btn" data-ip="${ip.ip_address}">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="2" class="text-center py-4 text-muted">暂无封禁IP</td></tr>';
                    document.getElementById('bannedIpsList').innerHTML = html;
                }
            }

            // Action Functions
            async function delRecord(id) { 
                if (confirm('确定要删除这条记录吗？')) { 
                    await api('/api/admin/records/'+id, {method:'DELETE'}); 
                    loadRecords(); loadStats(); 
                } 
            }
            
            async function handleBanWork() {
                const id = document.getElementById('inputBanWorkId').value;
                if (!id) return;
                
                const modalEl = document.getElementById('modalBanWork');
                const modal = bootstrap.Modal.getInstance(modalEl);
                
                await api('/api/admin/banned-works', {method:'POST', body:{work_id:parseInt(id)}});
                
                document.getElementById('inputBanWorkId').value = '';
                modal.hide();
                loadBannedWorks();
                loadStats();
            }
            
            async function handleBanIp() {
                const ip = document.getElementById('inputBanIp').value;
                const duration = document.getElementById('inputBanDuration').value;
                if (!ip) return;
                
                const modalEl = document.getElementById('modalBanIp');
                const modal = bootstrap.Modal.getInstance(modalEl);
                
                await api('/api/admin/banned-ips', {method:'POST', body:{ip_address:ip, duration_hours:parseInt(duration)}});
                
                document.getElementById('inputBanIp').value = '';
                modal.hide();
                loadBannedIps();
                loadStats();
            }

            async function delBannedWork(id) { 
                await api('/api/admin/banned-works/'+id, {method:'DELETE'}); 
                loadBannedWorks(); loadStats(); 
            }
            
            async function delBannedIp(ip) { 
                await api('/api/admin/banned-ips/'+encodeURIComponent(ip), {method:'DELETE'}); 
                loadBannedIps(); loadStats(); 
            }

            async function handleChangePassword() {
                const oldPwd = document.getElementById('inputOldPassword').value;
                const newPwd = document.getElementById('inputNewPassword').value;
                const confirmPwd = document.getElementById('inputConfirmPassword').value;
                const errorDiv = document.getElementById('changePwdError');
                
                errorDiv.style.display = 'none';
                
                if (!oldPwd || !newPwd || !confirmPwd) {
                    errorDiv.textContent = '请填写所有字段';
                    errorDiv.style.display = 'block';
                    return;
                }
                
                if (newPwd !== confirmPwd) {
                    errorDiv.textContent = '两次输入的新密码不一致';
                    errorDiv.style.display = 'block';
                    return;
                }
                
                const btn = document.getElementById('confirmChangePassword');
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = '提交中...';
                
                const res = await api('/api/admin/change-password', {
                    method: 'POST',
                    body: { old_password: oldPwd, new_password: newPwd }
                });
                
                btn.disabled = false;
                btn.textContent = originalText;
                
                if (res.success) {
                    alert('密码修改成功，请重新登录');
                    logout();
                } else {
                    errorDiv.textContent = res.error || '修改失败';
                    errorDiv.style.display = 'block';
                }
            }

            // Initialization
            document.addEventListener('DOMContentLoaded', () => {
                // Static Bindings
                document.getElementById('loginBtn').addEventListener('click', login);
                document.getElementById('password').addEventListener('keypress', e => e.key === 'Enter' && login());
                
                // Global buttons
                document.getElementById('logoutBtn')?.addEventListener('click', (e) => { e.preventDefault(); logout(); });
                
                // Modal Confirm Buttons
                document.getElementById('confirmBanWork')?.addEventListener('click', handleBanWork);
                document.getElementById('confirmBanIp')?.addEventListener('click', handleBanIp);
                document.getElementById('confirmChangePassword')?.addEventListener('click', handleChangePassword);

                // Event Delegation for Dynamic Elements
                document.addEventListener('click', (e) => {
                    const delRecBtn = e.target.closest('.del-record-btn');
                    if (delRecBtn) delRecord(delRecBtn.dataset.id);
                    
                    const delBannedWorkBtn = e.target.closest('.del-banned-work-btn');
                    if (delBannedWorkBtn) delBannedWork(delBannedWorkBtn.dataset.id);
                    
                    const delBannedIpBtn = e.target.closest('.del-banned-ip-btn');
                    if (delBannedIpBtn) delBannedIp(delBannedIpBtn.dataset.ip);
                });

                // Auto check login
                api('/api/admin/stats').then(res => { if (res.success) showPanel(); });
            });
        })();
    </script>
</body>
</html>'''


# ==================== 数据库模型 ====================

class DecompilerRecord(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, nullable=False, index=True)
    work_name = db.Column(db.String(255))
    work_type = db.Column(db.String(20))
    author_name = db.Column(db.String(100))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    client_ip = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, index=True)
    download_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {'id': self.id, 'work_id': self.work_id, 'work_name': self.work_name, 'work_type': self.work_type, 'author_name': self.author_name, 'file_size': self.file_size, 'status': self.status, 'created_at': self.created_at.isoformat() if self.created_at else None, 'expires_at': self.expires_at.isoformat() if self.expires_at else None, 'download_count': self.download_count}


class BannedWork(db.Model):
    __tablename__ = 'banned_works'
    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    work_name = db.Column(db.String(255))
    reason = db.Column(db.String(500))
    banned_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BannedIP(db.Model):
    __tablename__ = 'banned_ips'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), unique=True, nullable=False, index=True)
    reason = db.Column(db.String(500))
    banned_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)


class AdminUser(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime)

    def set_password(self, pwd): self.password_hash = generate_password_hash(pwd)
    def check_password(self, pwd): return check_password_hash(self.password_hash, pwd)


# ==================== 反编译核心 ====================

# 注意：反编译过程是同步且耗时的。在生产环境中，如果访问量较大，
# 建议使用 Celery 等异步任务队列来处理反编译任务，以避免阻塞 Flask worker。
SHADOW_ALL_TYPES = {"math_number", "controller_shadow", "text", "logic_empty", "lists_get", "broadcast_input", "get_audios", "get_whole_audios", "get_current_costume", "default_value", "get_current_scene", "get_sensing_current_scene"}
SHADOW_ATTRS = {"math_number": {"name": "NUM", "constraints": "-Infinity,Infinity,0,", "allow_text": "true"}, "controller_shadow": {"name": "NUM", "constraints": "-Infinity,Infinity,0,false"}, "text": {"name": "TEXT"}, "lists_get": {"name": "VAR"}, "broadcast_input": {"name": "MESSAGE"}, "get_audios": {"name": "sound_id"}, "get_whole_audios": {"name": "sound_id"}, "get_current_costume": {"name": "style_id"}, "default_value": {"name": "TEXT", "has_been_edited": "false"}, "get_current_scene": {"name": "scene"}, "get_sensing_current_scene": {"name": "scene"}}
SHADOW_TEXTS = {"math_number": "0", "controller_shadow": "0", "text": "", "lists_get": "?", "broadcast_input": "Hi", "get_audios": "?", "get_whole_audios": "all", "get_current_costume": "", "default_value": "0", "get_current_scene": "", "get_sensing_current_scene": ""}

class DecompilerError(Exception): pass
class WorkNotFoundError(DecompilerError): pass

def rand_id(): return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(20))

def create_shadow(stype, bid=None, txt=None):
    if stype == "logic_empty": return f'<empty type="logic_empty" id="{bid}" visible="visible" editable="false"></empty>'
    bid, txt = bid or rand_id(), txt or SHADOW_TEXTS.get(stype, "")
    attrs = SHADOW_ATTRS.get(stype, {})
    s = ElementTree.Element("shadow"); s.set("type", stype); s.set("id", bid); s.set("visible", "visible"); s.set("editable", "true")
    f = ElementTree.SubElement(s, "field")
    for n, v in attrs.items(): f.set(n, v)
    f.text = str(txt)
    return ElementTree.tostring(s, encoding='unicode')


class CodemaoAPI:
    @staticmethod
    def get_work_info(wid):
        try:
            r = requests.get(f"https://api.codemao.cn/creation-tools/v1/works/{wid}", timeout=30)
            if r.status_code != 200: raise WorkNotFoundError(f"作品不存在: {wid}")
            d = r.json()
            return {"id": d["id"], "name": d["work_name"], "type": d["type"], "version": d["bcm_version"], "author_id": d["user_info"]["id"], "author_name": d["user_info"]["nickname"]}
        except (KeyError, json.JSONDecodeError): raise WorkNotFoundError(f"作品不存在: {wid}")

    @staticmethod
    def get_compiled_url(info):
        wid, wt = info["id"], info["type"]
        if wt in ("KITTEN4", "KITTEN3", "KITTEN2"):
            return requests.get(f"https://api-creation.codemao.cn/kitten/r2/work/player/load/{wid}", timeout=30).json()["source_urls"][0]
        elif wt == "COCO":
            return requests.get(f"https://api-creation.codemao.cn/coconut/web/work/{wid}/load", timeout=30).json()["data"]["bcmc_url"]
        raise DecompilerError(f"不支持的作品类型: {wt}")


class BlockDecompiler:
    def __init__(self, compiled, actor): self.compiled, self.actor, self.block, self.conn, self.shadows, self.fields = compiled, actor, {}, {}, {}, {}
    def start(self): self._info(); self._nexts(); self._children(); self._conds(); self._params(); return self.block
    def _info(self):
        self.id = self.block["id"] = self.compiled["id"]; self.type = self.block["type"] = self.compiled["type"]
        self.block.update({"location": [0, 0], "is_shadow": self.type in SHADOW_ALL_TYPES, "collapsed": False, "disabled": False, "deletable": True, "movable": True, "editable": True, "visible": "visible", "shadows": self.shadows, "fields": self.fields, "field_constraints": {}, "field_extra_attr": {}, "comment": None, "mutation": "", "parent_id": None, "is_output": self.type in SHADOW_ALL_TYPES or self.type in {"logic_boolean", "procedures_2_stable_parameter"}})
        self.actor.conns[self.id] = self.conn; self.actor.blocks[self.id] = self.block
    def _nexts(self):
        if "next_block" in self.compiled:
            nb = get_block_decompiler(self.compiled["next_block"], self.actor).start(); nb["parent_id"] = self.id; self.conn[nb["id"]] = {"type": "next"}
    def _children(self):
        if "child_block" in self.compiled:
            for i, c in enumerate(self.compiled["child_block"]):
                if c:
                    cb = get_block_decompiler(c, self.actor).start(); cb["parent_id"] = self.id; n = self._child_name(i); self.conn[cb["id"]] = {"type": "input", "input_type": "statement", "input_name": n}; self.shadows[n] = ""
    def _child_name(self, i): return "DO"
    def _conds(self):
        if "conditions" in self.compiled:
            for i, c in enumerate(self.compiled["conditions"]):
                cb = get_block_decompiler(c, self.actor).start(); cb["parent_id"] = self.id; n = f"IF{i}"
                if cb["type"] != "logic_empty": self.conn[cb["id"]] = {"type": "input", "input_type": "value", "input_name": n}
                self.shadows[n] = create_shadow("logic_empty", cb["id"])
    def _params(self):
        for n, v in self.compiled.get("params", {}).items():
            if isinstance(v, dict):
                pb = get_block_decompiler(v, self.actor).start(); pb["parent_id"] = self.id; pt = pb["type"]
                if pt in SHADOW_ALL_TYPES:
                    for fn, fv in pb["fields"].items(): self.shadows[n] = create_shadow(pt, pb["id"], fv)
                else: self.shadows[n] = create_shadow("logic_empty" if n in {"condition", "BOOL"} else "math_number")
                self.conn[pb["id"]] = {"type": "input", "input_type": "value", "input_name": n}
            else: self.fields[n] = v

class ControlsIfDecompiler(BlockDecompiler):
    def start(self):
        super().start(); ch = self.compiled["child_block"]
        if len(ch) == 2 and ch[-1] is None: self.shadows["EXTRA_ADD_ELSE"] = ""
        else: self.block["mutation"] = f'<mutation elseif="{len(self.compiled["conditions"]) - 1}" else="1"></mutation>'; self.shadows["ELSE_TEXT"] = ""
        return self.block
    def _child_name(self, i): return f"DO{i}" if i < len(self.compiled["conditions"]) else "ELSE"

class ProcDefDecompiler(BlockDecompiler):
    def start(self):
        self._info(); self._children(); self.shadows["PROCEDURES_2_DEFNORETURN_DEFINE"] = ""; self.shadows["PROCEDURES_2_DEFNORETURN_MUTATOR"] = ""; self.fields["NAME"] = self.compiled["procedure_name"]
        m = ElementTree.Element("mutation")
        for i, (pn, _) in enumerate(self.compiled.get("params", {}).items()):
            ni = f"PARAMS{i}"; ElementTree.SubElement(m, "arg").set("name", ni); self.shadows[ni] = create_shadow("math_number")
            pb = get_block_decompiler({"id": rand_id(), "kind": "domain_block", "type": "procedures_2_stable_parameter", "params": {"param_name": pn, "param_default_value": ""}}, self.actor).start(); pb["parent_id"] = self.block["id"]; self.conn[pb["id"]] = {"type": "input", "input_type": "value", "input_name": ni}
        self.block["mutation"] = ElementTree.tostring(m, encoding='unicode'); return self.block
    def _child_name(self, i): return "STACK"

class ProcCallDecompiler(BlockDecompiler):
    def start(self):
        self._info(); self._nexts(); n = self.compiled["procedure_name"]
        try: fid = self.actor.work.functions[n]["id"]
        except: fid, self.block["disabled"] = rand_id(), True
        self.shadows["NAME"], self.fields["NAME"] = "", n; m = ElementTree.Element("mutation"); m.set("name", n); m.set("def_id", fid)
        for i, (pn, v) in enumerate(self.compiled.get("params", {}).items()):
            pb = get_block_decompiler(v, self.actor).start(); self.shadows[f"ARG{i}"] = create_shadow("default_value", pb["id"]); ElementTree.SubElement(m, "procedures_2_parameter_shadow").set("name", pn); self.conn[pb["id"]] = {"type": "input", "input_type": "value", "input_name": f"ARG{i}"}
        self.block["mutation"] = ElementTree.tostring(m, encoding='unicode'); return self.block

SPECIAL = {"controls_if": ControlsIfDecompiler, "controls_if_no_else": ControlsIfDecompiler, "procedures_2_defnoreturn": ProcDefDecompiler, "procedures_2_return_value": ProcDefDecompiler, "procedures_2_callnoreturn": ProcCallDecompiler, "procedures_2_callreturn": ProcCallDecompiler}
def get_block_decompiler(c, a): return SPECIAL.get(c["type"], BlockDecompiler)(c, a)

class ActorDecompiler:
    def __init__(self, work, actor, compiled): self.work, self.actor, self.compiled, self.blocks, self.conns = work, actor, compiled, {}, {}
    def prepare(self): self.actor["block_data_json"] = {"blocks": self.blocks, "connections": self.conns, "comments": {}}; [self.work.functions.__setitem__(n, f) for n, f in self.compiled.get("procedures", {}).items()]
    def start(self):
        [self.work.functions.__setitem__(n, ProcDefDecompiler(f, self).start()) for n, f in self.compiled.get("procedures", {}).items()]
        [get_block_decompiler(b, self).start() for b in self.compiled.get("compiled_block_map", {}).values()]

class KittenDecompiler:
    def __init__(self, info, work): self.info, self.work, self.functions = info, work, {}
    def start(self):
        ds = [ActorDecompiler(self, self._get_actor(a["id"]), a) for a in self.work.get("compile_result", [])]
        [d.prepare() for d in ds]; [d.start() for d in ds]; self._write(); self._clean(); return self.work
    def _get_actor(self, aid): t = self.work.get("theatre", {}); return t.get("actors", {}).get(aid) or t.get("scenes", {}).get(aid, {})
    def _clean(self): [self.work.pop(k, None) for k in ["compile_result", "preview", "author_nickname"]]
    def _write(self):
        order = ["event", "control", "action", "appearance", "audio", "pen", "sensing", "operator", "data", "data", "procedure", "mobile_control", "physic", "physics2", "cloud_variable", "cloud_list", "advanced", "ai_lab", "ai_game", "cognitive", "camera", "video", "wood", "arduino", "weeemake", "microbit", "ai", "midimusic"]
        self.work["last_toolbox_order"] = order
        self.work.update({"hidden_toolbox": {"toolbox": [], "blocks": []}, "work_source_label": 0, "sample_id": "", "project_name": self.info["name"], "toolbox_order": order})

class CoCoDecompiler:
    def __init__(self, info, work): self.info, self.work = info, work
    def start(self): self._write(); self._clean(); return self.work
    def _clean(self): [self.work.pop(k, None) for k in ["id", "screenList", "widgetMap", "variableMap", "gridMap", "blockJsonMap", "initialScreenId", "apiToken", "imageFileMap", "soundFileMap", "iconFileMap", "fontFileMap", "blockCode"]]
    def _write(self):
        self.work.update({"authorId": self.info["author_id"], "title": self.info["name"], "screens": {}, "screenIds": [], "globalVariableList": [], "globalArrayList": [], "globalObjectList": [], "globalWidgets": self.work.get("widgetMap", {}), "globalWidgetIds": list(self.work.get("widgetMap", {}).keys()), "sourceTag": 1, "sourceId": ""})
        for s in self.work.get("screenList", []):
            sid = s["id"]; s["snapshot"] = ""; self.work["screens"][sid] = s; self.work["screenIds"].append(sid); s.update({"primitiveVariables": [], "arrayVariables": [], "objectVariables": [], "broadcasts": ["Hi"], "widgets": {}})
            for wid in s.get("widgetIds", []) + s.get("invisibleWidgetIds", []):
                if wid in self.work.get("widgetMap", {}): s["widgets"][wid] = self.work["widgetMap"][wid]
        self.work["blockly"] = {sid: {"screenId": sid, "workspaceJson": blks, "workspaceOffset": {"x": 0, "y": 0}} for sid, blks in self.work.get("blockJsonMap", {}).items()}
        for k, lk in [("imageFileMap", "imageFileList"), ("soundFileMap", "soundFileList"), ("iconFileMap", "iconFileList"), ("fontFileMap", "fontFileList")]: self.work[lk] = list(self.work.get(k, {}).values())

class Decompiler:
    @staticmethod
    def decompile(wid):
        info = CodemaoAPI.get_work_info(wid); url = CodemaoAPI.get_compiled_url(info)
        r = requests.get(url, timeout=60)
        if r.status_code != 200: raise DecompilerError(f"获取编译文件失败: HTTP {r.status_code}")
        work = r.json(); wt = info["type"]
        return info, (KittenDecompiler if wt in ("KITTEN4", "KITTEN3", "KITTEN2") else CoCoDecompiler)(info, work).start()


# ==================== 工具函数 ====================

def get_ip():
    if request.headers.get('X-Forwarded-For'): return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def check_banned(ip, wid):
    bip = BannedIP.query.filter_by(ip_address=ip).first()
    if bip and (not bip.expires_at or bip.expires_at > datetime.utcnow()): return True, f"IP已被封禁: {bip.reason or '无原因'}"
    bw = BannedWork.query.filter_by(work_id=wid).first()
    if bw: return True, f"作品已被禁止反编译: {bw.reason or '无原因'}"
    return False, None

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if not session.get('admin_id'): return jsonify({'success': False, 'error': '未授权'}), 401
        admin = AdminUser.query.get(session['admin_id'])
        if not admin: return jsonify({'success': False, 'error': '管理员不存在'}), 401
        request.admin = admin; return f(*a, **kw)
    return d


# ==================== 路由 ====================

@app.route('/')
def index(): return INDEX_HTML

@app.route('/admin')
def admin_page(): return ADMIN_HTML

@app.route('/api/decompile', methods=['POST'])
def api_decompile():
    d = request.get_json()
    if not d or 'work_id' not in d: return jsonify({'success': False, 'error': '请提供作品ID'}), 400
    try: wid = int(d['work_id'])
    except: return jsonify({'success': False, 'error': '作品ID必须是数字'}), 400
    if wid <= 0: return jsonify({'success': False, 'error': '作品ID无效'}), 400
    ip = get_ip(); banned, reason = check_banned(ip, wid)
    if banned: return jsonify({'success': False, 'error': reason}), 403
    rec = DecompilerRecord(work_id=wid, client_ip=ip, status='pending'); db.session.add(rec); db.session.commit()
    try:
        info, src = Decompiler.decompile(wid)
        ext = {"KITTEN4": ".bcm4", "KITTEN3": ".bcm", "COCO": ".json"}.get(info['type'], ".json")
        fp = os.path.join(app.config['UPLOAD_FOLDER'], f"{wid}_{rec.id}{ext}")
        with open(fp, 'w', encoding='utf-8') as f: json.dump(src, f, ensure_ascii=False, indent=2)
        fs = os.path.getsize(fp); exp = datetime.utcnow() + timedelta(minutes=app.config['FILE_EXPIRE_MINUTES'])
        rec.work_name, rec.work_type, rec.author_name, rec.file_path, rec.file_size, rec.status, rec.expires_at = info['name'], info['type'], info['author_name'], fp, fs, 'success', exp
        db.session.commit()
        return jsonify({'success': True, 'data': {'record_id': rec.id, 'work_id': wid, 'work_name': info['name'], 'work_type': info['type'], 'author_name': info['author_name'], 'file_size': fs, 'download_url': f"/api/download/{rec.id}", 'expires_at': exp.isoformat()}})
    except WorkNotFoundError:
        rec.status, rec.error_message = 'not_found', f'作品不存在: {wid}'; db.session.commit()
        return jsonify({'success': False, 'error': f'作品不存在: {wid}'}), 404
    except Exception as e:
        rec.status, rec.error_message = 'error', str(e); db.session.commit()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/records')
def api_records():
    page = request.args.get('page', 1, type=int); per = min(request.args.get('per_page', 20, type=int), 100)
    recs = DecompilerRecord.query.filter_by(status='success').order_by(DecompilerRecord.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
    return jsonify({'success': True, 'data': {'records': [r.to_dict() for r in recs.items], 'total': recs.total, 'page': page, 'per_page': per, 'pages': recs.pages}})

@app.route('/api/download/<int:rid>')
def api_download(rid):
    rec = DecompilerRecord.query.get(rid)
    if not rec: return jsonify({'success': False, 'error': '记录不存在'}), 404
    if rec.status != 'success': return jsonify({'success': False, 'error': f'文件不可用: {rec.status}'}), 400
    if not rec.file_path or not os.path.exists(rec.file_path): return jsonify({'success': False, 'error': '文件已过期'}), 404
    if rec.expires_at and rec.expires_at < datetime.utcnow():
        try: os.remove(rec.file_path)
        except: pass
        rec.file_path = None; db.session.commit()
        return jsonify({'success': False, 'error': '文件已过期'}), 410
    rec.download_count += 1; db.session.commit()
    return send_file(rec.file_path, as_attachment=True, download_name=f"{rec.work_name or rec.work_id}{os.path.splitext(rec.file_path)[1]}", mimetype='application/json')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    d = request.get_json()
    if not d or 'username' not in d or 'password' not in d: return jsonify({'success': False, 'error': '请输入用户名和密码'}), 400
    admin = AdminUser.query.filter_by(username=d['username']).first()
    if not admin or not admin.check_password(d['password']): return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
    admin.last_login = datetime.utcnow(); db.session.commit(); session['admin_id'] = admin.id
    return jsonify({'success': True, 'data': {'admin': {'id': admin.id, 'username': admin.username}}})

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout(): session.pop('admin_id', None); return jsonify({'success': True})

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    return jsonify({'success': True, 'data': {'total_records': DecompilerRecord.query.count(), 'success_records': DecompilerRecord.query.filter_by(status='success').count(), 'today_records': DecompilerRecord.query.filter(DecompilerRecord.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)).count(), 'banned_works': BannedWork.query.count(), 'banned_ips': BannedIP.query.count()}})

@app.route('/api/admin/records')
@admin_required
def admin_records():
    page = request.args.get('page', 1, type=int); per = min(request.args.get('per_page', 20, type=int), 100)
    q = DecompilerRecord.query
    if request.args.get('status'): q = q.filter_by(status=request.args['status'])
    if request.args.get('work_id'): q = q.filter_by(work_id=int(request.args['work_id']))
    recs = q.order_by(DecompilerRecord.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
    return jsonify({'success': True, 'data': {'records': [r.to_dict() for r in recs.items], 'total': recs.total, 'page': page, 'per_page': per, 'pages': recs.pages}})

@app.route('/api/admin/records/<int:rid>', methods=['DELETE'])
@admin_required
def admin_del_record(rid):
    rec = DecompilerRecord.query.get(rid)
    if not rec: return jsonify({'success': False, 'error': '记录不存在'}), 404
    if rec.file_path and os.path.exists(rec.file_path): os.remove(rec.file_path)
    db.session.delete(rec); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/banned-works')
@admin_required
def admin_banned_works():
    page = request.args.get('page', 1, type=int); per = min(request.args.get('per_page', 20, type=int), 100)
    ws = BannedWork.query.order_by(BannedWork.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
    return jsonify({'success': True, 'data': {'works': [{'id': w.id, 'work_id': w.work_id, 'work_name': w.work_name, 'reason': w.reason, 'banned_by': w.banned_by, 'created_at': w.created_at.isoformat() if w.created_at else None} for w in ws.items], 'total': ws.total, 'pages': ws.pages}})

@app.route('/api/admin/banned-works', methods=['POST'])
@admin_required
def admin_add_banned_work():
    d = request.get_json()
    if not d or 'work_id' not in d: return jsonify({'success': False, 'error': '请提供作品ID'}), 400
    if BannedWork.query.filter_by(work_id=d['work_id']).first(): return jsonify({'success': False, 'error': '已在封禁列表'}), 400
    db.session.add(BannedWork(work_id=d['work_id'], work_name=d.get('work_name'), reason=d.get('reason'), banned_by=request.admin.username)); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/banned-works/<int:wid>', methods=['DELETE'])
@admin_required
def admin_del_banned_work(wid):
    w = BannedWork.query.filter_by(work_id=wid).first()
    if not w: return jsonify({'success': False, 'error': '不在封禁列表'}), 404
    db.session.delete(w); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/banned-ips')
@admin_required
def admin_banned_ips():
    page = request.args.get('page', 1, type=int); per = min(request.args.get('per_page', 20, type=int), 100)
    ips = BannedIP.query.order_by(BannedIP.created_at.desc()).paginate(page=page, per_page=per, error_out=False)
    return jsonify({'success': True, 'data': {'ips': [{'id': i.id, 'ip_address': i.ip_address, 'reason': i.reason, 'expires_at': i.expires_at.isoformat() if i.expires_at else None, 'created_at': i.created_at.isoformat() if i.created_at else None} for i in ips.items], 'total': ips.total, 'pages': ips.pages}})

@app.route('/api/admin/banned-ips', methods=['POST'])
@admin_required
def admin_add_banned_ip():
    d = request.get_json()
    if not d or 'ip_address' not in d: return jsonify({'success': False, 'error': '请提供IP地址'}), 400
    if BannedIP.query.filter_by(ip_address=d['ip_address']).first(): return jsonify({'success': False, 'error': '已在封禁列表'}), 400
    exp = datetime.utcnow() + timedelta(hours=d['duration_hours']) if d.get('duration_hours') else None
    db.session.add(BannedIP(ip_address=d['ip_address'], reason=d.get('reason'), banned_by=request.admin.username, expires_at=exp)); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/banned-ips/<ip>', methods=['DELETE'])
@admin_required
def admin_del_banned_ip(ip):
    i = BannedIP.query.filter_by(ip_address=ip).first()
    if not i: return jsonify({'success': False, 'error': '不在封禁列表'}), 404
    db.session.delete(i); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/change-password', methods=['POST'])
@admin_required
def admin_change_password():
    d = request.get_json()
    if not d or 'old_password' not in d or 'new_password' not in d:
        return jsonify({'success': False, 'error': '请提供旧密码和新密码'}), 400
    
    admin = request.admin
    if not admin.check_password(d['old_password']):
        return jsonify({'success': False, 'error': '旧密码错误'}), 400
    
    admin.set_password(d['new_password'])
    db.session.commit()
    return jsonify({'success': True})


# ==================== 初始化 ====================

def cleanup_expired_files():
    """定时清理过期文件"""
    while True:
        try:
            with app.app_context():
                expired = DecompilerRecord.query.filter(DecompilerRecord.expires_at < datetime.utcnow(), DecompilerRecord.file_path.isnot(None)).all()
                for rec in expired:
                    if rec.file_path and os.path.exists(rec.file_path):
                        try: os.remove(rec.file_path)
                        except: pass
                    rec.file_path = None
                db.session.commit()
                if expired: print(f"[{datetime.now()}] 已清理 {len(expired)} 个过期文件")
        except Exception as e: print(f"清理文件时出错: {e}")
        time.sleep(600)  # 每10分钟检查一次

with app.app_context():
    db.create_all()
    if not AdminUser.query.first():
        admin = AdminUser(username=app.config['ADMIN_USERNAME'])
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin); db.session.commit()
    
    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_expired_files, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════════════╗
║         编程猫作品反编译服务已启动                          ║
╠════════════════════════════════════════════════════════════╣
║  访问地址: http://localhost:5000
║  后台管理: http://localhost:5000/admin
╚════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)
