from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
import gspread
import json
import os
import traceback

app = Flask(__name__)

# Google Sheets 인증 스코프
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# --- Google Sheets 연결 함수 ---
def get_sheet():
    """환경변수에 저장된 서비스 계정 JSON으로 인증 후 스프레드시트 열기"""

    try:
        service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    except Exception:
        return None, "GOOGLE_SERVICE_ACCOUNT_JSON 환경변수를 찾을 수 없습니다."

    try:
        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)

        # ⚠️ 사용 중인 스프레드시트 ID 입력
        SPREADSHEET_ID = "1ng7tW1woN5jYo3uW1zkEEgREzTVUjkN3hQyYycnBzRM"

        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        return sheet, None

    except Exception as e:
        return None, str(e)


# --- Health Check ---
@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# --- 곡 저장 API ---
@app.route("/song_db/create", methods=["POST"])
def song_db_create():
    """POST 요청을 받아 Google Sheet에 1줄 추가"""

    sheet, error = get_sheet()
    if error:
        return jsonify({
            "error": "Google 인증 설정이 올바르지 않습니다.",
            "detail": error
        }), 500

    try:
        data = request.get_json()

        required_fields = ["title", "scripture", "theme", "language", "mood", "yt_title"]
        row = [data.get(f, "") for f in required_fields]

        sheet.append_row(row)

        return jsonify({
            "ok": True,
            "title": data.get("title", "")
        }), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "append_error",
            "detail": str(e)
        }), 500


# --- 곡 조회 API (리스트) ---
@app.route("/song_db/list", methods=["GET"])
def song_db_list():
    """Google Sheet에서 저장된 곡 전체 조회"""

    sheet, error = get_sheet()
    if error:
        return jsonify({"error": "Google 인증 실패", "detail": error}), 500

    try:
        rows = sheet.get_all_values()

        if not rows:
            return jsonify({"total": 0, "songs": []}), 200

        header = rows[0]      # 첫 줄: 헤더
        data_rows = rows[1:]  # 나머지: 실제 데이터

        songs = []
        for row in data_rows:
            item = {}
            for i, key in enumerate(header):
                if not key:
                    continue
                item[key] = row[i] if i < len(row) else ""
            songs.append(item)

        # 페이징 쿼리 적용
        limit = request.args.get("limit", default=20, type=int)
        offset = request.args.get("offset", default=0, type=int)

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        sliced = songs[offset:offset + limit]

        return jsonify({
            "total": len(songs),
            "offset": offset,
            "limit": limit,
            "songs": sliced
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "list_error", "detail": str(e)}), 500


# --- Render 서버 실행 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
