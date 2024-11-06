import discord
import os
from discord.ext import commands
from dotenv import load_dotenv  # Agrega esta línea

load_dotenv()  # Agrega esta línea para cargar las variables de entorno

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

actividades = {
    "Trafico aéreo": {
        "items": [
            "Beretta - $35,000"
        ],
        "recompensa": 35000,
        "emoji": "1️⃣"
    },
    "Barriles": {
        "items": [
            "Glock, Teck, Fosforo, 2 Yodos, 1 Gas butano",
            "1 TEC, 1 Skorpion, 1 Glock, 1 Yodo",
            "Escopeta, Tec, Skorpions",
            "Skorpion, Escopeta, Uzi descargada, 2 Yodos de peróxido, Escáner"
        ],
        "recompensa": 50000,
        "emoji": "2️⃣"
    },
    "Avionetas": {
        "items": [
            "Uzi (15 balas), Skorpion",
            "Luguer, Carga de Asalto, Uzi"
        ],
        "recompensa": 150000,
        "emoji": "3️⃣"
    },
    "Trafico avanzado": {
        "items": [
            "Usp, Glock, Carga de pistola, 2 Gas butano, Tolueno",
            "Tompson, Usp, 2 Cargadores de pistola, Caja de municiones",
            "2 Yodos, 2 Cargadores"
        ],
        "recompensa": 170000,
        "emoji": "4️⃣"
    }
}

usuario_actividades = {}
contador_actividad = 1

@bot.command()
async def actividad(ctx):
    global contador_actividad
    embed = discord.Embed(title="🛠️ Elige una actividad", description="Reacciona con el número correspondiente a la actividad que realizaste.", color=0x00ff00)

    for nombre, info in actividades.items():
        embed.add_field(name=f"{info['emoji']} {nombre}", value=f"Selecciona esta actividad", inline=False)

    message = await ctx.send(embed=embed)

    for info in actividades.values():
        await message.add_reaction(info['emoji'])

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in [info['emoji'] for info in actividades.values()]

    reaction, user = await bot.wait_for('reaction_add', check=check)

    actividad_seleccionada = next(name for name, info in actividades.items() if info['emoji'] == str(reaction.emoji))

    embed_items = discord.Embed(
        title=f"Selecciona los items para {actividad_seleccionada}",
        description="Cada item tiene un valor que se suma al total del resumen final. Reacciona con el número correspondiente al item.",
        color=0x00ff00
    )

    for item in actividades[actividad_seleccionada]["items"]:
        embed_items.add_field(name=item, value="Selecciona este item", inline=False)

    message_items = await ctx.send(embed=embed_items)

    emoji_options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for emoji in emoji_options[:len(actividades[actividad_seleccionada]["items"])]:
        await message_items.add_reaction(emoji)

    def check_items(reaction, user):
        return user == ctx.author and reaction.message.id == message_items.id and str(reaction.emoji) in emoji_options[:len(actividades[actividad_seleccionada]["items"])]

    reaction_items, user = await bot.wait_for('reaction_add', check=check_items)

    item_seleccionado = actividades[actividad_seleccionada]["items"][int(str(reaction_items.emoji)[0]) - 1]

    await ctx.send("¿Cuántos miembros ayudaron en esta actividad? (En caso de ninguno pon 0)")

    def check_members(m):
        return m.author == ctx.author and m.channel == ctx.channel

    message_members = await bot.wait_for('message', check=check_members)
    miembros = int(message_members.content)

    if miembros > 0:
        await ctx.send("Menciona a los miembros que ayudaron.")

        message_mencion = await bot.wait_for('message', check=check_members)
        mencionados = message_mencion.mentions
    else:
        mencionados = []

    await ctx.send("Menciona a quien se lo entregaste.")

    message_entregado = await bot.wait_for('message', check=check_members)
    entregado_a = message_entregado.mentions

    await ctx.send("Adjunta la imagen o el link de la actividad.")

    def check_attachment_or_link(m):
        return m.author == ctx.author and m.channel == ctx.channel

    image_message = await bot.wait_for('message', check=check_attachment_or_link)
    image_url = image_message.attachments[0].url if len(image_message.attachments) > 0 else image_message.content

    if ctx.author.id not in usuario_actividades:
        usuario_actividades[ctx.author.id] = []

    actividad_id = contador_actividad
    contador_actividad += 1

    actividad_data = {
        "id": actividad_id,
        "actividad": actividad_seleccionada,
        "item": item_seleccionado,
        "recompensa": actividades[actividad_seleccionada]['recompensa'],
        "mencionados": [m.mention for m in mencionados],
        "entregado_a": [m.mention for m in entregado_a],
        "imagen_url": image_url
    }
    usuario_actividades[ctx.author.id].append(actividad_data)

    for miembro in mencionados:
        if miembro.id not in usuario_actividades:
            usuario_actividades[miembro.id] = []

        usuario_actividades[miembro.id].append({
            "id": actividad_id,
            "actividad": actividad_seleccionada,
            "item": item_seleccionado,
            "recompensa": round(actividades[actividad_seleccionada]['recompensa'] / miembros),
            "mencionados": [ctx.author.mention],
            "imagen_url": image_url
        })

    recompensa_total = actividades[actividad_seleccionada]['recompensa']
    recompensa_por_miembro = round(recompensa_total / (miembros + 1))

    embed_resumen = discord.Embed(
        title=f"Resumen de la Actividad #{actividad_id}",
        description=f"**Organizador:** {ctx.author.mention}\n"
                    f"**Actividad:** {actividad_seleccionada}\n"
                    f"**Item Seleccionado:** {item_seleccionado}\n"
                    f"**Pago total al organizador:** ${recompensa_total}\n"
                    f"**Recompensa por miembro:** ${recompensa_por_miembro}\n"
                    f"**Miembros que ayudaron:** {', '.join([m.mention for m in mencionados]) if mencionados else 'Nadie'}\n"
                    f"**Se lo entregaste a:** {', '.join([m.mention for m in entregado_a])}\n"
                    f"**Imagen o Link Adjunto:**\n{image_url}",
        color=0x00ff00
    )
    embed_resumen.set_footer(text=f"ID de Actividad: {actividad_id}")
    embed_resumen.set_image(url=image_url if image_message.attachments else None)

    await ctx.send(embed=embed_resumen)

@bot.command()
async def veractividad(ctx, actividad_id: int):
    actividades_usuario = usuario_actividades.get(ctx.author.id, [])
    actividad_encontrada = next((a for a in actividades_usuario if a["id"] == actividad_id), None)

    if actividad_encontrada:
        embed = discord.Embed(
            title=f"Detalles de la Actividad #{actividad_encontrada['id']}",
            description=f"**Actividad:** {actividad_encontrada['actividad']}\n"
                        f"**Item Seleccionado:** {actividad_encontrada['item']}\n"
                        f"**Recompensa Total:** ${actividad_encontrada['recompensa']}\n"
                        f"**Mencionados:** {', '.join(actividad_encontrada['mencionados']) if actividad_encontrada['mencionados'] else 'Nadie'}\n"
                        f"**Entregado a:** {', '.join(actividad_encontrada['entregado_a']) if actividad_encontrada['entregado_a'] else 'Nadie'}\n"
                        f"**Imagen o Link Adjunto:**\n{actividad_encontrada['imagen_url']}",
            color=0x00ff00
        )
        embed.set_image(url=actividad_encontrada['imagen_url'])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No se encontró la actividad con ID {actividad_id}.")

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está conectado y listo para usar!')

bot.run(os.getenv('DISCORD_TOKEN'))
