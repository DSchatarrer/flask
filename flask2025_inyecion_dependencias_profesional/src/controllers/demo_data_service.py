# src\controllers\demo_data_service.py

from flask import jsonify, Request

class DemoDataService:
    def __init__(self, session):
        self.session = session
        
    def saludar(self, request: Request):
        token = request.cookies.get("X-Sync.Ref")
        return jsonify({"hola":token})