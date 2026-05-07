import asyncio
from tortoise import Tortoise
from app.core.database import TORTOISE_ORM
from app.modules.auth.service import AuthService


async def main():
    await Tortoise.init(config=TORTOISE_ORM)
    
    admin = await AuthService.create_first_admin()
    
    if admin:
        print(f"✓ First admin user created successfully!")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Default password: admin123456")
        print(f"\n⚠ IMPORTANT: Please change the password after first login!")
    else:
        print("Admin user already exists. Skipping creation.")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
