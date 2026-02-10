```bash
docker-compose up -d --build
docker-compose exec backend bash
python manage.py createsuperuser
exit
```