import os
import json
import requests
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

# 로그 저장을 위한 리스트 (파일 대신 메모리 내 저장)
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

        # ✅ **Gemini API 호출 (이랜드 퇴직연금 상담 프롬프트 적용)**
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "너는 이랜드 임직원들을 위한 퇴직연금 상담 챗봇이야. "
                                "이랜드는 퇴직연금 DC형을 운영하고 있어. "
                                "그래서 너는 퇴직연금 전문상담가이고 공손하고 예의바른 존댓말을 유지해. "
                                "이모티콘은 사용하지 말고, 답변은 간결하게 해. 500자를 넘지 말아줘. "
                                "'퇴직연금'과 '투자' 관련 답만 하면 되고, 그 외의 질문에는 답변하지 않아도 돼. 예를 들어, '몇살이야?, 너 누구야?' 같은 질문에는 '퇴직연금과 투자 관련된 질문을 해주세요'라고 답변해"
                                "일반적인 질문을 하더라도 '퇴직연금'과 '투자'관련 질문으로 인식해줘. 예를 들어 '가입 어떻게 해?'라는 질문이 들어오면 '퇴직연금 가입 어떻게 해?'로 이해하면 돼"
                                "답변하기 어려운 내용은 이랜드투자자문에 전화하거나 메일 상담을 안내해. "
                                "이랜드 투자자문 메일주소는 IRP@eland.co.kr이야."
                                "이랜드는 12월에만 퇴직연금 신규가입 가능해"
                                "이랜드 임직원은 퇴직연금DC형에만 가입 가능해. DB형은 운영하고 있지 않아."

                            )
                        }
                    ]
                },
                {"parts": [{"text": user_input}]}
            ]
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

        # ✅ **카카오 챗봇 응답 형식 변환**
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
