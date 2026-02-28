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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}"
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

# 内存检查与 SWAP 预处理 (必须在所有安装操作之前)
check_ram_pre() {
    # 获取可用内存 (Available)
    local available_mem=$(free -m | awk '/^Mem:/{print $7}')
    [ -z "$available_mem" ] && available_mem=$(free -m | awk '/^Mem:/{print $4 + $6}')
    
    local swap_total=$(free -m | awk '/^Swap:/{print $2}')
    
    print_step "系统资源检查:"
    print_info "系统可用物理内存: ${available_mem}MB"
    print_info "当前 SWAP 分区: ${swap_total}MB"
    
    # 如果物理内存极低且没有 SWAP，优先处理 SWAP
    if [ "$available_mem" -lt 800 ] && [ "$swap_total" -lt 512 ]; then
        print_warn "检测到您的服务器内存非常紧张，且未开启虚拟内存 (SWAP)。"
        print_warn "这会导致安装过程中系统强制杀死进程 (Killed)。"
        read -p "是否立即创建 2GB 虚拟内存以保证安装成功? [Y/n]: " create_swap
        if [[ "$create_swap" =~ ^[Yy]|^$ ]]; then
            print_step "正在紧急创建 SWAP 分区..."
            # 停止可能占用内存的进程(可选，但这里不做，以免误杀用户进程)
            dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
            chmod 600 /swapfile
            mkswap /swapfile
            swapon /swapfile
            print_info "SWAP 分区已启用，安装环境已加固。"
        fi
    fi
}

check_ram_pre

# 显示Banner
show_banner

# 交互式配置函数
interactive_config() {
    print_step "进入交互式配置模式 (直接回车保持默认):"
    
    read -p "请输入安装目录 [默认: ${APP_DIR}]: " input_dir
    [ -n "$input_dir" ] && APP_DIR="$input_dir"
    
    read -p "请输入服务端口 [默认: ${APP_PORT}]: " input_port
    [ -n "$input_port" ] && APP_PORT="$input_port"
    
    read -p "请输入访问域名 [默认: ${DOMAIN:-无}]: " input_domain
    [ -n "$input_domain" ] && DOMAIN="$input_domain"
    
    read -p "请输入管理员账号 [默认: ${ADMIN_USER}]: " input_user
    [ -n "$input_user" ] && ADMIN_USER="$input_user"
    
    read -p "请输入管理员密码 [默认: 自动生成]: " input_pass
    [ -n "$input_pass" ] && ADMIN_PASS="$input_pass"
}

# 生成随机密码
generate_password() {
    openssl rand -base64 12 | tr -d '/+=' | head -c 16
}

# 如果没有通过命令行参数提供域名，或者明确要求交互，则进入交互模式
if [ -z "$DOMAIN" ]; then
    interactive_config
fi

if [ -z "$ADMIN_PASS" ]; then
    ADMIN_PASS=$(generate_password)
fi

# 生成密钥
generate_secret() {
    openssl rand -hex 32
}

SECRET_KEY=$(generate_secret)

print_step "最终配置预览:"
echo "  - 安装目录: ${APP_DIR}"
echo "  - 服务端口: ${APP_PORT}"
echo "  - 域名: ${DOMAIN:-未设置 (将仅通过IP访问)}"
echo "  - 管理员: ${ADMIN_USER}"
echo "  - 密码: ${ADMIN_PASS}"
echo "  - SSL: ${WITH_SSL}"
echo ""

read -p "确认开始部署? [Y/n]: " confirm
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
print_step "安装系统依赖 (可能需要几分钟)..."

# 检查是否已安装必要组件
check_installed() {
    if command -v python3 &>/dev/null && command -v nginx &>/dev/null && command -v git &>/dev/null; then
        return 0
    else
        return 1
    fi
}

if check_installed; then
    print_info "检测到系统已预装必要依赖，跳过包管理器更新以节省内存。"
else
    if [ "$PKG_MANAGER" = "dnf" ]; then
        # 增加内存限制优化
        for i in {1..3}; do
            print_info "正在通过 DNF 安装依赖 (尝试次数: $i)..."
            # 彻底静默，减少输出导致的内存压力
            dnf install -y python3 python3-pip python3-devel git nginx --setopt=install_weak_deps=False --nodocs -q && break
            print_warn "DNF 安装遇到问题，正在清理重试..."
            dnf clean all -q
            sleep 5
        done
        
        if ! command -v supervisord &> /dev/null; then
            dnf install -y supervisor --setopt=install_weak_deps=False --nodocs -q || pip3 install supervisor -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -q
        fi
    else
        apt update -qq
        apt install -y python3 python3-pip python3-venv git nginx supervisor -qq
    fi
fi

# 3. 创建必要目录
print_step "创建必要目录..."
mkdir -p ${APP_DIR}/files
mkdir -p ${APP_DIR}/logs

# 4. 创建虚拟环境并安装依赖
print_step "创建Python虚拟环境并安装依赖 (使用清华镜像源)..."
cd ${APP_DIR}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir
pip install gunicorn -q -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir
deactivate

# 5. 创建环境配置
print_step "创建环境配置..."
cat > ${APP_DIR}/.env << EOF
# 生产环境配置
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}
PORT=${APP_PORT}
HOST=0.0.0.0
FILE_EXPIRE_MINUTES=20
DATABASE_URL=sqlite:///data.db
UPLOAD_FOLDER=files
EOF

# 6. 创建 Systemd 服务
print_step "创建 Systemd 服务..."
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Codemao Decompiler Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 4 --threads 2 --bind 0.0.0.0:${APP_PORT} --timeout 120 --access-logfile ${APP_DIR}/logs/access.log --error-logfile ${APP_DIR}/logs/error.log 'app:app'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. 创建 Nginx 配置
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

# 8. 设置权限
print_step "设置文件权限..."
chown -R root:root ${APP_DIR}
chmod -R 755 ${APP_DIR}
chmod -R 777 ${APP_DIR}/files
chmod -R 777 ${APP_DIR}/logs
chmod 600 ${APP_DIR}/.env

# 9. 启动服务
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

# 10. 配置防火墙
print_step "配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http 2>/dev/null || true
    firewall-cmd --permanent --add-service=https 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi

# 11. 显示结果
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
