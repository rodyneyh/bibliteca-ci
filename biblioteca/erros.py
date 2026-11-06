class ErroBiblioteca(Exception):
    """Erro de negócio. A camada HTTP traduz para status + JSON."""

    def __init__(self, status: int, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.codigo = codigo
        self.mensagem = mensagem
