"""Controller sin dependencias de request: no expone la cookie/JWT."""
class UsersController:
    def greet(self, username: str) -> dict[str, str]:
        return {"hola": username}
