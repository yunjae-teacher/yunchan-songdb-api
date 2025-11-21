import os
import json
import traceback

from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
import gspread

app = Flask(__name__)

# ---- 여기만 네 시트 ID로 맞춰줘! ----
SPREADSHEET_ID = "1ng7tW1woN5jYo3uW1zkEEgREzTVUjkN3hQyYycnBzRM"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    """
    환경변수 GOOGLE_SERVICE_ACCOUNT_JSON 을 읽어서
    gspread worksheet 객체를 돌려주는 함수
    (에러 나면 자세한 설명 포함해서 예외 발생)
    """
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        raise RuntimeError("환경변수 GOOGLE_SERVICE_ACCOUNT_JSON 이 설정되어 있지 않습니다.")

    # JSON 파싱
    try:
        info = json.loads(service_account_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_JSON 값이 올바른 JSON 이 아닙니다: {e}")

    # Credentials 생성
    try:
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    except Exception as e:
        raise RuntimeError(f"Credentials 생성 중 오류: {e}")

    # gspread 클라이언트 생성
    try:
        client = gspread.authorize(creds)
    except Exception as e:
        raise RuntimeError(f"gspread.authorize 중 오류: {e}")

    # 시트 열기
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.sheet1  # 첫 번째 워크시트 사용
    except Exception as e:
        raise RuntimeError(f"스프레드시트(ID={SPREADSHEET_ID}) 열기 오류: {e}")

    return ws


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/song_db/create", methods=["POST"])
def song_db_create():
    """
    예시용 곡 정보 한 줄을 스프레드시트에 추가하는 API
    """
    data = request.get_json(silent=True) or {}

    required = ["title", "scripture", "theme", "language", "mood", "yt_title"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({
            "error": "missing_fields",
            "missing": missing
        }), 400

    try:
        sheet = get_sheet()
        # 필요한 열 순서대로 추가 (원하면 열 순서는 시트 구조에 맞게 조정)
        sheet.append_row([
            data["title"],
            data["scripture"],
            data["theme"],
            data["language"],
            data["mood"],
            data["yt_title"],
        ])
        return jsonify({
            "ok": True,
            "title": data["title"]
        }), 201

    except Exception as e:
        # Render 로그에서 볼 수 있도록 서버 콘솔에 출력
        traceback.print_exc()
        return jsonify({
            "error": "google_error",
            "detail": str(e)
        }), 500


if __name__ == "__main__":
    # 로컬 테스트용
    app.run(host="0.0.0.0", port=5000, debug=True)
