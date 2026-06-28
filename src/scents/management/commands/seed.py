from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from scents.models import Batch, Capsule, MuseumProfile, Reservation


class Command(BaseCommand):
    help = "Popula dados de exemplo para o desafio."

    def handle(self, *args, **options):
        today = timezone.localdate()
        batch, _ = Batch.objects.get_or_create(
            code="CHUVA-1987",
            defaults={
                "preservation_method": "destilação afetiva em vidro âmbar",
                "produced_at": today - timedelta(days=30),
                "expires_at": today + timedelta(days=180),
                "notes": "Lote de demonstração para visitas guiadas.",
            },
        )

        capsule_specs = [
            {
                "name": "Chuva em Paralelepípedo",
                "scent_profile": "ozônio, barro frio e freio de bicicleta",
                "rarity": Capsule.Rarity.RARE,
                "requires_manual_approval": True,
            },
            {
                "name": "Cinema de Bairro às 15h",
                "scent_profile": "pipoca doce, carpete antigo e cortina pesada",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Biblioteca Antes do Ar-condicionado",
                "scent_profile": "papel ácido, madeira encerada e poeira mansa",
                "rarity": Capsule.Rarity.UNIQUE,
                "requires_manual_approval": True,
            },
            # Cheiros da infância brasileira — memórias afetivas pesquisadas
            # (produtos, comidas, escola, casa e rua que quase não existem mais).
            {
                "name": "Leite de Rosas na Pele Depois do Banho",
                "scent_profile": "rosa em pó, glicerina morna e algodão limpo",
                "rarity": Capsule.Rarity.RARE,
            },
            {
                "name": "Talco Johnson's no Trocador",
                "scent_profile": "talco adocicado, camomila e pele de bebê",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Sabonete Granado de Glicerina",
                "scent_profile": "glicerina translúcida, ervas suaves e espuma fina",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Cola Branca Escolar Recém-Aberta",
                "scent_profile": "cola de PVA, plástico novo e dedo de criança",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Giz na Lousa Verde",
                "scent_profile": "pó de giz, ardósia úmida e apagador cansado",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Caderno Novo no Primeiro Dia de Aula",
                "scent_profile": "papel virgem, capa plastificada e tinta de gráfica",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Borracha Cheirosa de Morango",
                "scent_profile": "morango artificial, borracha macia e estojo de lata",
                "rarity": Capsule.Rarity.RARE,
            },
            {
                "name": "Lápis Preto Recém-Apontado",
                "scent_profile": "cedro cru, grafite e raspa de apontador",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Pipoca Estourando na Panela de Sábado",
                "scent_profile": "milho tostado, óleo quente e sal grosso",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Bolo de Chocolate Saindo do Forno",
                "scent_profile": "cacau quente, manteiga e baunilha de caixinha",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Grama Cortada no Fim de Tarde",
                "scent_profile": "clorofila rasgada, terra seca e sol de domingo",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Cera Vermelha no Chão de Ladrilho",
                "scent_profile": "cera de assoalho, pano úmido e domingo de faxina",
                "rarity": Capsule.Rarity.RARE,
                "requires_manual_approval": True,
            },
            {
                "name": "Pizza Caseira com Orégano no Domingo",
                "scent_profile": "orégano tostado, molho de tomate e queijo derretido",
                "rarity": Capsule.Rarity.COMMON,
            },
            {
                "name": "Perfume da Mãe Antes de Sair",
                "scent_profile": "floral empoado, batom e colo aquecido",
                "rarity": Capsule.Rarity.UNIQUE,
                "requires_manual_approval": True,
            },
            {
                "name": "Posto de Gasolina na Viagem de Férias",
                "scent_profile": "gasolina, asfalto quente e salgadinho de saquinho",
                "rarity": Capsule.Rarity.RARE,
                "requires_manual_approval": True,
            },
        ]

        for spec in capsule_specs:
            Capsule.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "batch": batch,
                    "scent_profile": spec["scent_profile"],
                    "origin_story": "Registro criado pela curadoria para o desafio técnico.",
                    "rarity": spec.get("rarity", Capsule.Rarity.COMMON),
                    "requires_manual_approval": spec.get("requires_manual_approval", False),
                    "expires_at": today + timedelta(days=120),
                },
            )

        capsule = Capsule.objects.get(name="Cinema de Bairro às 15h")
        Reservation.objects.get_or_create(
            capsule=capsule,
            visitor_name="Visitante Exemplo",
            status=Reservation.Status.PENDING,
            defaults={
                "starts_at": timezone.now() + timedelta(days=1),
                "pickup_deadline": timezone.now() + timedelta(days=1, hours=2),
            },
        )

        self._seed_profiles()

        self.stdout.write(self.style.SUCCESS("Seed concluído."))

    def _seed_profiles(self):
        user_model = get_user_model()
        people = [
            ("ana.curadoria", "Ana Curadoria", MuseumProfile.Role.CURATOR),
            ("tito.tecnico", "Tito Técnico", MuseumProfile.Role.TECHNICIAN),
            ("vera.visitante", "Vera Visitante", MuseumProfile.Role.VISITOR),
        ]
        for username, display_name, role in people:
            user, _ = user_model.objects.get_or_create(username=username)
            MuseumProfile.objects.get_or_create(
                user=user,
                defaults={"display_name": display_name, "role": role},
            )
