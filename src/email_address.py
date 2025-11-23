class EmailAddress:
    def __init__(self, address: str):
        normalized = self.normalize_address(address)
        if not self._check_correct_email(normalized):
            raise ValueError(f"Некорректный email: {address}")
        self._address = normalized

    @property
    def address(self) -> str:
        return self._address

    @property
    def masked(self) -> str:
        local, domain = self._address.split("@")
        return f"{local[:2]}***@{domain}"

    def normalize_address(self, address: str) -> str:
        return address.lower().strip()

    def _check_correct_email(self, address: str) -> bool:
        return (
            "@" in address
            and (address.endswith(".com") or address.endswith(".ru") or address.endswith(".net"))
        )
