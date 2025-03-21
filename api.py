import os
import json
import requests
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

# 로그 저장을 위한 리스트 (파일 대신 사용)
log_messages = []

def log_message(message):
    """로그 메시지를 리스트에 저장"""
    log_messages.append(message)
    print(message)  # 콘솔에도 출력

# 환경 변수에서 API 키 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
log_message(f"Loaded GEMINI_API_KEY: {GEMINI_API_KEY}")

# FastAPI 앱 생성
app = FastAPI()

@app.get("/")
def home():
    """서버 정상 작동 확인"""
    return {"message": "Gemini Chatbot is Running!"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # 클라이언트에서 보낸 JSON 데이터 받기
        data = await request.json()
        log_message(f"Received data: {json.dumps(data, ensure_ascii=False)}")

        if "userRequest" not in data or "utterance" not in data["userRequest"]:
            log_message("Invalid request format")
            return JSONResponse(content={"error": "Invalid request format"}, status_code=400)

        user_input = data["userRequest"]["utterance"]
        log_message(f"User Input: {user_input}")

        # ✅ Gemini API 호출
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": user_input}]}]
        }

        response = requests.post(api_url, headers=headers, json=payload)
        log_message(f"Gemini API Response: {response.text}")

        # API 응답 확인
        if response.status_code != 200:
            error_message = f"Gemini API Error: {response.status_code} - {response.text}"
            log_message(error_message)
            return JSONResponse(content={"error": error_message}, status_code=response.status_code)

        response_data = response.json()
        bot_reply = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "응답을 생성할 수 없습니다.")

        log_message(f"Gemini Response: {bot_reply}")

        # 카카오 챗봇 응답 형식으로 변환
        kakao_response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": bot_reply
                        }
                    }
                ]
            }
        }

        return JSONResponse(content=kakao_response)

    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        log_message(error_message)
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ 로그 확인 엔드포인트 추가 (log.txt 대신 메모리 내 로그 확인)
@app.get("/logs")
def get_logs():
    """메모리 내 로그 확인하는 엔드포인트"""
    return {"logs": log_messages}
