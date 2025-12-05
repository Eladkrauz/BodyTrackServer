from Server.Utilities.Logger import Logger
from Server.Communication.FlaskServer import FlaskServer
from Server.Communication.Communication import Communication
import json

def test_ping():
    server = FlaskServer()
    client = server.app.test_client()

    response = client.get("/ping")

    assert response.status_code == 200
    response:dict = response.json
    print("Opcode:       ", response.get("opcode"))
    print("Message Type: ", "Response" if response.get("message_type") == 2 else "Error")
    print("Title:        ", response.get("title"))
    print("Description:  ", response.get("description"))

def main() -> None:
    Logger.initialize()
    test_ping()

main()