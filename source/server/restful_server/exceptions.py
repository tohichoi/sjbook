class EmptyResultError(LookupError):
    def __init__(self, message="조회 결과가 없습니다. 다른 기간으로 검색해보세요.") -> None:
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        return super().__repr__()