import os
import sys

import pandas as pd
from colorama import Fore, Style, init

# --- CONFIGURAÇÃO ---
# Caminho do arquivo gerado pelo seu main.py
INPUT_FILE = "data/generated_schedule.csv"
OUTPUT_EXCEL = "data/Escala_Final_Formatada.xlsx"

# Cores para o terminal
init(autoreset=True)


def view_schedule():
    print(f"{Fore.CYAN}🔍 Lendo arquivo de escala: {INPUT_FILE}...{Style.RESET_ALL}")

    if not os.path.exists(INPUT_FILE):
        print(f"{Fore.RED}❌ Erro: Arquivo '{INPUT_FILE}' não encontrado.")
        print("   Rode o 'main.py' primeiro para gerar a escala.")
        return

    try:
        # 1. Carregar Dados
        df = pd.read_csv(INPUT_FILE)

        # Garantir que a coluna de data seja tratada como data (para ordenar corretamente)
        df["date"] = pd.to_datetime(df["date"])

        # 2. Criar a Tabela Pivô (A Mágica ✨)
        # Index: Data e Evento
        # Columns: Papel (Role)
        # Values: Nome do Membro
        pivot_df = df.pivot_table(
            index=["date", "event"],
            columns="role",
            values="member_name",
            aggfunc=lambda x: ", ".join(
                x
            ),  # Caso haja 2 pessoas na mesma função (ex: 2 BackVocals), junta com vírgula
        ).fillna("-")  # Onde não tem ninguém, põe um tracinho

        # 3. Formatação para o Terminal
        print("\n" + "=" * 60)
        print(f"{Fore.GREEN}📅  VISUALIZAÇÃO DA ESCALA  📅{Style.RESET_ALL}")
        print("=" * 60)

        # Usamos tabulate se estiver instalado, senão pandas padrão
        try:
            from tabulate import tabulate

            print(tabulate(pivot_df, headers="keys", tablefmt="fancy_grid"))
        except ImportError:
            print(pivot_df)
            print(
                f"\n{Fore.YELLOW}💡 Dica: Instale 'tabulate' para tabelas mais bonitas: pip install tabulate{Style.RESET_ALL}"
            )

        # 4. Exportar para Excel (Formatado)
        print(f"\n{Fore.CYAN}💾 Exportando para Excel...{Style.RESET_ALL}")

        # Ordenar por data antes de salvar
        pivot_df.sort_index(inplace=True)

        # Exportação simples
        pivot_df.to_excel(OUTPUT_EXCEL)

        print(
            f"{Fore.GREEN}✅ Sucesso! Arquivo pronto em: {OUTPUT_EXCEL}{Style.RESET_ALL}"
        )
        print("   (Pode abrir e enviar no WhatsApp!)")

    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao processar escala: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    view_schedule()
