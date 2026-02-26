#!/bin/bash
# ====================================
# Codemao Decompiler 一键部署脚本
# 适用于 CentOS 9 / Rocky Linux 9
# 支持宝塔面板环境
# ====================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 显示Banner
show_banner() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}         编程猫作品反编译器 - 一键部署脚本                  ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}         Codemao Decompiler Auto Deployer                    ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -d, --domain <域名>      设置访问域名"
    echo "  -p, --port <端口>        设置服务端口 (默认: 5000)"
    echo "  -u, --user <用户名>      设置管理员用户名 (默认: admin)"
    echo "  -w, --password <密码>    设置管理员密码 (默认: 随机生成)"
    echo "  --app-dir <目录>         设置安装目录 (默认: /opt/codemao-decompiler)"
    echo "  --with-ssl               自动配置SSL证书 (需要域名)"
    echo "  --uninstall              卸载服务"
    echo "  -h, --help               显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -d example.com -u admin -w mypassword"
    echo "  $0 -d example.com --with-ssl"
    echo "  $0 --uninstall"
    exit 0
}

# 默认配置
APP_NAME="codemao-decompiler"
APP_DIR="/opt/${APP_NAME}"
APP_PORT=5000
DOMAIN=""
ADMIN_USER="admin"
ADMIN_PASS=""
WITH_SSL=false
UNINSTALL=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -p|--port)
            APP_PORT="$2"
            shift 2
            ;;
        -u|--user)
            ADMIN_USER="$2"
            shift 2
            ;;
        -w|--password)
            ADMIN_PASS="$2"
            shift 2
            ;;
        --app-dir)
            APP_DIR="$2"
            shift 2
            ;;
        --with-ssl)
            WITH_SSL=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            ;;
    esac
done

# 卸载函数
uninstall() {
    print_info "开始卸载服务..."
    
    # 停止服务
    systemctl stop ${APP_NAME} 2>/dev/null || true
    systemctl disable ${APP_NAME} 2>/dev/null || true
    
    # 删除服务文件
    rm -f /etc/systemd/system/${APP_NAME}.service
    rm -f /etc/nginx/conf.d/${APP_NAME}.conf
    rm -f /etc/supervisord.d/${APP_NAME}.ini 2>/dev/null || true
    
    # 重载systemd
    systemctl daemon-reload
    
    # 删除应用目录
    if [ -d "${APP_DIR}" ]; then
        read -p "是否删除应用目录 ${APP_DIR}? [y/N]: " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            rm -rf ${APP_DIR}
            print_info "应用目录已删除"
        fi
    fi
    
    print_info "卸载完成"
    exit 0
}

# 执行卸载
if [ "$UNINSTALL" = true ]; then
    uninstall
fi

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    print_error "请使用root用户运行此脚本"
    exit 1
fi

# 显示Banner
show_banner

# 生成随机密码
generate_password() {
    openssl rand -base64 12 | tr -d '/+=' | head -c 16
}

if [ -z "$ADMIN_PASS" ]; then
    ADMIN_PASS=$(generate_password)
fi

# 生成密钥
generate_secret() {
    openssl rand -hex 32
}

SECRET_KEY=$(generate_secret)

print_step "配置信息:"
echo "  - 安装目录: ${APP_DIR}"
echo "  - 服务端口: ${APP_PORT}"
echo "  - 域名: ${DOMAIN:-未设置}"
echo "  - 管理员: ${ADMIN_USER}"
echo "  - 密码: ${ADMIN_PASS}"
echo "  - SSL: ${WITH_SSL}"
echo ""

read -p "确认以上配置? [Y/n]: " confirm
if [[ ! "$confirm" =~ ^[Yy]|^$ ]]; then
    print_info "已取消安装"
    exit 0
fi

# 1. 检查系统
print_step "检查系统环境..."
if [ -f /etc/centos-release ] || [ -f /etc/rocky-release ] || [ -f /etc/almalinux-release ]; then
    PKG_MANAGER="dnf"
    print_info "检测到 RHEL/CentOS/Rocky Linux 系统"
elif [ -f /etc/debian_version ]; then
    PKG_MANAGER="apt"
    print_info "检测到 Debian/Ubuntu 系统"
else
    print_warn "未检测到支持的系统，尝试继续安装..."
    PKG_MANAGER="dnf"
fi

# 2. 安装系统依赖
print_step "安装系统依赖..."
if [ "$PKG_MANAGER" = "dnf" ]; then
    dnf install -y python3 python3-pip python3-devel git nginx
    # 检查是否安装supervisor
    if ! command -v supervisord &> /dev/null; then
        dnf install -y supervisor || pip3 install supervisor
    fi
else
    apt update
    apt install -y python3 python3-pip python3-venv git nginx supervisor
fi

# 3. 创建应用目录
print_step "创建应用目录..."
mkdir -p ${APP_DIR}
mkdir -p ${APP_DIR}/data
mkdir -p ${APP_DIR}/data/files
mkdir -p ${APP_DIR}/logs

# 4. 复制项目文件
print_step "复制项目文件..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 复制必要文件
cp -r ${SCRIPT_DIR}/app ${APP_DIR}/
cp ${SCRIPT_DIR}/run.py ${APP_DIR}/
cp ${SCRIPT_DIR}/requirements.txt ${APP_DIR}/

# 5. 创建虚拟环境并安装依赖
print_step "创建Python虚拟环境..."
cd ${APP_DIR}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install gunicorn -q
deactivate

# 6. 创建环境配置
print_step "创建环境配置..."
cat > ${APP_DIR}/.env << EOF
# 生产环境配置
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}
PORT=${APP_PORT}
HOST=127.0.0.1
FILE_EXPIRE_MINUTES=20

# 数据库配置 (默认SQLite，可切换MySQL)
# DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
EOF

# 7. 创建 Systemd 服务
print_step "创建 Systemd 服务..."
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Codemao Decompiler Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 4 --threads 2 --bind 127.0.0.1:${APP_PORT} --timeout 120 --access-logfile ${APP_DIR}/logs/access.log --error-logfile ${APP_DIR}/logs/error.log 'run:app'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. 创建 Nginx 配置
print_step "创建 Nginx 配置..."
if [ -n "${DOMAIN}" ]; then
    cat > /etc/nginx/conf.d/${APP_NAME}.conf << EOF
upstream ${APP_NAME} {
    server 127.0.0.1:${APP_PORT};
    keepalive 32;
}

server {
    listen 80;
    server_name ${DOMAIN};
    
    access_log ${APP_DIR}/logs/nginx_access.log;
    error_log ${APP_DIR}/logs/nginx_error.log;
    
    client_max_body_size 50M;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 限流
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://${APP_NAME};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static {
        alias ${APP_DIR}/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF
else
    print_warn "未设置域名，跳过 Nginx 配置"
fi

# 9. 设置权限
print_step "设置文件权限..."
chown -R root:root ${APP_DIR}
chmod -R 755 ${APP_DIR}
chmod -R 777 ${APP_DIR}/data
chmod -R 777 ${APP_DIR}/logs
chmod 600 ${APP_DIR}/.env

# 10. 启动服务
print_step "启动服务..."
systemctl daemon-reload
systemctl enable ${APP_NAME}
systemctl start ${APP_NAME}

if [ -n "${DOMAIN}" ]; then
    systemctl enable nginx
    systemctl restart nginx
    
    # SSL配置
    if [ "$WITH_SSL" = true ]; then
        print_step "配置SSL证书..."
        if command -v certbot &> /dev/null; then
            certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --register-unsafely-without-email || \
                print_warn "SSL证书配置失败，请手动配置"
        else
            print_warn "未安装certbot，跳过SSL配置"
        fi
    fi
fi

# 11. 配置防火墙
print_step "配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http 2>/dev/null || true
    firewall-cmd --permanent --add-service=https 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi

# 12. 显示结果
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}                   部署完成!                                ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "${DOMAIN}" ]; then
    echo -e "  访问地址: ${GREEN}http://${DOMAIN}${NC}"
    echo -e "  后台管理: ${GREEN}http://${DOMAIN}/admin${NC}"
else
    echo -e "  访问地址: ${GREEN}http://服务器IP:${APP_PORT}${NC}"
    echo -e "  后台管理: ${GREEN}http://服务器IP:${APP_PORT}/admin${NC}"
fi

echo ""
echo -e "  管理员账号: ${YELLOW}${ADMIN_USER}${NC}"
echo -e "  管理员密码: ${YELLOW}${ADMIN_PASS}${NC}"
echo ""
echo -e "  应用目录: ${APP_DIR}"
echo -e "  日志目录: ${APP_DIR}/logs"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  查看状态: systemctl status ${APP_NAME}"
echo "  重启服务: systemctl restart ${APP_NAME}"
echo "  查看日志: tail -f ${APP_DIR}/logs/error.log"
echo "  查看访问: tail -f ${APP_DIR}/logs/access.log"
echo ""
print_warn "请妥善保存管理员密码，并建议修改默认配置!"
