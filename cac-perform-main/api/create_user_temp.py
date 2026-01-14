 #!/usr/bin/env python3
"""
Script temporaire pour créer un utilisateur de test
en attendant l'installation de MongoDB
"""

import bcrypt
import json
import os

# Créer un fichier JSON temporaire pour stocker les utilisateurs
USERS_FILE = "temp_users.json"

def create_temp_user():
    """Crée un utilisateur temporaire dans un fichier JSON"""
    
    # Données de l'utilisateur
    email = "admin@cac-perform.local"
    password = "MonMotDePasse!2026"
    
    # Hacher le mot de passe
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
    
    # Structure de l'utilisateur
    user_data = {
        "email": email,
        "mot_de_passe": hashed_password,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Lire les utilisateurs existants ou créer une nouvelle liste
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except:
            users = []
    
    # Vérifier si l'utilisateur existe déjà
    user_exists = any(user.get("email") == email for user in users)
    
    if not user_exists:
        users.append(user_data)
        
        # Sauvegarder dans le fichier
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Utilisateur créé avec succès :")
        print(f"   Email: {email}")
        print(f"   Mot de passe: {password}")
        print(f"   Fichier: {USERS_FILE}")
    else:
        print(f"⚠️  L'utilisateur {email} existe déjà")
    
    return user_data

def verify_user(email, password):
    """Vérifie les identifiants de l'utilisateur"""
    
    if not os.path.exists(USERS_FILE):
        print("❌ Aucun utilisateur trouvé")
        return False
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        for user in users:
            if user.get("email") == email:
                stored_password = user.get("mot_de_passe", "")
                
                # Vérifier le mot de passe
                try:
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        print(f"✅ Connexion réussie pour {email}")
                        return True
                    else:
                        print(f"❌ Mot de passe incorrect pour {email}")
                        return False
                except Exception as e:
                    print(f"❌ Erreur de vérification: {e}")
                    return False
        
        print(f"❌ Utilisateur {email} non trouvé")
        return False
        
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Création d'un utilisateur temporaire")
    print("=" * 50)
    
    # Créer l'utilisateur
    user = create_temp_user()
    
    print("\n🧪 Test de connexion")
    print("=" * 50)
    
    # Tester la connexion
    verify_user("admin@cac-perform.local", "MonMotDePasse!2026")
    
    print("\n📋 Instructions:")
    print("1. Installez MongoDB : https://www.mongodb.com/try/download/community")
    print("2. Démarrez MongoDB : net start MongoDB")
    print("3. Exécutez : python create_manager.py")
    print("4. Supprimez le fichier temporaire : del temp_users.json")
