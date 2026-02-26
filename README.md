# 编程猫作品反编译器 (Codemao Decompiler)

[![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

一个功能强大、界面美观的编程猫作品反编译平台，支持 Kitten 2/3/4 和 CoCo 作品的源码提取。

## 📜 致谢与版权声明

**特别感谢原作者：[SLIGHTNING](https://gitee.com/slightning)**

本项目核心反编译逻辑基于开源项目 [Kitten-4-Decompiler](https://gitee.com/slightning/Kitten-4-Decompiler) 进行二次开发。我们在此基础上进行了：
- 现代化的 UI/UX 重新设计（基于 Bootstrap 5）
- 完善的后台管理系统（支持黑名单、统计、密码修改等）
- 稳定的 Web 服务封装与部署脚本优化

本项目严格遵守 **GNU Affero General Public License Version 3 (AGPLv3)** 开源协议。
根据协议，如果您基于本项目进行修改或提供网络服务，**必须**：
1. **保持开源**：向所有用户提供您的源代码。
2. **保留声明**：保留原作者 SLIGHTNING 的版权声明及本项目声明。
3. **同协议分发**：衍生作品必须同样采用 AGPLv3 协议。

## ✨ 功能特性

- **多版本支持**：兼容编程猫 Kitten 2/3/4 和 CoCo 引擎。
- **现代化 UI**：极简、美观、响应式的 Web 界面。
- **强大后台**：可视化管理反编译记录、封禁恶意作品/IP。
- **安全加固**：支持管理员密码修改、基于环境变量的配置。
- **一键部署**：提供完善的 Shell 脚本，支持 Linux 服务器快速上线。

## 📁 项目结构

```
codemao-decompiler/
├── app.py           # 主程序（所有代码都在这里）
├── requirements.txt # 依赖
├── deploy.sh        # 一键部署脚本
├── LICENSE          # AGPLv3协议
└── README.md        # 说明文档
```

## 🚀 宝塔部署

### 方法一：一键部署

```bash
chmod +x deploy.sh
./deploy.sh -d example.com
```

### 方法二：手动部署

1. **上传项目到服务器**
   - 将整个项目上传到 `/www/wwwroot/decompiler`

2. **安装依赖**
   ```bash
   cd /www/wwwroot/decompiler
   pip3 install -r requirements.txt
   ```

3. **启动服务**
   ```bash
   python3 app.py
   ```

4. **宝塔配置反向代理**
   - 网站 → 设置 → 反向代理 → 添加
   - 目标URL: `http://127.0.0.1:5000`

## 🔧 生产环境

使用 Gunicorn：

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

配置环境变量：

```bash
export SECRET_KEY="随机生成的密钥"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="你的密码"
```

## 📖 API

### 反编译作品
```bash
curl -X POST http://localhost:5000/api/decompile \
  -H "Content-Type: application/json" \
  -d '{"work_id": 12345678}'
```

### 下载文件
```bash
curl http://localhost:5000/api/download/1 -o source.bcm4
```

## 📜 开源协议

GNU Affero General Public License Version 3 (AGPLv3)
