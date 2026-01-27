#!/usr/bin/env python
"""
Скрипт за създаване на начални данни (seed data)
Това улеснява тестването на приложението
"""
from app import app
from extensions import db
from models import Company, Office, Employee, User, Client
from datetime import datetime

def seed_data():
    with app.app_context():
        # Очисти старите данни - АКТИВИРАНО за пресъздаване
        db.drop_all()
        db.create_all()
        
        print("Създавам начални данни...")
        
        # 1. Създай компанията
        company = Company(
            name="FastLogistics",
            registration_number="BG12345678",
            address="1 бул. България, 1000 София",
            phone="+359888123456",
            email="info@fastlogistics.com"
        )
        db.session.add(company)
        db.session.flush()
        
        # 2. Създай офис
        office = Office(
            name="Sofia Office",
            company_id=company.id,
            address="1 бул. България, 1000 София",
            phone="+359888111111",
            email="sofia@fastlogistics.com",
            city="Sofia",
            country="Bulgaria"
        )
        db.session.add(office)
        db.session.flush()
        
        # 3. Създай служител (admin)
        admin_user = User(
            email="admin@fastlogistics.com",
            role="EMPLOYEE"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.flush()
        
        admin_employee = Employee(
            user_id=admin_user.id,
            company_id=company.id,
            office_id=office.id,
            first_name="Admin",
            last_name="User",
            phone="+359888222222"
        )
        db.session.add(admin_employee)
        db.session.flush()
        
        # 4. Създай тестови клиенти
        clients_data = [
            {
                "email": "client1@example.com",
                "password": "client123",
                "first_name": "Иван",
                "last_name": "Петров",
                "company_name": "ООО Петров и сина",
                "phone": "+359888333333",
                "address": "Ул. Търговска 10, София",
                "city": "София",
                "country": "България"
            },
            {
                "email": "client2@example.com",
                "password": "client123",
                "first_name": "Мария",
                "last_name": "Йванова",
                "company_name": "АД Йванова Тр.",
                "phone": "+359888444444",
                "address": "Ул. Славянска 5, Пловдив",
                "city": "Пловдив",
                "country": "България"
            },
            {
                "email": "client3@example.com",
                "password": "client123",
                "first_name": "Георги",
                "last_name": "Димов",
                "company_name": "Трейд Кооперация",
                "phone": "+359888555555",
                "address": "Ул. Европейска 20, Бургас",
                "city": "Бургас",
                "country": "България"
            }
        ]
        
        for client_data in clients_data:
            user = User(
                email=client_data["email"],
                role="CLIENT"
            )
            user.set_password(client_data["password"])
            db.session.add(user)
            db.session.flush()
            
            client = Client(
                user_id=user.id,
                first_name=client_data["first_name"],
                last_name=client_data["last_name"],
                company_name=client_data["company_name"],
                phone=client_data["phone"],
                address=client_data["address"],
                city=client_data["city"],
                country=client_data["country"]
            )
            db.session.add(client)
        
        db.session.commit()
        
        print("✅ Начални данни създадени успешно!")
        print(f"   Компания: {company.name}")
        print(f"   Офис: {office.name}")
        print(f"   Служител (admin): admin@fastlogistics.com / admin123")
        print("\n   Тестови клиенти:")
        for client_data in clients_data:
            print(f"   - {client_data['email']} / {client_data['password']} ({client_data['first_name']} {client_data['last_name']})")
        print("\nМожете да влезете като служител или клиент на адреса /login.html")

if __name__ == '__main__':
    seed_data()

