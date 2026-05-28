from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import asyncio

from app.database import AsyncSessionLocal
from app.models.models import User as UserModel, Media as MediaModel, Comment as CommentModel
from app.routers.users import get_password_hash


async def seed_database():
    async with AsyncSessionLocal() as db:
        print("🧹 Clearing existing data...")
        await db.execute(text("DELETE FROM comments"))
        await db.execute(text("DELETE FROM media"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()

        print("🌱 Seeding fresh test data...")

        # 1. Create Admin User
        admin = UserModel(
            email="test@example.com",
            username="KingDiabetes",
            hashed_password=get_password_hash("SB12345"),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"✅ Admin created → {admin.username} / SB12345")

        # 2. Create Regular User
        user = UserModel(
            email="test_user@email.com",
            username="test_user",
            hashed_password=get_password_hash("SB12345"),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ Regular user created → {user.username} / SB12345")

        # 3. Create Media (assigned to Admin)
        media = MediaModel(
            title="Cello Performance Test",
            description="Beautiful cello test image for seeding comments and replies",
            media_type="image",
            bucket="media",
            file_path="CELLO_TEST_PIC.jpg",
            public_url="https://yxkharrshmhyfkmsbdyy.supabase.co/storage/v1/object/public/media/CELLO_TEST_PIC.jpg",
            user_id=admin.id,          # ← This was missing
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)
        print(f"✅ Media created (ID: {media.id}) - owned by {admin.username}")

        # 4. Create Comments + Replies
        comment1 = CommentModel(
            content="This cello sounds absolutely incredible!",
            user_id=user.id,
            media_id=media.id,
            is_approved=True,
            is_deleted=False,
        )
        db.add(comment1)
        await db.commit()
        await db.refresh(comment1)

        reply1 = CommentModel(
            content="I agree! The tone is so rich and warm.",
            user_id=admin.id,
            media_id=media.id,
            parent_id=comment1.id,
            is_approved=True,
            is_deleted=False,
        )
        db.add(reply1)
        await db.commit()

        comment2 = CommentModel(
            content="Anyone know what piece this is being played?",
            user_id=user.id,
            media_id=media.id,
            is_approved=True,
            is_deleted=False,
        )
        db.add(comment2)
        await db.commit()

        print("\n🎉 Database seeded successfully!")
        print("\n=== Login Credentials ===")
        print(f"Admin   → username: KingDiabetes    password: SB12345")
        print(f"Regular → username: test_user        password: SB12345")
        print(f"Media ID: {media.id}   ← use this for testing comments/replies")


if __name__ == "__main__":
    asyncio.run(seed_database())