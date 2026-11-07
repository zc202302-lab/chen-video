# Chen Video

基于 Jellyfin 的私人音视频库部署项目。代码由 GitHub 管理，媒体和运行数据仅保存在你指定的美国服务器。此项目不重新实现 Jellyfin 播放器，也不向 GitHub 上传媒体。

## 第一版范围

- 视频、系列课程、音乐和有声书媒体库。
- Jellyfin 原生合集、播放列表、已看状态和单个视频断点续播。
- 同一账号在不同设备间接续播放；按用户分别保存记录。
- Docker Compose 部署，可选 Caddy HTTPS，运行目录独立持久化。
- 停机一致性配置备份，包含用户、合集和进度数据库，不包含媒体。

合集用于归类，播放列表用于顺序播放；整个列表的一键续播不作为已实现功能。系列课程推荐按剧集组织。长音频续听、自动下一集及各客户端表现需在实际版本上验收。

## 部署

前置条件：Linux、Docker Engine 和 Compose 插件、Python 3。安装 Docker 请遵循官方文档，不通过本项目自动修改系统。先检查内存、磁盘、流量和现有端口占用；低配置 VPS 优先直接播放，不依赖实时视频转码。

```bash
git clone https://github.com/zc202302-lab/chen-video.git
cd chen-video
cp .env.example .env
```

编辑 `.env`：填写服务器媒体域名、邮箱、媒体管理用户的 `id -u` / `id -g`，以及独立的 `DATA_ROOT`。镜像默认使用官方渠道标签；正式部署前将镜像改为经过验证的发行标签或摘要，并记录版本。不要写入密码、令牌或私钥。

```bash
sudo python3 scripts/init.py
docker compose config --quiet
docker compose pull jellyfin
docker compose up -d jellyfin
```

8096 仅监听服务器回环地址。通过你电脑的 SSH 隧道完成初始设置：

```bash
ssh -L 18096:127.0.0.1:8096 用户名@服务器IP
```

电脑打开 `http://127.0.0.1:18096`，创建强密码管理员并完成向导。媒体路径见下表。确认初始向导完成后再开放 HTTPS。不要先把未初始化实例暴露到公网。

| 媒体库 | 容器内路径 | 组织建议 |
|---|---|---|
| 视频 | `/media/videos` | 家庭视频或其他适合的类型；关闭不需要的在线刮削 |
| 系列课程 | `/media/series` | 剧集类型，按季、集编号 |
| 音乐 | `/media/music` | 音乐类型 |
| 有声书 | `/media/audiobooks` | 书籍/有声书类型，实测断点续听 |

### 开启域名和 HTTPS

域名 A 记录直接指向美国服务器；如有 AAAA 记录，确保 IPv6 同样可达。不要接入内地缓存或中转。域名解析服务只解析地址。

确认服务器 TCP 80、443 空闲并放行，且初始化向导已完成，再运行：

```bash
docker compose --profile https config --quiet
docker compose --profile https up -d
docker compose --profile https logs --tail=50 caddy
```

访问 `https://你的媒体域名`。若现有服务占用 80/443，不要停掉现有服务，也不要启动本项目 Caddy；改用现有反向代理转发到 `127.0.0.1:8096`。若现有代理也在容器内，需要共享 Docker 网络或另行配置可达地址。

在 Jellyfin 网络设置中将实际反向代理 IP 加入 Known Proxies；可通过 `docker inspect` 查询 chen-video Caddy 容器的网络地址，容器重建后注意检查。不要把所有来源都设为可信代理。

## 使用与安全

通过 SFTP 将媒体上传至 `DATA_ROOT/media` 下对应目录，确保 PUID/PGID 有读取权限，然后扫描媒体库。媒体挂载为只读，Jellyfin 无法删除原文件；封面及元数据保存在 config。初版没有另行开发网页上传器。

管理员仅用于管理，日常建立普通用户，限制删除、管理和不必要的下载权限，隐藏登录页用户列表。低配置服务器为普通用户禁用视频转码并先使用浏览器兼容的视频格式。音乐播放列表不保证长音频断点续听；有声书需按专用类型配置并实测。续播有最小进度、剩余时长等阈值，应在播放设置中按实际用途调整。

首次建议关闭在线元数据抓取及第三方插件，避免文件标题等信息被发送给外部服务。服务端转码缓存、配置备份均放在美国服务器；观看设备仍会产生本地缓冲。不保证服务商自身的底层复制地域，严格地域要求需核对其合同。

## 备份、升级和验收

```bash
sudo bash scripts/backup.sh
```

备份会短暂停止 Jellyfin，然后自动启动。备份含敏感账号和观看记录，只留在受保护的境外存储，不提交 GitHub。媒体另行备份；仅备份配置不能恢复媒体。恢复时停止 Jellyfin，将 config 先另行留存，再从可信备份恢复到相同目录，核对属主与版本后启动。不要在运行中覆盖数据库。

升级前备份配置，修改镜像版本后 `docker compose pull jellyfin`、`docker compose up -d jellyfin`。数据库迁移后不可仅靠降级镜像回滚，需对应的升级前配置备份。`docker compose down` 会停止服务但不删除宿主机数据目录。

验收清单见 [docs/acceptance.md](docs/acceptance.md)。仓库初始化和静态检查通过不代表服务器部署成功。

参考：[官方容器文档](https://jellyfin.org/docs/general/installation/container/)、[反向代理文档](https://jellyfin.org/docs/general/post-install/networking/reverse-proxy/)。
