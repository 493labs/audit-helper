window:
flask --app .\services\api.py run

linux
pip install waitress
waitress-serve --host 127.0.0.1 services.api:app
或者
waitress-serve services.api:app