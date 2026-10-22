
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dashboard.models import Domain, ExpectedMX


class Command(BaseCommand):
    help = "Importa domínios e seus MX esperados de um arquivo separado por ponto e vírgula."

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            type=str,
            help="Caminho do arquivo no formato dominio;servidor_mx",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        caminho = Path(options["arquivo"])

        if not caminho.is_file():
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        importados = 0
        ignorados = 0

        with caminho.open("r", encoding="utf-8-sig") as arquivo:
            for numero, linha in enumerate(arquivo, start=1):
                linha = linha.strip()

                if not linha:
                    continue

                partes = linha.split(";")

                if len(partes) != 2:
                    raise CommandError(
                        f"Linha {numero} inválida: esperado dominio;servidor_mx"
                    )

                dominio_nome = partes[0].strip().lower().rstrip(".")
                servidor_mx = partes[1].strip().lower().rstrip(".")

                if not dominio_nome or not servidor_mx:
                    raise CommandError(
                        f"Linha {numero} inválida: domínio ou MX vazio"
                    )

                dominio, _ = Domain.objects.get_or_create(
                    domain_name=dominio_nome
                )

                _, criado = ExpectedMX.objects.get_or_create(
                    domain=dominio,
                    exchange=servidor_mx,
                    priority=10,
                )

                if criado:
                    importados += 1
                else:
                    ignorados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {importados} MX esperados adicionados; "
                f"{ignorados} já existiam."
            )
        )
        self.stdout.write(
            f"Total de domínios no banco: {Domain.objects.count()}"
        )
        self.stdout.write(
            f"Total de MX esperados no banco: {ExpectedMX.objects.count()}"
        )
