import os
import sys

import pandas as pd
from colorama import Fore, Style, init

# --- CONFIGURAÇÃO ---
INPUT_FILE = "data/final_schedule.csv"
OUTPUT_EXCEL = "data/Escala_Final_Formatada.xlsx"

# 1. Dicionário de Cores (Tons pastéis para manter a fonte preta legível)
CORES_MEMBROS = {
    "Rhyan": "#DDEBF7",  # Azul claro
    "Grazy de Melo": "#FCE4D6",  # Pêssego/Laranja claro
    "Gabriel": "#E2EFDA",  # Verde claro
    "Adryan Gabriel": "#FFF2CC",  # Amarelo claro
    "Joao Alencar": "#E4DFEC",  # Roxo/Lilás claro
}

MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

init(autoreset=True)


def view_schedule():
    print(f"{Fore.CYAN}🔍 Lendo arquivo de escala: {INPUT_FILE}...{Style.RESET_ALL}")

    if not os.path.exists(INPUT_FILE):
        print(f"{Fore.RED}❌ Erro: Arquivo '{INPUT_FILE}' não encontrado.")
        print("   Rode o 'main.py' primeiro para gerar a escala.")
        return

    try:
        df = pd.read_csv(INPUT_FILE)

        # Converter para data real para ordenação e extração do mês
        df["date"] = pd.to_datetime(df["date"], dayfirst=True)

        # Criar a Tabela Pivô
        pivot_df = df.pivot_table(
            index=["date", "event"],
            columns="role",
            values="member_name",
            aggfunc=lambda x: ", ".join(x),
        ).fillna("-")

        # Transformar os índices (date e event) em colunas normais
        pivot_df.columns.name = None
        pivot_df = pivot_df.reset_index()

        # Roles already separated by slots in solver (e.g. Sonoplastia 1, Sonoplastia 2)

        # Determinar o mês base (pega a primeira data da escala)
        mes_base = pivot_df["date"].iloc[0].month if not pivot_df.empty else 1
        nome_mes = MESES.get(mes_base, "")

        # Formatar a data para exibição limpa (remove o horário 00:00:00)
        pivot_df["date"] = pivot_df["date"].dt.date

        # Formatação para o Terminal
        print("\n" + "=" * 60)
        print(f"{Fore.GREEN}📅  VISUALIZAÇÃO DA ESCALA  📅{Style.RESET_ALL}")
        print("=" * 60)

        try:
            from tabulate import tabulate

            print(
                tabulate(
                    pivot_df, headers="keys", tablefmt="fancy_grid", showindex=False
                )
            )
        except ImportError:
            print(pivot_df.to_string(index=False))
            print(
                f"\n{Fore.YELLOW}💡 Dica: Instale 'tabulate' para tabelas mais bonitas: pip install tabulate{Style.RESET_ALL}"
            )

        print(f"\n{Fore.CYAN}💾 Exportando para Excel...{Style.RESET_ALL}")

        # 3. Exportar para Excel com Título Mesclado e Cores Automáticas
        with pd.ExcelWriter(
            OUTPUT_EXCEL, engine="xlsxwriter", datetime_format="dd-mm-yyyy"
        ) as writer:
            workbook = writer.book

            # startrow=1 libera a primeira linha (0) para o nosso título mesclado
            pivot_df.to_excel(writer, sheet_name="Escala", index=False, startrow=1)
            worksheet = writer.sheets["Escala"]

            # -- Formatação do Título (Merge Cell) --
            titulo_format = workbook.add_format(
                {
                    "bold": True,
                    "align": "center",
                    "valign": "vcenter",
                    "fg_color": "#D9E1F2",
                    "border": 1,
                    "font_size": 14,
                }
            )

            num_cols = len(pivot_df.columns) - 1
            texto_titulo = f"Escala Sonoplastia - Mês {nome_mes}"
            # Funde da linha 0, coluna 0 até a linha 0, última coluna
            worksheet.merge_range(0, 0, 0, num_cols, texto_titulo, titulo_format)

            # -- Aplicação das Cores (Formatação Condicional) --
            linha_fim = len(pivot_df) + 1

            for membro, hex_cor in CORES_MEMBROS.items():
                fmt_cor = workbook.add_format(
                    {"bg_color": hex_cor, "font_color": "black"}
                )

                # Aplica a cor em todas as colunas de cargos (da coluna 2 em diante)
                for col_idx in range(2, len(pivot_df.columns)):
                    worksheet.conditional_format(
                        2,
                        col_idx,
                        linha_fim,
                        col_idx,
                        {
                            "type": "cell",
                            "criteria": "==",
                            "value": f'"{membro}"',
                            "format": fmt_cor,
                        },
                    )

            worksheet.autofit()

        print(
            f"{Fore.GREEN}✅ Sucesso! Arquivo pronto em: {OUTPUT_EXCEL}{Style.RESET_ALL}"
        )

    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao processar escala: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    view_schedule()
