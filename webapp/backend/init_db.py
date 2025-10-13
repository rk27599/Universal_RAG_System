#!/usr/bin/env python3
"""
Database Initialization Script
Creates tables and initial admin user
"""

import sys
from sqlalchemy.orm import Session

from core.database import engine, Base, SessionLocal, init_db
from core.security import security_manager
from models.user import User
from models.conversation import Conversation, Message
from models.document import Document, Chunk


def create_admin_user(db: Session):
    """Create initial admin user"""
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        print("ℹ️  Admin user already exists")
        return existing_admin

    # Create admin user with secure password
    admin_password = "Admin@123"  # Strong password meeting all requirements
    hashed_password = security_manager.get_password_hash(admin_password)

    admin_user = User(
        username="admin",
        email="admin@localhost",
        full_name="System Administrator",
        password_hash=hashed_password,
        is_active=True,
        is_admin=True,
        email_verified=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    print(f"✅ Admin user created:")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print(f"   Email: admin@localhost")
    print(f"   ⚠️  IMPORTANT: Change this password after first login!")

    return admin_user


def create_sample_conversation(db: Session, user: User):
    """Create a sample conversation for demo purposes"""
    existing_conv = db.query(Conversation).filter(Conversation.user_id == user.id).first()
    if existing_conv:
        print("ℹ️  Sample conversation already exists")
        return

    sample_conv = Conversation(
        user_id=user.id,
        title="Welcome to RAG System",
        is_active=True,
        model_name="mistral",
        message_count=2
    )

    db.add(sample_conv)
    db.commit()
    db.refresh(sample_conv)

    # Add welcome messages
    welcome_msg = Message(
        conversation_id=sample_conv.id,
        role="system",
        content="Welcome to the Local RAG System by Rohan ! This is a sample conversation to get you started."
    )
    db.add(welcome_msg)

    info_msg = Message(
        conversation_id=sample_conv.id,
        role="assistant",
        content="I'm your AI assistant powered by local Ollama models. You can ask me questions, and I'll use your uploaded documents to provide relevant answers. Start by uploading some documents in the Documents section!",
        token_count=50
    )
    db.add(info_msg)

    db.commit()
    print(f"✅ Sample conversation created")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("🔧 Initializing Database...")
    print("=" * 60)

    try:
        # Create all tables
        print("\n📋 Creating database tables...")
        init_db()

        # Create session
        db = SessionLocal()

        try:
            # Create admin user
            print("\n👤 Creating admin user...")
            admin_user = create_admin_user(db)

            # Create sample conversation
            print("\n💬 Creating sample conversation...")
            create_sample_conversation(db, admin_user)

            print("\n" + "=" * 60)
            print("✅ Database initialization complete!")
            print("=" * 60)
            print("\n🚀 You can now start the application with:")
            print("   python3 app/main.py")
            print("\n🌐 Then login at http://localhost:8000 with:")
            print("   Username: admin")
            print("   Password: Admin@123")
            print("=" * 60)

        finally:
            db.close()

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
