from app.errors import AppError
from app.events import agent
from flask import Blueprint, current_app, jsonify, request
from dotenv import load_dotenv

from app.service.agent_service import ServiceAgent
from app.dto.request import GenerateRequest
from app.dto.response import GenerateResponse
load_dotenv()

api = Blueprint("api",__name__)

@api.route("/generate_analysis",methods=["POST"])
async def generate_analysis():
    try:
        data = request.get_json() or {}
        request_object = GenerateRequest.from_dict(data)
        service = ServiceAgent()
        response = await service.generate_result(request_object.user_input)
        response = GenerateResponse(agent_output=response).to_dict()
        return jsonify({"response":response})
    except AppError as e:
        return jsonify({"error":e.code,"message":e.message}), e.http_status 
    except Exception as e:
        print(e)
        return jsonify({"error":"internal_error","message": str(e)}), 500