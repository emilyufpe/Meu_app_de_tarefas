import flet as ft
import uuid


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
COR_BARRA_FUNDO = "#2a2a3d"


def main(page: ft.Page):

    # -----------------------------------------------------------
    # CONFIGURAÇÃO GERAL (MOBILE)
    # -----------------------------------------------------------

    page.title = "Central de Missões"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COR_FUNDO

    page.window_width = 360
    page.window_height = 720
    page.window_resizable = False

    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # =============================================================
    # ESTADO DA APLICAÇÃO
    #
    # Nada de variáveis globais soltas (missao, recompensa, etapas...).
    # Cada missão é um dicionário independente, guardado dentro de
    # `estado.missoes`. Estrutura de cada missão:
    #
    # {
    #     "id": str,
    #     "titulo": str,
    #     "recompensa": str,
    #     "xp_total": int,
    #     "xp_atual": int,
    #     "concluida": bool,
    #     "etapas": [
    #         {"nome": str, "xp": int, "concluida": bool},
    #         ...
    #     ],
    # }
    # =============================================================

    class Estado:
        def __init__(self):
            self.missoes = []          # lista de missões cadastradas
            self.nova_missao = {}      # rascunho usado durante a criação

    estado = Estado()

    # =============================================================
    # FUNÇÕES AUXILIARES DE DADOS
    # =============================================================

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
        """Divide o xp_total entre as etapas sem perder resto na divisão."""
        base = xp_total // quantidade_etapas
        resto = xp_total % quantidade_etapas

        valores = [base] * quantidade_etapas
        valores[-1] += resto  # a última etapa absorve o resto da divisão
        return valores

    # =============================================================
    # NAVEGAÇÃO
    # =============================================================

    def ir_para(tela_func, *args):
        page.clean()
        tela_func(*args)
        page.update()

    def mostrar_erro(mensagem):
        page.show_dialog(ft.SnackBar(ft.Text(mensagem), bgcolor="#d32f2f"))
        page.update()

    # =============================================================
    # COMPONENTES REUTILIZÁVEIS DE UI
    # =============================================================

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

    # =============================================================
    # TELA: CENTRAL DE MISSÕES
    # =============================================================

    def tela_central():

        def iniciar_nova_missao(e):
            estado.nova_missao = {}
            ir_para(tela_nova_missao_nome)

        cards = [cartao_missao(missao) for missao in estado.missoes]

        if cards:
            lista = ft.Column(cards, spacing=14, horizontal_alignment="center")
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
                    ft.Container(height=6),
                    lista,
                ],
                horizontal_alignment="center",
                spacing=10,
            )
        )

    def cartao_missao(missao):

        progresso = calcular_progresso(missao)
        concluidas = etapas_concluidas_count(missao)
        total_etapas = len(missao["etapas"])

        if missao["concluida"]:
            status_texto = "✅ Missão concluída"
            status_cor = COR_SUCESSO
        else:
            status_texto = "⏳ Em andamento"
            status_cor = COR_ANDAMENTO

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                missao["titulo"],
                                size=18,
                                weight="bold",
                                expand=True,
                            ),
                            ft.TextButton(
                                "🗑",
                                on_click=lambda e, m=missao: confirmar_exclusao(m),
                            ),
                        ],
                    ),
                    ft.ProgressBar(
                        value=progresso,
                        width=280,
                        bgcolor=COR_BARRA_FUNDO,
                        color=COR_PRIMARIA,
                    ),
                    ft.Text(f"{missao['xp_atual']} / {missao['xp_total']} XP", size=14),
                    ft.Text(
                        f"Etapas concluídas: {concluidas}/{total_etapas}",
                        size=13,
                        color=COR_TEXTO_SECUNDARIO,
                    ),
                    ft.Text(status_texto, size=13, weight="bold", color=status_cor),
                ],
                spacing=6,
            ),
            bgcolor=COR_CARD,
            padding=16,
            border_radius=16,
            width=320,
            on_click=lambda e, mid=missao["id"]: ir_para(tela_missao_detalhe, mid),
        )

    def confirmar_exclusao(missao):

        def excluir(e):
            if missao in estado.missoes:
                estado.missoes.remove(missao)
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

    # =============================================================
    # FLUXO DE CRIAÇÃO DE MISSÃO
    # Nova missão -> Nome -> Esforço -> Recompensa -> Qtd etapas
    # -> Nome das etapas -> Salvar -> Central de Missões
    # =============================================================

    def tela_nova_missao_nome():

        campo = campo_texto(
            "Nome da missão",
            hint_text="Ex: escrever introdução do artigo",
            value=estado.nova_missao.get("titulo", ""),
        )

        def avancar(e):
            titulo = (campo.value or "").strip()
            if not titulo:
                mostrar_erro("Digite um nome para a missão.")
                return
            estado.nova_missao["titulo"] = titulo
            ir_para(tela_nova_missao_esforco)

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
            ir_para(tela_nova_missao_qtd_etapas)

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

    def tela_nova_missao_qtd_etapas():

        campo = campo_texto("Quantidade de etapas")
        campo.keyboard_type = ft.KeyboardType.NUMBER

        def avancar(e):
            texto = (campo.value or "").strip()

            if not texto.isdigit() or int(texto) <= 0:
                mostrar_erro("Informe um número válido de etapas (maior que 0).")
                return

            ir_para(tela_nova_missao_nomes_etapas, int(texto))

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_central),
                    titulo_tela("📌 Divida sua missão", 24),
                    campo,
                    botao_grande("Criar etapas", avancar),
                ],
                horizontal_alignment="center",
                spacing=16,
            )
        )

    def tela_nova_missao_nomes_etapas(quantidade):

        campos = [
            campo_texto(f"Etapa {i + 1}") for i in range(quantidade)
        ]

        def salvar(e):
            nomes = [(c.value or "").strip() for c in campos]

            if any(nome == "" for nome in nomes):
                mostrar_erro("Preencha o nome de todas as etapas.")
                return

            finalizar_criacao_missao(nomes)

        page.add(
            ft.Column(
                [
                    cabecalho_voltar(tela_nova_missao_qtd_etapas),
                    titulo_tela("📝 Nomeie as etapas", 22),
                    *campos,
                    botao_grande("Salvar missão", salvar),
                ],
                horizontal_alignment="center",
                spacing=14,
            )
        )

    def finalizar_criacao_missao(nomes_etapas):

        xp_total = estado.nova_missao["xp_total"]
        valores_xp = distribuir_xp_por_etapas(xp_total, len(nomes_etapas))

        etapas = [
            {"nome": nome, "xp": xp, "concluida": False}
            for nome, xp in zip(nomes_etapas, valores_xp)
        ]

        missao = {
            "id": str(uuid.uuid4()),
            "titulo": estado.nova_missao["titulo"],
            "recompensa": estado.nova_missao["recompensa"],
            "xp_total": xp_total,
            "xp_atual": 0,
            "concluida": False,
            "etapas": etapas,
        }

        estado.missoes.append(missao)
        estado.nova_missao = {}

        ir_para(tela_central)

    # =============================================================
    # TELA: DETALHE / PROGRESSO DA MISSÃO
    # =============================================================

    def tela_missao_detalhe(missao_id):

        missao = buscar_missao(missao_id)

        if missao is None:
            ir_para(tela_central)
            return

        progresso = calcular_progresso(missao)

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

        corpo.append(ft.Text("Etapas:", size=16, weight="bold"))
        corpo.extend(botoes_etapas)

        page.add(
            ft.Column(corpo, horizontal_alignment="center", spacing=12)
        )

    def concluir_etapa(missao, etapa):

        etapa["concluida"] = True
        missao["xp_atual"] += etapa["xp"]

        if all(e["concluida"] for e in missao["etapas"]):
            missao["concluida"] = True
            ir_para(tela_missao_concluida, missao["id"])
        else:
            ir_para(tela_missao_detalhe, missao["id"])

    # =============================================================
    # TELA: MISSÃO CONCLUÍDA (RECOMPENSA)
    # =============================================================

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

    # =============================================================
    # INÍCIO DO APP
    # =============================================================

    tela_central()


if __name__ == "__main__":
    ft.app(target=main)