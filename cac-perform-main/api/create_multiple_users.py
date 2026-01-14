#!/usr/bin/env python3
"""
Script pour créer plusieurs utilisateurs CAC-Perform
Usage: python create_multiple_users.py
"""

import bcrypt
import pymongo
import secrets
import string
import sys
from datetime import datetime

# Configuration MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cac_perform"

def generate_secure_password(length=12):
    """Génère un mot de passe sécurisé"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_users():
    """Crée plusieurs utilisateurs pour l'équipe"""
    
    # Liste des utilisateurs à créer
    users_to_create = [
        {
            "email": "admin@cac-perform.local",
            "role": "Administrateur",
            "name": "Administrateur Principal",
            "password": None  # Sera généré automatiquement
        },
        {
            "email": "manager@cabinet.com",
            "role": "Manager",
            "name": "Manager Audit",
            "password": None
        },
        {
            "email": "auditeur1@cabinet.com",
            "role": "Auditeur Senior",
            "name": "Auditeur Senior",
            "password": None
        },
        {
            "email": "auditeur2@cabinet.com",
            "role": "Auditeur",
            "name": "Auditeur Junior",
            "password": None
        },
        {
            "email": "auditeur3@cabinet.com",
            "role": "Auditeur",
            "name": "Auditeur Confirmé",
            "password": None
        },
        {
            "email": "stagiaire@cabinet.com",
            "role": "Stagiaire",
            "name": "Stagiaire Audit",
            "password": None
        }
    ]
    
    print("🔧 Création des utilisateurs CAC-Perform")
    print("=" * 60)
    
    try:
        # Connexion à MongoDB
        print("📡 Connexion à MongoDB...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        
        # Test de connexion
        client.server_info()
        print("✅ Connexion à MongoDB réussie")
        
        # Créer les utilisateurs
        created_users = []
        
        for user_data in users_to_create:
            email = user_data["email"]
            role = user_data["role"]
            name = user_data["name"]
            
            # Vérifier si l'utilisateur existe déjà
            existing_user = db.Manager.find_one({"email": email})
            
            if existing_user:
                print(f"⚠️  L'utilisateur {email} existe déjà - ignoré")
                continue
            
            # Générer un mot de passe sécurisé
            password = generate_secure_password()
            
            # Hacher le mot de passe
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
            
            # Créer l'utilisateur
            user_doc = {
                "email": email,
                "mot_de_passe": hashed_password,
                "role": role,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }
            
            # Insérer dans la base de données
            result = db.Manager.insert_one(user_doc)
            
            if result.inserted_id:
                created_users.append({
                    "email": email,
                    "password": password,
                    "role": role,
                    "name": name
                })
                print(f"✅ Utilisateur créé: {name} ({email})")
            else:
                print(f"❌ Erreur lors de la création de {email}")
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES UTILISATEURS CRÉÉS")
        print("=" * 60)
        
        if created_users:
            print(f"✅ {len(created_users)} utilisateur(s) créé(s) avec succès")
            print("\n📧 IDENTIFIANTS DE CONNEXION:")
            print("-" * 40)
            
            for user in created_users:
                print(f"👤 {user['name']} ({user['role']})")
                print(f"   📧 Email: {user['email']}")
                print(f"   🔑 Mot de passe: {user['password']}")
                print()
            
            print("⚠️  IMPORTANT:")
            print("   - Notez ces identifiants dans un endroit sécurisé")
            print("   - Demandez aux utilisateurs de changer leur mot de passe")
            print("   - Supprimez ce fichier après avoir noté les identifiants")
            
        else:
            print("ℹ️  Aucun nouvel utilisateur créé (tous existaient déjà)")
        
        # Statistiques
        total_users = db.Manager.count_documents({})
        print(f"\n📊 Total d'utilisateurs dans la base: {total_users}")
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("❌ Impossible de se connecter à MongoDB")
        print("💡 Vérifiez que MongoDB est démarré sur localhost:27017")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
        
    finally:
        if 'client' in locals():
            client.close()

def list_existing_users():
    """Liste les utilisateurs existants"""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        
        users = list(db.Manager.find({}, {"email": 1, "role": 1, "name": 1, "created_at": 1}))
        
        if users:
            print("\n👥 UTILISATEURS EXISTANTS:")
            print("-" * 40)
            for user in users:
                role = user.get("role", "Non défini")
                name = user.get("name", "Non défini")
                created = user.get("created_at", "Date inconnue")
                print(f"📧 {user['email']} - {name} ({role}) - Créé: {created}")
        else:
            print("ℹ️  Aucun utilisateur trouvé dans la base de données")
            
    except Exception as e:
        print(f"❌ Erreur lors de la liste des utilisateurs: {e}")
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Fonction principale"""
    print("🚀 Gestionnaire d'utilisateurs CAC-Perform")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_existing_users()
        return
    
    # Créer les utilisateurs
    success = create_users()
    
    if success:
        print("\n🎉 Script terminé avec succès!")
        print("\n📋 Prochaines étapes:")
        print("   1. Distribuer les identifiants aux utilisateurs")
        print("   2. Tester les connexions")
        print("   3. Supprimer ce fichier pour des raisons de sécurité")
    else:
        print("\n❌ Script terminé avec des erreurs")
        sys.exit(1)

if __name__ == "__main__":
    main()









