import requests, json

APP_ID = "wxcac011f516067da2"
APP_SECRET = "c698684f020aacf968adb76d6c1e29f3"
THUMB = "FUxn_xDBTJiS2XrEbNZVDgNU3hE4z8g50cagHzVC_NoG7xomsC6-K4123asYTvrG"

t = requests.get(f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}").json()["access_token"]

tests = [
    "AI中转站这门生意",
    "AI中转站这门生意，",
    "AI中转站这门生意，为",
    "AI中转站这门生意，为什么",
    "AI中转站这门生意，为什么连",
]
for title in tests:
    p = {"articles": [{"title": title, "content": "<p>ABC</p>", "thumb_media_id": THUMB, "digest": "", "author": ""}]}
    r = requests.post(f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={t}", json=p).json()
    ok = "media_id" in r
    print(f'  {"OK" if ok else "FAIL"} {len(title.encode())}B "{title}"')
