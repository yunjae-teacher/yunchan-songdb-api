from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)

# Google Sheets API 인증 설정
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 환경변수에서 서비스 계정 JSON 가져오기
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)

# 스프레드시트 ID
SPREADSHEET_ID = "1ng7tW1woN5jYo3uW1zkEEgREzTVUjkN3hQyYycnBzRM"


@app.route("/healthz")
def health_check():
    return {"status": "ok"}


@app.route("/write", methods=["POST"])
def write_data():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        sheet = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
        sheet.append_row([data.get("name", ""), data.get("song", "")])

        return jsonify({"message": "Data written successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/read", methods=["GET"])
def read_data():
    try:
        sheet = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
        records = sheet.get_all_records()
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
