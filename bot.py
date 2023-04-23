import os
import io
import time
import uuid
from dotenv import load_dotenv
import discord
from discord import app_commands
import json

load_dotenv()  # Charger le fichier .env

# Pour les intents, on a besoin des intents de base + contenu de messages
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)  # Création du client
tree = app_commands.CommandTree(bot)  # Création du tree
bot.tree = tree  # Ajout du tree au bot

# Ouverture des fichiers JSON nécessaires
with open("db.json", "r") as f:
    bdd = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)


async def log(action: str, details: str, par: str = "un utilisateur inconnu"):
    salon = bot.get_channel(int(config["salon_logs"]))
    embed = discord.Embed(
        title=action,
        description=details,
        color=0x0ED3FF
    )
    embed.set_footer(text=f"Action effectuée par {par}")
    await salon.send(embed=embed)
    return True


async def close_ticket(interaction, raison=""):
    # On répète pas mal ce morceau de code, du coup ça part en fonction !
    await interaction.channel.delete()
    await log("Fermeture de ticket", "Le ticket \"" + interaction.channel.name + "\" a été fermé. Raison: "+raison,
              interaction.user.name+"#"+interaction.user.discriminator)
    # Envoyer les infos du ticket dans le salon logs, en tant que fichier JSON.
    # Premièrement, on crée le fichier JSON qui sera envoyé.

    contenu = json.dumps(bdd["tickets"][str(interaction.channel.id)], indent=None)
    fichier = discord.File(
        fp=io.StringIO(contenu),
        filename="ticket-" + interaction.channel.name + ".json"
    )

    await interaction.guild.get_channel(int(config["salon_logs"])).send(
        content="🔒 À la suite de la fermeture du ticket \"" + interaction.channel.name + "\", voici les informations du ticket. Vous pouvez visualiser ça joliment sur https://visutickets.softky.krbk.dev",
        file=fichier
    )

    return True


@bot.event
async def on_ready():  # Bot prêt !
    print(f"🔥 On fire ! Je suis connecté en tant que {bot.user}")
    # Print la configuration et la base de données
    print("Configuration:")
    print(config)
    print("Base de données:")
    print(bdd)
    # Préparation du tree
    await bot.tree.sync()
    # Change le statut du bot en "Regarde des tickets"
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="des tickets"),
        status=discord.Status.idle
    )


@bot.tree.command(name="ping", description="🤖 Connaître la latence du bot")
async def ping(interaction):
    await interaction.response.send_message(
        content=f"Pong! Latence: {round(bot.latency * 1000)}ms",
        ephemeral=True
    )


@bot.tree.command(name="embed_ticket", description="🎫 Envoyer l'embed de création de ticket")
async def envoyer_embed_ticket(interaction):
    # Limiter la commande aux admins. Vérification de la permission "Administrateur"
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Tu n'as pas la permission d'utiliser cette commande !",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="🗨️ **Besoin d'aide ?**",
        description="En créant un ticket, tu pourras poser tes questions à l'équipe de modération directement dans un channel dédié !",
        color=0x0ED3FF
    )

    # Pour préparer le bouton, création de la view
    vue = discord.ui.View()  # Oui, j'ai appelé ça "vue" pour franciser les variables.

    # Création du bouton
    bouton = discord.ui.Button(
        label="Créer un ticket",
        style=discord.ButtonStyle.danger,
        custom_id="creer_ticket",
        emoji="📩"
    )

    # Ajout du bouton à la vue
    vue.add_item(bouton)

    # Envoi de l'embed
    await interaction.channel.send(
        content="",
        embed=embed,
        view=vue
    )
    await interaction.followup.send(
        content="✅ L'embed a bien été envoyée !",
        ephemeral=True
    )


@bot.tree.command(name="ticket", description="📩 Créer un ticket")
async def creation_ticket(interaction):
    await creer_ticket(interaction)  # Ça peut paraître bizarre, mais c'est pour éviter de dupliquer le code



async def creer_ticket(interaction):
    # Vérification du nombre de tickets ouverts
    # D'abord on vérifie si l'utilisateur est dans la "bdd"
    if str(interaction.user.id) not in bdd["utilisateurs"]:
        bdd["utilisateurs"][str(interaction.user.id)] = {
            "tickets": []
        }

    # Puis, on vérifie son nombre de tickets ouverts
    if len(bdd["utilisateurs"][str(interaction.user.id)]["tickets"]) >= config["tickets_max_par_utilisateur"]:
        await interaction.response.send_message(
            content="❌ Tu as déjà trop de tickets ouverts !",
            ephemeral=True
        )
        return

    # Enfin, si tout est bon, on peut créer le ticket !
    await interaction.response.defer(ephemeral=True)

    salon = await interaction.guild.create_text_channel(
        name=f"ticket-{interaction.user.name}-{interaction.user.discriminator}-{uuid.uuid4().hex[:4]}",
    )
    bdd["utilisateurs"][str(interaction.user.id)]["tickets"].append(salon.id)

    # Déplacement du salon dans la catégorie des tickets
    categorie_tickets = interaction.guild.get_channel(int(config["categorie_tickets"]))
    await salon.edit(category=categorie_tickets)

    # On enlève la permission d'envoyer de lire les messages pour les membres...
    await salon.set_permissions(interaction.guild.default_role, read_messages=False)

    # ... mais on la met pour l'utilisateur qui a créé le ticket...
    await salon.set_permissions(interaction.user, read_messages=True)

    # ...et pour le rôle support !
    role_support = interaction.guild.get_role(int(config["role_support"]))
    await salon.set_permissions(role_support, read_messages=True)

    # On ajoute le salon à la base de données
    bdd["tickets"][str(salon.id)] = {
        "ouvert_par": interaction.user.id,
        "ouvert_timestamp": int(time.time()),
        "transcript": [],
        "utilisateurs": {
            str(interaction.user.id): {
                "nom": interaction.user.name,
                "avatar": str(interaction.user.avatar)
            },
            str(bot.user.id): {
                "nom": bot.user.name,
                "avatar": str(bot.user.avatar)
            }
        }
    }

    print("BDD après création de ticket:")
    print(bdd)
    # Sauvegarde de la base de données+
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))

    # Envoi du message de bienvenue
    embed = discord.Embed(
        title="👋 **Fermer le ticket**",
        description=f"Pour fermer le ticket, appuie sur le bouton ci-dessous.",
        color=0xFF1111
    )
    embed.set_footer(text="Ticket créé par " + interaction.user.name, icon_url=interaction.user.avatar)

    # Préparation du bouton
    vue = discord.ui.View()  # Oui, j'ai (encore) appelé ça "vue" pour franciser les variables.
    bouton = discord.ui.Button(
        label="Fermer le ticket",
        style=discord.ButtonStyle.danger,
        custom_id="fermer_ticket",
        emoji="🔒"
    )
    vue.add_item(bouton)

    # Envoi du message
    await salon.send(
        content=f"Salut {interaction.user.mention}, un <@&{config['role_support']}> te répondra bientôt :)",
        embed=embed,
        view=vue
    )

    await interaction.followup.send(
        content=f"✅ Le ticket a bien été créé ! {salon.mention}",
        ephemeral=True
    )


@bot.tree.command(name="closeticket", description="🔒 Fermer un ticket")
async def fermer_ticket(interaction):
    if not interaction.channel.category_id == int(config["categorie_tickets"]):
        await interaction.response.send_message(
            content="❌ Cette commande ne peut être exécutée que dans un ticket.",
            ephemeral=True
        )
        return

    # Vérifier si l'utilisateur est le propriétaire du ticket
    if interaction.user.id != bdd["tickets"][str(interaction.channel.id)]["ouvert_par"]:
        await interaction.response.send_message(
            content="❌ Tu n'es pas le créateur de ce ticket.",
            ephemeral=True
        )
        return

    # Fermer le ticket
    await interaction.response.defer(ephemeral=True)
    await close_ticket(interaction)

    # Suppression de la BDD
    del bdd["tickets"][str(interaction.channel.id)]
    bdd["utilisateurs"][str(interaction.user.id)]["tickets"].remove(interaction.channel.id)

    # Sauvegarde de la base de données
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))


@bot.tree.command(name="closereason", description="🔒 Fermer un ticket avec une raison")
@app_commands.describe(raison="La raison de la fermeture du ticket")
async def fermer_ticket_avec_raison(interaction, raison: str):
    if not interaction.channel.category_id == int(config["categorie_tickets"]):
        await interaction.response.send_message(
            content="❌ Cette commande ne peut être exécutée que dans un ticket.",
            ephemeral=True
        )
        return

    # Cette commande est utilisable uniquement par les admins, donc on vérifie les perms en conséquence !
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Tu n'as pas la permission d'utiliser cette commande !",
            ephemeral=True
        )
        return

    # Fermer le ticket
    await interaction.response.defer(ephemeral=True)
    await close_ticket(interaction, raison)

    createur = bdd["tickets"][str(interaction.channel.id)]["ouvert_par"]

    # Suppression de la BDD
    del bdd["tickets"][str(interaction.channel.id)]
    bdd["utilisateurs"][str(createur)]["tickets"].remove(interaction.channel.id)

    # Envoi d'un message au créateur du ticket
    c_o = createur
    createur = await bot.fetch_user(createur)

    if createur is not None:
        await createur.send(
            content=f"Le ticket {interaction.channel.name} a été fermé par un admin avec la raison suivante : {raison}"
        )
    else:
        print(list(bot.get_all_members())[0])
    # Sauvegarde de la base de données
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))


@bot.tree.command(name="addtoticket", description="📣 Ajouter un utilisateur au ticket")
@app_commands.describe(utilisateur="L'utilisateur à ajouter au ticket")
async def ajouter_utilisateur_ticket(interaction, utilisateur: discord.Member):
    if not interaction.channel.category_id == int(config["categorie_tickets"]):
        await interaction.response.send_message(
            content="❌ Cette commande ne peut être exécutée que dans un ticket.",
            ephemeral=True
        )
        return

    # On vérifie si la personne qui a fait la commande est un admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Tu n'as pas la permission d'utiliser cette commande !",
            ephemeral=True
        )
        return

    # On vérifie que l'utilisateur à ajouter n'est pas un bot (au cas où).
    if utilisateur.bot:
        await interaction.response.send_message(
            content="❌ Tu ne peux pas ajouter un bot au ticket.",
            ephemeral=True
        )
        return

    # Enfin, on vérifie que l'utilisateur n'est pas déjà dans le ticket. On vérifie juste ses perms.
    if interaction.channel.permissions_for(utilisateur).read_messages:
        await interaction.response.send_message(
            content="❌ Cet utilisateur est déjà dans le ticket.",
            ephemeral=True
        )
        return

    # Ajouter l'utilisateur au ticket
    await interaction.channel.set_permissions(utilisateur, read_messages=True)

    # Ajouter l'utilisateur à la BDD si il n'y est pas déjà
    if not str(utilisateur.id) in bdd["tickets"][str(interaction.channel.id)]["utilisateurs"]:
        bdd["tickets"][str(interaction.channel.id)]["utilisateurs"][str(utilisateur.id)] = {
            "nom": utilisateur.name,
            "avatar": str(utilisateur.avatar)
        }
    bdd["tickets"][str(interaction.channel.id)]["transcript"].append(
        {
            "type": "ajout",
            "utilisateur": utilisateur.id,
            "par": interaction.user.id,
            "timestamp": int(time.time())
        }
    )

    # Sauvegarde de la base de données
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))

    await interaction.response.send_message(
        content=f"✅ {utilisateur.mention} a bien été ajouté au ticket.",
        ephemeral=True
    )


@bot.tree.command(name="removefromticket", description="👋 Retirer un utilisateur du ticket")
@app_commands.describe(utilisateur="L'utilisateur à retirer du ticket")
async def retirer_utilisateur_ticket(interaction, utilisateur: discord.Member):
    if not interaction.channel.category_id == int(config["categorie_tickets"]):
        await interaction.response.send_message(
            content="❌ Cette commande ne peut être exécutée que dans un ticket.",
            ephemeral=True
        )
        return

    # On vérifie si la personne qui a fait la commande est un admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            content="❌ Tu n'as pas la permission d'utiliser cette commande !",
            ephemeral=True
        )
        return

    # On vérifie que l'utilisateur à retirer n'est pas un bot (au cas où).
    if utilisateur.bot:
        await interaction.response.send_message(
            content="❌ Tu ne peux pas retirer un bot du ticket.",
            ephemeral=True
        )
        return

    # Enfin, on vérifie que l'utilisateur est dans le ticket (avec ses perms).
    if not interaction.channel.permissions_for(utilisateur).read_messages:
        await interaction.response.send_message(
            content="❌ Cet utilisateur n'est pas dans le ticket.",
            ephemeral=True
        )
        return

    # Retirer l'utilisateur du ticket
    await interaction.channel.set_permissions(utilisateur, read_messages=None)

    # Retirer l'utilisateur de la BDD
    bdd["tickets"][str(interaction.channel.id)]["transcript"].append(
        {
            "type": "retrait",
            "utilisateur": utilisateur.id,
            "par": interaction.user.id,
            "timestamp": int(time.time())
        }
    )

    # Sauvegarde de la base de données
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))

    await interaction.response.send_message(
        content=f"✅ {utilisateur.mention} a bien été retiré du ticket.",
        ephemeral=True
    )


# Pour le transcript, on écoute tous les messages
@bot.event
async def on_message(message):
    # Un message a été envoyé. On vérifie :
    # D'abord si le message a été envoyé sur un serveur
    if not message.guild:
        return

    # Puis
    # - Si le message a été envoyé dans un ticket
    # - Si le message a bien été envoyé par un utilisateur

    if not message.channel.category_id == int(config["categorie_tickets"]) or message.author.bot:
        return

    # On vérifie d'abord si le ticket existe dans la base de données
    if str(message.channel.id) not in bdd["tickets"]:
        return  # Si le ticket n'existe pas, on ne fait rien

    # On ajoute l'utilisateur à la liste des utilisateurs du ticket (si il n'y est pas déjà)
    if not str(message.author.id) in bdd["tickets"][str(message.channel.id)]["utilisateurs"]:
        bdd["tickets"][str(message.channel.id)]["utilisateurs"][str(message.author.id)] = {
            "nom": message.author.name,
            "avatar": str(message.author.avatar)
        }

    # On ajoute le message au transcript
    bdd["tickets"][str(message.channel.id)]["transcript"].append(
        {
            "type": "message",
            "utilisateur": message.author.id,
            "message": message.content,
            "timestamp": int(time.time())
        }
    )

    # Et on sauvegarde !
    with open("db.json", "w") as base:
        base.write(json.dumps(bdd, indent=None))


@bot.event
async def on_interaction(inter: discord.Interaction):
    if inter.type == discord.InteractionType.component:
        identifiant = inter.data.get("custom_id")
        if inter.data.get("component_type") == discord.ComponentType.button.value:
            if identifiant == "creer_ticket":
                await creer_ticket(inter)
            elif identifiant == "fermer_ticket":
                # Normalement, ce bouton ne peut être que dans un ticket.
                # Mais on vérifie quand même, au cas où !
                if inter.channel.category_id == int(config["categorie_tickets"]):
                    await inter.response.defer(ephemeral=True)
                    await close_ticket(inter)
                    createur = bdd["tickets"][str(inter.channel.id)]["ouvert_par"]

                    # Suppression de la BDD
                    del bdd["tickets"][str(inter.channel.id)]
                    bdd["utilisateurs"][str(createur)]["tickets"].remove(inter.channel.id)

                    # Et enfin, on sauvegarde !
                    with open("db.json", "w") as base:
                        base.write(json.dumps(bdd, indent=None))


bot.run(os.getenv("TOKEN"))