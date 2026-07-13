import flet as ft
import uuid
import json
import os
from datetime import date, datetime


# =====================================================================
# PALETA DE CORES (usamos strings hex em vez de ft.colors/ft.icons
# para manter compatibilidade entre diferentes versões do Flet)
# =====================================================================

COR_FUNDO = "#12121c"
COR_CARD = "#1c1c2b"
COR_PRIMARIA = "#7c4dff"
COR_TEXTO_SECUNDARIO = "#9a9ab0"
COR_SUCESSO = "#4caf50"
COR_ANDAMENTO = "#ffb300"
COR_ALERTA = "#e57373"
COR_BARRA_FUNDO = "#2a2a3d"

ALTURA_LISTA_MISSOES = 430
DIAS_ALERTA_PRAZO = 3

CATEGORIAS_FIXAS = ["Acadêmica", "Espiritual", "Pessoal"]
CATEGORIA_OUTRO = "Outro"
CATEGORIAS_GRAFICO = CATEGORIAS_FIXAS + [CATEGORIA_OUTRO]

ICONE_CATEGORIA = {
    "Acadêmica": "🎓",
    "Espiritual": "🙏",
    "Pessoal": "🌱",
    CATEGORIA_OUTRO: "✨",
}

CORES_CATEGORIA = {
    "Acadêmica": "#4dd0e1",
    "Espiritual": "#ba68c8",
    "Pessoal": "#81c784",
    CATEGORIA_OUTRO: "#ffb74d",
}


def bucket_categoria(categoria):
    return categoria if categoria in CATEGORIAS_FIXAS else CATEGORIA_OUTRO


def formatar_data_br(data_iso):
    if not data_iso:
        return "-"
    try:
        return date.fromisoformat(data_iso).strftime("%d/%m/%Y")
    except ValueError:
        return "-"


def texto_e_cor_prazo(missao):
    if missao.get("concluida"):
        return None

    data_fim_texto = missao.get("data_fim")
    if not data_fim_texto:
        return None

    try:
        data_fim = date.fromisoformat(data_fim_texto)
    except ValueError:
        return None

    dias_restantes = (data_fim - date.today()).days

    if dias_restantes < 0:
        return f"⚠️ Venceu há {abs(dias_restantes)} dia(s)", COR_ALERTA
    if dias_restantes == 0:
        return "⏰ Prazo é hoje!", COR_ANDAMENTO
    if dias_restantes <= DIAS_ALERTA_PRAZO:
        return f"⏰ Faltam {dias_restantes} dia(s)", COR_ANDAMENTO
    return f"Faltam {dias_restantes} dia(s)", COR_TEXTO_SECUNDARIO


DIRETORIO_DADOS = os.getenv("FLET_APP_STORAGE_DATA", ".")
os.makedirs(DIRETORIO_DADOS, exist_ok=True)
CAMINHO_ARQUIVO_DADOS = os.path.join(DIRETORIO_DADOS, "missoes.json")


def main(page: ft.Page):

    page.title = "Central de Missões"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COR_FUNDO

    page.window_width = 360
    page.window_height = 720
    page.window_resizable = False

    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    class Estado:
        def __init__(self):
            self.missoes = []
            self.nova_missao = {}

    estado = Estado()

    def salvar_estado():
        try:
            with open(CAMINHO_ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
                json.dump(estado.missoes, arquivo)
        except Exception as ex:
            print(f"Erro ao salvar estado: {ex}")

    def carregar_estado():
        try:
            if os.path.exists(CAMINHO_ARQUIVO_DADOS):
                with open(CAMINHO_ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
                    estado.missoes = json.load(arquivo)
        except Exception as ex:
            print(f"Erro ao carregar estado: {ex}")
            estado.missoes = []

    def calcular_progresso(missao):
        if missao["xp_total"] == 0:
            return 0.0
        return missao["xp_atual"] / missao["xp_total"]

    def etapas_concluidas_count(missao):
        return sum(1 for etapa in missao["etapas"] if etapa["concluida"])

    def buscar_missao(missao_id):
        for missao in estado.missoes:
            if missao["id"] == missao_id:
                return missao
        return None

    def distribuir_xp_por_etapas(xp_total, quantidade_etapas):
        base = xp_total // quantidade_etapas
        resto = xp_total % quantidade_etapas

        valores = [base] * quantidade_etapas
        valores[-1] += resto
        return valores

    def calcular_xp_por_categoria():
        totais = {categoria: 0 for categoria in CATEGORIAS_GRAFICO}
        for missao in estado.missoes:
            categoria = missao.get("categoria", CATEGORIA_OUTRO)
            totais[bucket_categoria(categoria)] += missao["xp_atual"]
        return totais

    def missoes_perto_do_prazo():
        resultado = []
        for missao in estado.missoes:
            info = texto_e_cor_prazo(missao)
            if info is None:
                continue
            texto, cor = info
            if cor in (COR_ALERTA, COR_ANDAMENTO):
                resultado.append((missao, texto))
        return resultado

    def ir_para(tela_func, *args):
        page.clean()
        tela_func(*args)
        page.update()

    def mostrar_erro(mensagem):
        page.show_dialog(ft.SnackBar(ft.Text(mensagem), bgcolor="#d32f2f"))
        page.update()

    def notificar_prazos_proximos():
        pendentes = missoes_perto_do_prazo()
        if not pendentes:
            return

        partes = [f"{missao['titulo']} ({texto})" for missao, texto in pendentes]
        mensagem = "⏰ Prazos para acompanhar: " + " | ".join(partes)

        page.show_dialog(
            ft.SnackBar(
                ft.Text(mensagem),
                bgcolor=COR_ANDAMENTO,
                duration=6000,
            )
        )
        page.update()

    def botao_grande(texto, on_click, cor=COR_PRIMARIA):
        return ft.ElevatedButton(
            content=ft.Text(texto, size=16, weight="bold"),
            width=300,
            height=52,
            bgcolor=cor,
            color="#ffffff",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
            on_click=on_click,
        )

    def titulo_tela(texto, size=26):
        return ft.Text(texto, size=size, weight="bold", text_align="center")

    def cabecalho_voltar(destino, *args):
        return ft.Row(
            [ft.TextButton("⬅ Voltar", on_click=lambda e: ir_para(destino, *args))],
            alignment="start",
        )

    def campo_texto(label, hint_text="", value=""):
        return ft.TextField(
            label=label,
            hint_text=hint_text,
            value=value,
            width=300,
            border_radius=12,
        )

    def etiqueta_categoria(categoria):
        grupo = bucket_categoria(categoria)
        cor = CORES_CATEGORIA.get(grupo, CORES_CATEGORIA[CATEGORIA_OUTRO])
        icone = ICONE_CATEGORIA.get(grupo, ICONE_CATEGORIA[CATEGORIA_OUTRO])

        return ft.Container(
            content=ft.Text(f"{icone} {categoria}", size=11, weight="bold", color="#12121c"),
            bgcolor=cor,
            padding=ft.Padding(left=10, right=10, top=3, bottom=3),
            border_radius=20,
        )

    def tela_central():

        def iniciar_nova_missao(e):
            estado.nova_missao = {}
            ir_para(tela_nova_missao_nome)

        cards = [cartao_missao(missao) for missao in estado.missoes]

        if cards:
            lista = ft.ReorderableListView(
                controls=cards,
                on_reorder=mudar_ordem_missoes,
                width=320,
                height=ALTURA_LISTA_MISSOES,
            )
        else:
            lista = ft.Container(
                content=ft.Text(
                    "Nenhuma missão cadastrada.\nCrie a sua primeira missão!",
                    text_align="center",
                    size=15,
                    color=COR_TEXTO_SECUNDARIO,
                ),
                padding=30,
            )

        page.add(
            ft.Column(
                [
                    ft.Text("🎯", size=40, text_align="center"),
                    titulo_tela("Central de Missões"),
                    ft.Container(height=6),
                    botao_grande("➕ Nova missão", iniciar_nova_missao),
                    ft.TextButton(
                        "📊 Ver progresso por área",
                        on_click=lambda e: ir_para(tela_dashboard),
                    ),
                    ft.Text(
                        "Toque e segure um card para arrastar e reordenar",
                        size=12,
                        color=COR_TEXTO_SECUNDARIO,
                        text_align="center",
                    ) if cards else ft.Container(),
                    ft.Container(height=6),
                    lista,
                ],
                horizontal_alignment="center",
                spacing=10,
            )
        )

    def mudar_ordem_missoes(e):
        indice_antigo = e.old_index
        indice_novo = e.new_index

        if indice_novo > indice_antigo:
            indice_novo -= 1

        missao_movida = estado.missoes.pop(indice_antigo)
        estado.missoes.insert(indice_novo, missao_movida)

        salvar_estado()
        ir_para(tela_central)

    def cartao_missao(missao):

        progresso = calcular_progresso(missao)
        concluidas = etapas_concluidas_count(missao)
        total_etapas = len(missao["etapas"])
        categoria = missao.get("categoria", CATEGORIA_OUTRO)

        if missao["concluida"]:
            status_texto = "✅ Missão concluída"
            status_cor = COR_SUCESSO
        else:
            status_texto = "⏳ Em andamento"
            status_cor = COR_ANDAMENTO

        itens_card = [
            ft.Row(
                [
                    ft.Text(
                        missao["titulo"],
                        size=18,
                        weight="bold",
                        expand=True,
                    ),
                    ft.Text(
                        "⠿",
                        size=18,
                        color=COR_TEXTO_SECUNDARIO,
                    ),
                    ft.TextButton(
                        "🗑",
                        on_click=lambda e, m=missao: confirmar_exclusao(m),
                    ),
                ],
            ),
            etiqueta_categoria(categoria),
        ]

        if missao.get("data_inicio") or missao.get("data_fim"):
            itens_card.append(
                ft.Text(
                    f"📅 {formatar_data_br(missao.get('data_inicio'))} → "
                    f"{formatar_data_br(missao.get('data_fim'))}",
                    size=12,
                    color=COR_TEXTO_SECUNDARIO,
                )
            )

        info_prazo = texto_e_cor_prazo(missao)
        if info_prazo:
            texto_prazo, cor_prazo = info_prazo
            itens_card.append(
                ft.Text(texto_prazo, size=12, weight="bold", color=cor_prazo)
            )

        itens_card += [
            ft.ProgressBar(
                value=progresso,
                width=280,
                bgcolor=COR_BARRA_FUNDO,
                color=COR_PRIMARIA,
            ),
            ft.Text(f"{missao['xp_atual']} / {missao['xp_total']} XP", size=14),
        ]

        if total_etapas > 0:
            itens_card.append(
                ft.Text(
                    f"Etapas concluídas: {concluidas}/{total_etapas}",
                    size=13,
                    color=COR_TEXTO_SECUNDARIO,
                )
            )

        itens_card.append(
            ft.Text(status_texto, size=13, weight="bold", color=status_cor)
        )

        return ft.Container(
            key=missao["id"],
            content=ft.Column(itens_card, spacing=6),
            bgcolor=COR_CARD,
            padding=16,
            margin=ft.Margin(bottom=14),
            border_radius=16,
            width=320,
            on_click=lambda e, mid=missao["id"]: ir_para(tela_missao_detalhe, mid),
        )

    def confirmar_exclusao(missao):

        def excluir(e):
            if missao in estado.missoes:
                estado.missoes.remove(missao)
                salvar_estado()
            page.pop_dialog()
            ir_para(tela_central)

        def cancelar(e):
            page.pop_dialog()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Excluir missão"),
            content=ft.Text(
                f'Deseja excluir a missão "{missao["titulo"]}"? '
                "Essa ação não pode ser desfeita."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Excluir", on_click=excluir),
            ],
            actions_alignment="end",
        )

        page.show_dialog(dialogo)

    def tela_dashboard():

        totais = calcular_xp_por_categoria()
        maior_valor = max(totais.values())
        maior_valor = maior_valor if maior_valor > 0 else 1

        largura_maxima_barra = 240

        linhas_grafico = []
        for categoria in CATEGORIAS_GRAFICO:
            valor = totais[categoria]
            largura_barra = max(6, (valor / maior_valor) * largura_maxima_barra)
            cor = CORES_CATEGORIA[categoria]
            icone = ICONE_CATEGORIA[categoria]

            linhas_grafico.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f"{icone} {categoria}", size=14, weight="bold"),
                                ft.Text(f"{valor} XP", size=13, color=COR_TEXTO_SECUNDARIO),
                            ],
                            width=280,
                            alignment="spaceBetween",
                        ),
                        ft.Container(
                            content=ft.Container(
                                bgcolor=cor,
                                width=largura_barra,
                                height=18,
                                border_radius=8,
                            ),
                            bgcolor=COR_BARRA_FUNDO,
                            width=280,
                            height=18,
                            border_radius=8,
                        ),
                    ],
                    spacing=6,
                )
            )

        xp_total_geral = sum(totais.values())

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("📊 Progresso por área", 22),
                    ft.Text(
                        f"Total acumulado: {xp_total_geral} XP",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO,
                    ),
                    ft.Container(height=8),
                    *linhas_grafico,
                ],
                horizontal_alignment="center",
                spacing=18,
            )
        )

    def tela_nova_missao_nome():

        campo = campo_texto(
            "Nome da missão",
            hint_text="Ex: escrever a introdução do artigo",
            value=estado.nova_missao.get("titulo", ""),
        )

        def avancar(e):
            titulo = (campo.value or "").strip()
            if not titulo:
                mostrar_erro("Digite um nome para a missão.")
                return
            estado.nova_missao["titulo"] = titulo
            ir_para(tela_nova_missao_categoria)

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("🆕 Nova Missão", 24),
                    ft.Text("Qual é a sua missão?", size=16),
                    campo,
                    botao_grande("Próximo ➡", avancar),
                ],
                horizontal_alignment="center",
                spacing=16,
            )
        )

    def tela_nova_missao_categoria():

        def escolher_categoria(categoria):
            estado.nova_missao["categoria"] = categoria
            ir_para(tela_nova_missao_esforco)

        def escolher_outro(e):
            ir_para(tela_nova_missao_categoria_personalizada)

        botoes_categoria = [
            botao_grande(
                f"{ICONE_CATEGORIA[categoria]} {categoria}",
                (lambda e, c=categoria: escolher_categoria(c)),
                cor=CORES_CATEGORIA[categoria],
            )
            for categoria in CATEGORIAS_FIXAS
        ]

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_nova_missao_nome),
                    titulo_tela("🏷️ Área da vida", 24),
                    ft.Text(estado.nova_missao.get("titulo", ""), size=18),
                    ft.Text(
                        "Em qual área essa missão se encaixa?",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO,
                    ),
                    *botoes_categoria,
                    botao_grande(
                        f"{ICONE_CATEGORIA[CATEGORIA_OUTRO]} Outra (personalizada)",
                        escolher_outro,
                        cor=CORES_CATEGORIA[CATEGORIA_OUTRO],
                    ),
                ],
                horizontal_alignment="center",
                spacing=14,
            )
        )

    def tela_nova_missao_categoria_personalizada():

        campo = campo_texto(
            "Nome da categoria",
            hint_text="Ex: Viagens, Família, Finanças",
        )

        def confirmar(e):
            nome_categoria = (campo.value or "").strip()
            if not nome_categoria:
                mostrar_erro("Digite um nome para a categoria.")
                return
            estado.nova_missao["categoria"] = nome_categoria
            ir_para(tela_nova_missao_esforco)

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_nova_missao_categoria),
                    titulo_tela("✨ Nova categoria", 22),
                    campo,
                    botao_grande("Confirmar categoria", confirmar),
                ],
                horizontal_alignment="center",
                spacing=16,
            )
        )

    def tela_nova_missao_esforco():

        def escolher(valor):
            estado.nova_missao["xp_total"] = valor
            ir_para(tela_nova_missao_recompensa)

        niveis = [
            ("Mínimo - 125 XP", 125),
            ("Médio - 250 XP", 250),
            ("Máximo - 500 XP", 500),
            ("Extremo - 1000 XP", 1000),
        ]

        botoes_nivel = [
            botao_grande(texto, (lambda e, v=valor: escolher(v)))
            for texto, valor in niveis
        ]

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("⚔️ Nível de esforço", 24),
                    ft.Text(estado.nova_missao.get("titulo", ""), size=18),
                    *botoes_nivel,
                ],
                horizontal_alignment="center",
                spacing=14,
            )
        )

    def tela_nova_missao_recompensa():

        campo = campo_texto(
            "Defina sua recompensa",
            hint_text="Ex: assistir meu filme favorito",
            value=estado.nova_missao.get("recompensa", ""),
        )

        def salvar(e):
            recompensa = (campo.value or "").strip()
            if not recompensa:
                mostrar_erro("Digite uma recompensa para a missão.")
                return
            estado.nova_missao["recompensa"] = recompensa
            ir_para(tela_nova_missao_datas)

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("🎁 Recompensa", 26),
                    ft.Text("Ela será liberada após completar a missão."),
                    campo,
                    botao_grande("Definir recompensa", salvar),
                ],
                horizontal_alignment="center",
                spacing=16,
            )
        )

    def tela_nova_missao_datas():

        prazo_temp = {
            "data_inicio": estado.nova_missao.get("data_inicio"),
            "data_fim": estado.nova_missao.get("data_fim"),
        }

        texto_inicio = ft.Text(
            f"📆 Início: {formatar_data_br(prazo_temp['data_inicio'])}"
            if prazo_temp["data_inicio"]
            else "📆 Início: não selecionada",
            size=14,
        )
        texto_fim = ft.Text(
            f"🏁 Término: {formatar_data_br(prazo_temp['data_fim'])}"
            if prazo_temp["data_fim"]
            else "🏁 Término: não selecionada",
            size=14,
        )

        def selecionar_inicio(e):
            if e.control.value:
                prazo_temp["data_inicio"] = e.control.value.date().isoformat()
                texto_inicio.value = f"📆 Início: {formatar_data_br(prazo_temp['data_inicio'])}"
                page.update()

        def selecionar_fim(e):
            if e.control.value:
                prazo_temp["data_fim"] = e.control.value.date().isoformat()
                texto_fim.value = f"🏁 Término: {formatar_data_br(prazo_temp['data_fim'])}"
                page.update()

        seletor_inicio = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=selecionar_inicio,
        )
        seletor_fim = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=selecionar_fim,
        )

        def avancar(e):
            data_inicio = prazo_temp["data_inicio"]
            data_fim = prazo_temp["data_fim"]

            if bool(data_inicio) != bool(data_fim):
                mostrar_erro("Selecione as duas datas ou deixe o prazo em branco.")
                return

            if data_inicio and data_fim and date.fromisoformat(data_fim) < date.fromisoformat(data_inicio):
                mostrar_erro("A data de término não pode ser antes da data de início.")
                return

            estado.nova_missao["data_inicio"] = data_inicio
            estado.nova_missao["data_fim"] = data_fim
            ir_para(tela_nova_missao_etapas)

        def pular(e):
            estado.nova_missao["data_inicio"] = None
            estado.nova_missao["data_fim"] = None
            ir_para(tela_nova_missao_etapas)

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("📅 Prazo da missão", 22),
                    ft.Text(
                        "Definir um prazo é opcional. Toque nos botões para "
                        "escolher as datas no calendário.",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO,
                        text_align="center",
                    ),
                    texto_inicio,
                    ft.OutlinedButton(
                        "Escolher data de início",
                        on_click=lambda e: page.show_dialog(seletor_inicio),
                    ),
                    texto_fim,
                    ft.OutlinedButton(
                        "Escolher data de término",
                        on_click=lambda e: page.show_dialog(seletor_fim),
                    ),
                    ft.Container(height=6),
                    botao_grande("Próximo ➡", avancar),
                    ft.TextButton(
                        "Pular (missão sem prazo definido)",
                        on_click=pular,
                    ),
                ],
                horizontal_alignment="center",
                spacing=14,
            )
        )

    def tela_nova_missao_etapas():

        etapas_temp = estado.nova_missao.setdefault("etapas_temp", [])

        lista_etapas = ft.Column(spacing=6)

        campo_etapa = campo_texto(
            "Nome da etapa",
            hint_text="Ex: pesquisar referências",
        )

        def atualizar_lista():
            lista_etapas.controls = [
                ft.Row(
                    [
                        ft.Text(f"{i + 1}. {nome}", size=14, expand=True),
                        ft.TextButton(
                            "🗑",
                            on_click=lambda e, indice=i: remover_etapa(indice),
                        ),
                    ],
                    width=300,
                )
                for i, nome in enumerate(etapas_temp)
            ]

        def adicionar_etapa(e):
            nome = (campo_etapa.value or "").strip()
            if not nome:
                mostrar_erro("Digite o nome da etapa antes de adicionar.")
                return
            etapas_temp.append(nome)
            campo_etapa.value = ""
            atualizar_lista()
            page.update()

        def remover_etapa(indice):
            etapas_temp.pop(indice)
            atualizar_lista()
            page.update()

        def finalizar(e):
            if not etapas_temp:
                mostrar_erro(
                    "Adicione ao menos uma etapa, ou toque em "
                    "'Missão sem etapas' para pular."
                )
                return
            nomes = list(etapas_temp)
            estado.nova_missao.pop("etapas_temp", None)
            finalizar_criacao_missao(nomes)

        def pular(e):
            estado.nova_missao.pop("etapas_temp", None)
            finalizar_criacao_missao([])

        atualizar_lista()

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_nova_missao_datas),
                    titulo_tela("📌 Etapas da missão", 22),
                    ft.Text(
                        "Adicione as etapas uma de cada vez, sem precisar "
                        "definir a quantidade antes. É opcional.",
                        size=14,
                        color=COR_TEXTO_SECUNDARIO,
                        text_align="center",
                    ),
                    campo_etapa,
                    botao_grande("➕ Adicionar etapa", adicionar_etapa),
                    lista_etapas,
                    ft.Container(height=6),
                    botao_grande("✅ Próximo", finalizar),
                    ft.TextButton(
                        "Pular (missão sem etapas)",
                        on_click=pular,
                    ),
                ],
                horizontal_alignment="center",
                spacing=14,
            )
        )

    def finalizar_criacao_missao(nomes_etapas):

        xp_total = estado.nova_missao["xp_total"]

        if nomes_etapas:
            valores_xp = distribuir_xp_por_etapas(xp_total, len(nomes_etapas))
            etapas = [
                {"nome": nome, "xp": xp, "concluida": False}
                for nome, xp in zip(nomes_etapas, valores_xp)
            ]
        else:
            etapas = []

        missao = {
            "id": str(uuid.uuid4()),
            "titulo": estado.nova_missao["titulo"],
            "categoria": estado.nova_missao.get("categoria", CATEGORIA_OUTRO),
            "data_inicio": estado.nova_missao.get("data_inicio"),
            "data_fim": estado.nova_missao.get("data_fim"),
            "recompensa": estado.nova_missao["recompensa"],
            "xp_total": xp_total,
            "xp_atual": 0,
            "concluida": False,
            "etapas": etapas,
        }

        estado.missoes.append(missao)
        estado.nova_missao = {}
        salvar_estado()

        ir_para(tela_central)

    def tela_missao_detalhe(missao_id):

        missao = buscar_missao(missao_id)

        if missao is None:
            ir_para(tela_central)
            return

        progresso = calcular_progresso(missao)
        categoria = missao.get("categoria", CATEGORIA_OUTRO)

        botoes_etapas = []

        for etapa in missao["etapas"]:
            rotulo = f"{'✅' if etapa['concluida'] else '▶'} {etapa['nome']} (+{etapa['xp']} XP)"

            botoes_etapas.append(
                ft.ElevatedButton(
                    rotulo,
                    width=300,
                    disabled=etapa["concluida"],
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=lambda e, m=missao, et=etapa: concluir_etapa(m, et),
                )
            )

        corpo = [
            cabecalho_voltar(tela_central),
            titulo_tela(missao["titulo"], 24),
            etiqueta_categoria(categoria),
        ]

        if missao.get("data_inicio") or missao.get("data_fim"):
            corpo.append(
                ft.Text(
                    f"📅 {formatar_data_br(missao.get('data_inicio'))} → "
                    f"{formatar_data_br(missao.get('data_fim'))}",
                    size=13,
                    color=COR_TEXTO_SECUNDARIO,
                )
            )

        info_prazo = texto_e_cor_prazo(missao)
        if info_prazo:
            texto_prazo, cor_prazo = info_prazo
            corpo.append(ft.Text(texto_prazo, size=13, weight="bold", color=cor_prazo))

        corpo += [
            ft.ProgressBar(
                value=progresso, width=300, bgcolor=COR_BARRA_FUNDO, color=COR_PRIMARIA
            ),
            ft.Text(f"{missao['xp_atual']} / {missao['xp_total']} XP", size=16),
        ]

        if missao["concluida"]:
            corpo += [
                ft.Container(height=6),
                ft.Text("🏆 Missão concluída!", size=20, weight="bold", color=COR_SUCESSO),
                ft.Text("Recompensa:", size=14),
                ft.Text(missao["recompensa"], size=20, weight="bold"),
                ft.Container(height=6),
            ]

        if missao["etapas"]:
            corpo.append(ft.Text("Etapas:", size=16, weight="bold"))
            corpo.extend(botoes_etapas)
        elif not missao["concluida"]:
            corpo.append(
                ft.Text(
                    "Esta missão não foi dividida em etapas.",
                    size=13,
                    color=COR_TEXTO_SECUNDARIO,
                    text_align="center",
                )
            )
            corpo.append(
                ft.ElevatedButton(
                    "✅ Concluir missão",
                    width=300,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=lambda e, m=missao: concluir_missao_sem_etapas(m),
                )
            )

        page.add(
            ft.Column(corpo, horizontal_alignment="center", spacing=12)
        )

    def concluir_etapa(missao, etapa):

        etapa["concluida"] = True
        missao["xp_atual"] += etapa["xp"]

        if all(e["concluida"] for e in missao["etapas"]):
            missao["concluida"] = True
            salvar_estado()
            ir_para(tela_missao_concluida, missao["id"])
        else:
            salvar_estado()
            ir_para(tela_missao_detalhe, missao["id"])

    def concluir_missao_sem_etapas(missao):

        missao["xp_atual"] = missao["xp_total"]
        missao["concluida"] = True
        salvar_estado()
        ir_para(tela_missao_concluida, missao["id"])

    def tela_missao_concluida(missao_id):

        missao = buscar_missao(missao_id)
        recompensa = missao["recompensa"] if missao else ""

        page.add(
            ft.Column(
                [
                    ft.Text("🏆", size=50, text_align="center"),
                    titulo_tela("MISSÃO CUMPRIDA!", 28),
                    ft.Text("Sua recompensa:", size=16),
                    ft.Text(recompensa, size=24, weight="bold", text_align="center"),
                    ft.Text("Aproveite! 🎉", size=18),
                    ft.Container(height=10),
                    botao_grande(
                        "Voltar para Central de Missões",
                        lambda e: ir_para(tela_central),
                    ),
                ],
                horizontal_alignment="center",
                spacing=16,
            )
        )

    carregar_estado()
    tela_central()
    notificar_prazos_proximos()


if __name__ == "__main__":
    ft.app(target=main)