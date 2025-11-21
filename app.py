from flask import Flask, request, jsonify
import os
import json
import logging

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO)

# Google Sheets 설정
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1ng7tW1woN5jYo3uW1zkEEgREzTVUjkN3hQyYycnBzRM"


def get_gspread_client():
    """
    환경변수 GOOGLE_SERVICE_ACCOUNT_JSON 을 읽어서
    gspread Client 를 생성하는 헬퍼 함수.
    문제가 있으면 None 을 리턴하고, 서버는 죽지 않게 함.
    """
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        app.logger.error("환경변수 GOOGLE_SERVICE_ACCOUNT_JSON 이 설정되어 있지 않습니다.")
        return None

    try:
        info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        app.logger.exception("gspread Client 생성 중 오류 발생: %s", e)
        return None


@app.route("/healthz")
def health_check():
    """
    헬스 체크용 엔드포인트.
    구글 인증과 상관없이 항상 동작해야 하므로,
    gspread 는 사용하지 않음.
    """
    return jsonify({"status": "ok"})


@app.route("/write", methods=["POST"])
def write_data():
    """
    예시용 쓰기 API
    Body 예시:
    {
      "name": "홍길동",
      "song": "나는 나비"
    }
    """
    client = get_gspread_client()
    if client is None:
        return jsonify({"error": "Google 인증 설정이 올바르지 않습니다. (GOOGLE_SERVICE_ACCOUNT_JSON 확인 필요)"}), 500

    try:
        data = request.json or {}
        name = data.get("name", "")
        song = data.get("song", "")

        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        sheet.append_row([name, song])

        return jsonify({"message": "Data written successfully", "name": name, "song": song})
    except Exception as e:
        app.logger.exception("시트 쓰기 중 오류: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/read", methods=["GET"])
def read_data():
    """
    예시용 읽기 API
    """
    client = get_gspread_client()
    if client is None:
        return jsonify({"error": "Google 인증 설정이 올바르지 않습니다. (GOOGLE_SERVICE_ACCOUNT_JSON 확인 필요)"}), 500

    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        app.logger.exception("시트 읽기 중 오류: %s", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 로컬에서 테스트할 때만 사용 (Render에서는 gunicorn이 사용)
    app.run(host="0.0.0.0", port=5000, debug=True)
