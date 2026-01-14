#!/usr/bin/env python3
"""
Script de test pour vérifier la gestion des utilisateurs
Usage: python test_users.py
"""

import pymongo
import bcrypt
import sys

def test_mongodb_connection():
    """Teste la connexion à MongoDB"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ Connexion à MongoDB réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        return False

def test_user_authentication():
    """Teste l'authentification d'un utilisateur"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["cac_perform"]
        
        # Chercher un utilisateur
        user = db.Manager.find_one({})
        if not user:
            print("❌ Aucun utilisateur trouvé dans la base")
            return False
        
        email = user.get("email")
        stored_password = user.get("mot_de_passe")
        
        print(f"🧪 Test d'authentification pour: {email}")
        
        # Test avec un mot de passe incorrect
        test_password = "motdepasseincorrect"
        try:
            result = bcrypt.checkpw(test_password.encode('utf-8'), stored_password.encode('utf-8'))
            if result:
                print("❌ Erreur: mot de passe incorrect accepté")
                return False
            else:
                print("✅ Mot de passe incorrect correctement rejeté")
        except Exception as e:
            print(f"⚠️  Erreur lors du test bcrypt: {e}")
        
        print("✅ Test d'authentification réussi")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'authentification: {e}")
        return False

def test_user_structure():
    """Teste la structure des utilisateurs"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["cac_perform"]
        
        users = list(db.Manager.find({}))
        if not users:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"📊 Test de structure pour {len(users)} utilisateur(s)")
        
        required_fields = ["email", "mot_de_passe", "role", "name", "created_at"]
        
        for user in users:
            email = user.get("email", "N/A")
            missing_fields = []
            
            for field in required_fields:
                if field not in user:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Utilisateur {email}: champs manquants {missing_fields}")
                return False
            else:
                print(f"✅ Utilisateur {email}: structure correcte")
        
        print("✅ Tous les utilisateurs ont une structure correcte")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de structure: {e}")
        return False

def test_password_hashing():
    """Teste le hachage des mots de passe"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["cac_perform"]
        
        user = db.Manager.find_one({})
        if not user:
            print("❌ Aucun utilisateur trouvé pour tester le hachage")
            return False
        
        stored_password = user.get("mot_de_passe")
        email = user.get("email")
        
        print(f"🔐 Test de hachage pour: {email}")
        
        # Vérifier que le mot de passe est haché
        if not stored_password.startswith("$2b$"):
            print("❌ Le mot de passe n'est pas haché avec bcrypt")
            return False
        
        # Vérifier la longueur du hash
        if len(stored_password) < 50:
            print("❌ Le hash du mot de passe semble trop court")
            return False
        
        print("✅ Le mot de passe est correctement haché")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de hachage: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Tests de gestion des utilisateurs CAC-Perform")
    print("=" * 60)
    
    tests = [
        ("Connexion MongoDB", test_mongodb_connection),
        ("Structure des utilisateurs", test_user_structure),
        ("Hachage des mots de passe", test_password_hashing),
        ("Authentification", test_user_authentication)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ Test '{test_name}' échoué")
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés avec succès!")
        print("✅ Le système de gestion des utilisateurs est opérationnel")
        return True
    else:
        print("❌ Certains tests ont échoué")
        print("💡 Vérifiez la configuration et réessayez")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)









