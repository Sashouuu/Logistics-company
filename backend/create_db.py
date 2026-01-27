#!/usr/bin/env python
"""
Скрипт за създаване на базата и таблиците
"""
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

#먼저 базата создаем директно
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "")
db_host = os.getenv("DB_HOST", "127.0.0.1")
db_port = int(os.getenv("DB_PORT", "3306"))
db_name = os.getenv("DB_NAME", "logistics_company")

print(f"Свързвам се със MySQL на {db_host}:{db_port}...")

try:
    # Свързване без база данни
    connection = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    with connection.cursor() as cursor:
        # Создаем базата ако не съществува
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"✅ База данни '{db_name}' създадена")
    
    connection.commit()
    connection.close()
    
    # Сега създаваме таблиците
    from app import app
    from extensions import db
    
    with app.app_context():
        print("Създавам таблиците...")
        db.create_all()
        print("✅ Всички таблици създадени успешно!")
        
except pymysql.Error as e:
    print(f"❌ Грешка при свързване със MySQL: {e}")
except Exception as e:
    print(f"❌ Неочаквана грешка: {e}")
