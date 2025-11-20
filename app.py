from flask import Flask, request, jsonify
import datetime

import gspread
from google.oauth2.service_account import Credentials

# -----------------------
# 1. Google Sheets 연결
# -----------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# service_account.json 파일 경로
CREDS = Credentials.from_service_account_file(
    "service_account.json", scopes=SCOPES
)
gc = gspread.authorize(CREDS)

# 너의 스프레드시트 ID로 바꿔줘!
SPREADSHEET_ID = "1ng7tW1woN5jYo3uW1zkEEgREzTVUjkN3hQyYycnBzRM"
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.sheet1  # 첫 번째 시트 사용

# 한국 시간대 설정
KST = datetime.timezone(datetime.timedelta(hours=9))

# -----------------------
# 2. Flask 앱 설정
# -----------------------
app = Flask(__name__)


@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# POST /song_db/create
@app.route("/song_db/create", methods=["POST"])
def song_create():
    data = request.get_json(force=True)

    title = data.get("title", "")
    scripture = data.get("scripture", "")
    theme = data.get("theme", "")
    language = data.get("language", "")
    mood = data.get("mood", "")
    yt_title = data.get("yt_title", "")

    created_at = datetime.datetime.now(tz=KST).strftime("%Y-%m-%d %H:%M:%S")

    # 시트에 한 줄 추가
    row = [title, scripture, theme, language, mood, yt_title, created_at]
    worksheet.append_row(row)

    # 단순히 ok만 반환해도 됨
    return jsonify({
        "ok": True,
        "title": title,
        "scripture": scripture
    }), 201


# GET /song_db/search?scripture=사도행전 2:42-47&theme=교제
@app.route("/song_db/search", methods=["GET"])
def song_search():
    scripture_query = request.args.get("scripture", "").strip()
    theme_query = request.args.get("theme", "").strip()

    records = worksheet.get_all_records()  # [{...}, {...}, ...]

    results = []
    for row in records:
        match = True

        if scripture_query:
            if scripture_query not in row.get("scripture", ""):
                match = False

        if theme_query:
            if theme_query not in row.get("theme", ""):
                match = False

        if match:
            results.append({
                "title": row.get("title", ""),
                "scripture": row.get("scripture", ""),
                "theme": row.get("theme", ""),
                "language": row.get("language", ""),
                "mood": row.get("mood", ""),
                "yt_title": row.get("yt_title", "")
            })

    return jsonify({"results": results}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
