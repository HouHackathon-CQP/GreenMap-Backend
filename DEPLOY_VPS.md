# Deploy GreenMap Backend len VPS

Huong dan nay mac dinh VPS chay Ubuntu 22.04/24.04 va backend duoc chay bang Docker Compose.

## 1. Chuan bi VPS

```bash
sudo apt update
sudo apt install -y ca-certificates curl git ufw

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Dang xuat SSH roi dang nhap lai de user co quyen chay `docker`.

## 2. Dua source len VPS

```bash
cd /opt
sudo mkdir -p greenmap
sudo chown $USER:$USER greenmap
cd greenmap

git clone <YOUR_REPO_URL> GreenMap-Backend
cd GreenMap-Backend
```

Neu khong dung Git, co the upload folder backend len `/opt/greenmap/GreenMap-Backend`.

## 3. Tao file cau hinh

```bash
cp env.production.example .env
nano .env
```

Can doi toi thieu:

```env
SECRET_KEY="chuoi-random-dai"
POSTGRES_PASSWORD="mat-khau-db-manh"
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD="mat-khau-admin-manh"
BACKEND_PORT=8001
CORS_ORIGINS="*"
```

Khuyen nghi tao `SECRET_KEY`:

```bash
openssl rand -hex 32
```

## 4. Dat Firebase service account

Tren VPS:

```bash
mkdir -p secrets
nano secrets/firebase-service-account.json
```

Dan noi dung file Firebase service account JSON moi vao file tren.

Trong production compose, backend se doc file nay tai:

```text
/run/secrets/firebase-service-account.json
```

Khong can sua `FIREBASE_CREDENTIALS_FILE` trong `.env`.

## 5. Chay backend

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

Test:

```bash
curl http://localhost:8001/
```

Tu may ca nhan:

```text
http://YOUR_VPS_IP:8001/
```

## 6. Mo firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8001/tcp
sudo ufw enable
sudo ufw status
```

Khong expose Postgres, Mongo, Orion ra internet trong file production compose.

## 7. Cau hinh mobile app

Trong mobile app `local.properties`, doi backend URL thanh IP/domain VPS:

```properties
API_BASE_URL=http://YOUR_VPS_IP:8001/
```

Neu co domain va HTTPS:

```properties
API_BASE_URL=https://api.your-domain.com/
```

Sau do rebuild mobile app.

## 8. Lenh van hanh hay dung

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

Backup database:

```bash
docker exec greenmap-postgres pg_dump -U admin greenmap_db > greenmap_db_backup.sql
```
