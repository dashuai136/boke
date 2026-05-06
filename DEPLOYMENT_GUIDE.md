# 部署指南：长期后台守护 + 域名公网访问

## 1) 服务器准备
- Ubuntu 22.04+
- 创建用户：`sudo useradd -r -m -d /opt/begonia -s /usr/sbin/nologin begonia`
- 目录：
  - `/opt/begonia`（代码）
  - `/var/lib/begonia`（SQLite 数据）
  - `/var/log/begonia`（日志）

## 2) systemd 常驻运行（推荐）
1. 复制服务文件：
   - `deploy/systemd/begonia-web.service` -> `/etc/systemd/system/begonia-web.service`
2. 创建数据目录并授权：
   - `sudo mkdir -p /var/lib/begonia /var/log/begonia`
   - `sudo chown -R begonia:begonia /var/lib/begonia /var/log/begonia /opt/begonia`
3. 启动：
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable --now begonia-web`
4. 检查：
   - `sudo systemctl status begonia-web`
   - `curl http://127.0.0.1:8080/api/species`

## 3) supervisor 常驻运行（备选）
1. 复制配置：
   - `deploy/supervisor/begonia-web.conf` -> `/etc/supervisor/conf.d/begonia-web.conf`
2. 生效：
   - `sudo supervisorctl reread`
   - `sudo supervisorctl update`
   - `sudo supervisorctl status begonia-web`

## 4) 域名 + HTTPS + 公网
1. DNS：把 `A` 记录指向服务器公网 IP（例如 `flora.example.org`）。
2. Nginx：
   - `deploy/nginx/begonia.conf` -> `/etc/nginx/sites-available/begonia.conf`
   - 替换 `CHANGE_ME_DOMAIN`
   - `sudo ln -s /etc/nginx/sites-available/begonia.conf /etc/nginx/sites-enabled/begonia.conf`
   - `sudo nginx -t && sudo systemctl reload nginx`
3. 证书（Let’s Encrypt）：
   - `sudo certbot certonly --webroot -w /var/www/certbot -d flora.example.org`
   - `sudo systemctl reload nginx`
4. 公网验收：
   - `https://flora.example.org/`
   - `https://flora.example.org/api/species`

## 5) 运维检查清单
- 健康检查：`/api/species?page_size=1` 200
- 日志轮转：`/var/log/begonia/*.log`
- 备份：每日备份 `/var/lib/begonia/begonia.db`
- 回滚：保留最近 7 版代码 + 数据快照
