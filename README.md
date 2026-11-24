# Demo shop web app (Flask + gunicorn + nginx)

A small API for generating realistic web logs. Tested on Debian/Ubuntu.

## Layout

```
app/app.py              Flask app
systemd/webapp.service  runs the app with gunicorn on 127.0.0.1:5000
nginx/webapp.conf       nginx reverse proxy on port 80
install.sh              installs everything
generate_traffic.sh     sends a mix of requests to create log data
```

## Install (on the web server VM)

```bash
# copy the folder to the VM, e.g. from your machine:
gcloud compute scp --recurse webapp YOUR_WEB_VM:~ --zone YOUR_ZONE

# on the VM:
cd ~/webapp
sudo ./install.sh
```

## Check it works

```bash
systemctl status webapp nginx
curl http://127.0.0.1/
curl http://127.0.0.1/api/products
```

## Generate traffic

```bash
./generate_traffic.sh                     # 200 requests to http://127.0.0.1
./generate_traffic.sh http://127.0.0.1 1000
```

## Endpoints

| Method | Path                  | Behaviour                                   |
|--------|-----------------------|---------------------------------------------|
| GET    | /health               | 200 OK                                      |
| GET    | /api/products         | product list                                |
| GET    | /api/products/<id>    | 404 for unknown ids                         |
| POST   | /api/login            | 401 on bad password (alice / wonderland)    |
| POST   | /api/orders           | 201 placed, 409 out of stock (product 4)    |
| GET    | /api/slow             | 0.5–3 s delay                               |
| GET    | /api/error            | 500 with a stack trace in the app log       |

## Log files

| File                              | Written by | Format              |
|-----------------------------------|------------|---------------------|
| /var/log/nginx/webapp_access.log  | nginx      | combined (standard) |
| /var/log/nginx/webapp_error.log   | nginx      | nginx error format  |
| /var/log/webapp/app.log           | app        | JSON, one per line  |

## Useful commands

```bash
sudo systemctl restart webapp nginx
sudo journalctl -u webapp -f
sudo tail -f /var/log/webapp/app.log /var/log/nginx/webapp_access.log
```

To reach it from your browser, open TCP 80 in the GCP firewall for your IP
(same approach as port 8000 for Splunk).
