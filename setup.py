# Setup
print("👋 Salut ! Pour améliorer l'UX et pour pouvoir faire le setup plus facilement, je vais te poser quelques questions.")

# Token
print("Merci d'entrer le token de ton bot:")
token = str(input("> "))

# Tickets max par utilisateur
print("Merci d'entrer le nombre maximum de tickets que peut avoir un utilisateur (en simultané) :")
tickets_max = int(input("> "))

# Channel de logs
print("Merci d'entrer l'ID du channel de logs:")
logs = str(input("> "))

# Catégorie des tickets
print("Merci d'entrer l'ID de la catégorie des tickets:")
categorie = str(input("> "))

# Identifiants rôle support
print("Merci d'entrer l'identifiant de ton rôle support :")
support = str(input("> "))

# Sauvegarde
print("🤔 Je sauvegarde tout ça...")
with open(".env", "w") as f:
    f.write(f"TOKEN={token}")

with open("config.json", "w") as f:
    f.write(f'{{"tickets_max_par_utilisateur": {tickets_max}, "salon_logs": "{logs}", "categorie_tickets": "{categorie}", "role_support": "{support}"}}')

print("✅ Tout est prêt ! Tu peux lancer le bot avec 'python bot.py'")