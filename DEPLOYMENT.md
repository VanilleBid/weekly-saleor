## 1. Installing Saleor
```bash
pip3 install -r requirements.txt
python3 setup.py develop
```


## 2. Building Assets
```shell
npm i
npm run build-assets --production
npm run build-emails
```


## 3. Collect statics
```shell
python3 manage.py collectstatic --noinput
```
