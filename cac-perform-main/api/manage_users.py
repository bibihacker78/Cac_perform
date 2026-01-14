#!/usr/bin/env python3
"""
Script de gestion avancée des utilisateurs CAC-Perform
Usage: 
    python manage_users.py create    # Créer des utilisateurs
    python manage_users.py list      # Lister les utilisateurs
    python manage_users.py reset     # Réinitialiser un mot de passe
    python manage_users.py delete    # Supprimer un utilisateur
"""

import bcrypt
import pymongo
import secrets
import string
import sys
import getpass
from datetime import datetime

# Configuration MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cac_perform"

def generate_secure_password(length=12):
    """Génère un mot de passe sécurisé"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def get_db_connection():
    """Établit une connexion à la base de données"""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test de connexion
        return client[DB_NAME]
    except Exception as e:
        print(f"❌ Erreur de connexion à MongoDB: {e}")
        return None

def create_user_interactive():
    """Crée un utilisateur de manière interactive"""
    print("\n👤 Création d'un nouvel utilisateur")
    print("-" * 40)
    
    email = input("📧 Email: ").strip()
    if not email:
        print("❌ Email requis")
        return False
    
    name = input("👤 Nom complet: ").strip()
    if not name:
        print("❌ Nom requis")
        return False
    
    print("\n🎭 Rôles disponibles:")
    print("   1. Administrateur")
    print("   2. Manager")
    print("   3. Auditeur Senior")
    print("   4. Auditeur")
    print("   5. Stagiaire")
    
    role_choice = input("🎭 Choisir un rôle (1-5): ").strip()
    roles = {
        "1": "Administrateur",
        "2": "Manager", 
        "3": "Auditeur Senior",
        "4": "Auditeur",
        "5": "Stagiaire"
    }
    
    role = roles.get(role_choice, "Auditeur")
    
    # Générer ou demander un mot de passe
    password_choice = input("\n🔑 Générer un mot de passe automatiquement? (o/n): ").strip().lower()
    
    if password_choice in ['o', 'oui', 'y', 'yes']:
        password = generate_secure_password()
        print(f"🔑 Mot de passe généré: {password}")
    else:
        password = getpass.getpass("🔑 Mot de passe: ")
        if not password:
            print("❌ Mot de passe requis")
            return False
    
    # Créer l'utilisateur
    return create_user(email, name, role, password)

def create_user(email, name, role, password):
    """Crée un utilisateur dans la base de données"""
    db = get_db_connection()
    if not db:
        return False
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing = db.Manager.find_one({"email": email})
        if existing:
            print(f"⚠️  L'utilisateur {email} existe déjà")
            return False
        
        # Hacher le mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
        
        # Créer le document utilisateur
        user_doc = {
            "email": email,
            "mot_de_passe": hashed_password,
            "role": role,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "last_login": None
        }
        
        # Insérer dans la base
        result = db.Manager.insert_one(user_doc)
        
        if result.inserted_id:
            print(f"✅ Utilisateur créé avec succès:")
            print(f"   📧 Email: {email}")
            print(f"   👤 Nom: {name}")
            print(f"   🎭 Rôle: {role}")
            print(f"   🔑 Mot de passe: {password}")
            return True
        else:
            print("❌ Erreur lors de la création")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def list_users():
    """Liste tous les utilisateurs"""
    db = get_db_connection()
    if not db:
        return
    
    try:
        users = list(db.Manager.find({}, {
            "email": 1, 
            "name": 1, 
            "role": 1, 
            "created_at": 1, 
            "is_active": 1,
            "last_login": 1
        }))
        
        if not users:
            print("ℹ️  Aucun utilisateur trouvé")
            return
        
        print(f"\n👥 UTILISATEURS ({len(users)} total)")
        print("=" * 80)
        print(f"{'Email':<30} {'Nom':<20} {'Rôle':<15} {'Statut':<8} {'Créé le'}")
        print("-" * 80)
        
        for user in users:
            email = user.get("email", "N/A")
            name = user.get("name", "N/A")
            role = user.get("role", "N/A")
            is_active = "✅ Actif" if user.get("is_active", True) else "❌ Inactif"
            created = user.get("created_at", "N/A")
            if created != "N/A":
                created = created[:10]  # Juste la date
            
            print(f"{email:<30} {name:<20} {role:<15} {is_active:<8} {created}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def reset_password():
    """Réinitialise le mot de passe d'un utilisateur"""
    db = get_db_connection()
    if not db:
        return
    
    email = input("\n📧 Email de l'utilisateur: ").strip()
    if not email:
        print("❌ Email requis")
        return
    
    try:
        user = db.Manager.find_one({"email": email})
        if not user:
            print(f"❌ Utilisateur {email} non trouvé")
            return
        
        print(f"👤 Utilisateur trouvé: {user.get('name', 'N/A')}")
        
        # Générer un nouveau mot de passe
        new_password = generate_secure_password()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode()
        
        # Mettre à jour
        result = db.Manager.update_one(
            {"email": email},
            {"$set": {"mot_de_passe": hashed_password, "updated_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Mot de passe réinitialisé avec succès")
            print(f"🔑 Nouveau mot de passe: {new_password}")
        else:
            print("❌ Erreur lors de la réinitialisation")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def delete_user():
    """Supprime un utilisateur"""
    db = get_db_connection()
    if not db:
        return
    
    email = input("\n📧 Email de l'utilisateur à supprimer: ").strip()
    if not email:
        print("❌ Email requis")
        return
    
    try:
        user = db.Manager.find_one({"email": email})
        if not user:
            print(f"❌ Utilisateur {email} non trouvé")
            return
        
        print(f"👤 Utilisateur trouvé: {user.get('name', 'N/A')}")
        confirm = input("⚠️  Êtes-vous sûr de vouloir supprimer cet utilisateur? (oui/non): ").strip().lower()
        
        if confirm in ['oui', 'o', 'yes', 'y']:
            result = db.Manager.delete_one({"email": email})
            if result.deleted_count > 0:
                print(f"✅ Utilisateur {email} supprimé avec succès")
            else:
                print("❌ Erreur lors de la suppression")
        else:
            print("❌ Suppression annulée")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def create_default_users():
    """Crée les utilisateurs par défaut"""
    default_users = [
        {
            "email": "admin@cac-perform.local",
            "name": "Administrateur Principal",
            "role": "Administrateur",
            "password": "Admin2026!"
        },
        {
            "email": "manager@cabinet.com",
            "name": "Manager Audit",
            "role": "Manager",
            "password": "Manager2026!"
        },
        {
            "email": "auditeur1@cabinet.com",
            "name": "Auditeur Senior",
            "role": "Auditeur Senior",
            "password": "Audit2026!"
        }
    ]
    
    print("🔧 Création des utilisateurs par défaut...")
    
    for user_data in default_users:
        print(f"\n👤 Création de {user_data['name']}...")
        create_user(
            user_data["email"],
            user_data["name"], 
            user_data["role"],
            user_data["password"]
        )

def show_help():
    """Affiche l'aide"""
    print("""
🚀 Gestionnaire d'utilisateurs CAC-Perform

USAGE:
    python manage_users.py [COMMANDE]

COMMANDES:
    create     Créer un nouvel utilisateur (interactif)
    list       Lister tous les utilisateurs
    reset      Réinitialiser le mot de passe d'un utilisateur
    delete     Supprimer un utilisateur
    default    Créer les utilisateurs par défaut
    help       Afficher cette aide

EXEMPLES:
    python manage_users.py create
    python manage_users.py list
    python manage_users.py reset
    python manage_users.py delete
    python manage_users.py default
""")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    print("🚀 Gestionnaire d'utilisateurs CAC-Perform")
    print("=" * 50)
    
    if command == "create":
        create_user_interactive()
    elif command == "list":
        list_users()
    elif command == "reset":
        reset_password()
    elif command == "delete":
        delete_user()
    elif command == "default":
        create_default_users()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Commande inconnue: {command}")
        show_help()

if __name__ == "__main__":
    main()









