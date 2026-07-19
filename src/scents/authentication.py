from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication


class TokenAuthentication(BaseTokenAuthentication):
    """TokenAuthentication que nunca devolve 401.

    Uma requisição sem perfil identificado é tratada como visitante (BR-008),
    não como "não autenticada" — por isso a escrita sem permissão deve
    resultar em 403, igual a qualquer outro perfil sem o papel exigido.
    """

    def authenticate_header(self, request):
        return None
