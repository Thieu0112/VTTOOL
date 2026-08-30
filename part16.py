import html
import requests
import time
import random
import re
import json
import base64
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote, urlencode

# Kiểm tra và import PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[!] Pillow chưa được cài đặt. Cài bằng: pip install Pillow")
    print("[!] Chức năng thêm text vào ảnh sẽ bị vô hiệu hóa")

# ================== ⚙️ CẤU HÌNH DOC_ID ==================
DOC_IDS = {
    "ProfilePlusReauthPasswordStepQuery":    "23900760922861576",
    "ProfilePlusMarkReauthedMutation":       "24066063156313418",
    "useProfilePlusAddPermissionsSearchDataSourceQuery": "9673725249401044",
    "ProfilePlusCoreAppAdminInviteMutation": "26590697433850285",
    "ProfilePlusCometAcceptOrDeclineAdminInviteMutation": "33525122957135374",
    "AdditionalProfilePlusCreationMutation": "23863457623296585",
}

_CACHE_FILE = "fb_docids_cache.json"
if os.path.exists(_CACHE_FILE):
    try:
        _cached = json.loads(open(_CACHE_FILE).read())
        for _k, _v in _cached.items():
            if _v:
                DOC_IDS[_k] = _v
        print(f"[💾] Loaded {len(_cached)} doc_ids từ cache")
    except:
        pass

def save_docid(name, doc_id):
    try:
        existing = {}
        if os.path.exists(_CACHE_FILE):
            existing = json.loads(open(_CACHE_FILE).read())
        existing[name] = doc_id
        DOC_IDS[name] = doc_id
        with open(_CACHE_FILE, "w") as _f:
            json.dump(existing, _f, indent=2)
    except:
        pass


# ================== ⚙️ CÀI ĐẶT (SETTING) ==================
_SETTINGS_FILE = "fb_settings.json"
SETTINGS = {
    "so_luong": 1,
    "delay": 5.0,
    "proxy": "",
    "ten_type": "viet",  # "viet" hoặc "my"
    "keyword_avatar": "gái xinh rõ mặt",
    "keyword_cover": "gái xinh chụp ảnh full người",
}

if os.path.exists(_SETTINGS_FILE):
    try:
        _s = json.loads(open(_SETTINGS_FILE).read())
        if isinstance(_s.get("so_luong"), (int, float)) and _s["so_luong"] >= 1:
            SETTINGS["so_luong"] = int(_s["so_luong"])
        if isinstance(_s.get("delay"), (int, float)) and _s["delay"] >= 0:
            SETTINGS["delay"] = float(_s["delay"])
        if isinstance(_s.get("proxy"), str):
            SETTINGS["proxy"] = _s.get("proxy", "")
        if isinstance(_s.get("ten_type"), str):
            SETTINGS["ten_type"] = _s.get("ten_type", "viet")
        if isinstance(_s.get("keyword_avatar"), str):
            SETTINGS["keyword_avatar"] = _s.get("keyword_avatar", "gái xinh rõ mặt")
        if isinstance(_s.get("keyword_cover"), str):
            SETTINGS["keyword_cover"] = _s.get("keyword_cover", "gái xinh chụp ảnh full người")
        print(f"[💾] Loaded settings: so_luong={SETTINGS['so_luong']} | delay={SETTINGS['delay']}s | ten_type={SETTINGS['ten_type']}")
    except:
        pass

def save_settings():
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as _f:
            json.dump(SETTINGS, _f, indent=2, ensure_ascii=False)
        print(f"[💾] Đã lưu settings → {_SETTINGS_FILE}")
    except Exception as e:
        print(f"[!] Lưu settings lỗi: {e}")

# ================== 🌐 QUẢN LÝ PROXY ==================
_PROXY_FILE = "fb_proxies.txt"

def load_proxies() -> list:
    """Đọc danh sách proxy từ file, mỗi dòng 1 proxy"""
    if not os.path.exists(_PROXY_FILE):
        return []
    try:
        with open(_PROXY_FILE, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except:
        return []

def save_proxies(proxies: list):
    """Lưu danh sách proxy vào file"""
    try:
        with open(_PROXY_FILE, "w", encoding="utf-8") as f:
            for p in proxies:
                f.write(p + "\n")
        print(f"[💾] Đã lưu {len(proxies)} proxy → {_PROXY_FILE}")
    except Exception as e:
        print(f"[!] Lưu proxy lỗi: {e}")

def menu_proxy_manager():
    """Quản lý proxy"""
    while True:
        proxies = load_proxies()
        print("\n" + "=" * 70)
        print("🌐 QUẢN LÝ PROXY")
        print("=" * 70)
        print(f"  Tổng proxy đã lưu: {len(proxies)}")
        if proxies:
            print("-" * 70)
            for i, p in enumerate(proxies, 1):
                display = p[:50] + "..." if len(p) > 50 else p
                print(f"  [{i}] {display}")
            print("-" * 70)
        print("  [A] Thêm proxy (mỗi dòng 1 proxy)")
        print("  [X] Xóa proxy")
        print("  [C] Xóa tất cả")
        print("  [0] Quay lại menu chính")
        print("=" * 70)
        sub = input("👉 Chọn: ").strip().upper()

        if sub == "0" or sub == "":
            break

        elif sub == "A":
            print("👉 Nhập proxy (mỗi dòng 1, định dạng: http://user:pass@ip:port hoặc http://ip:port)")
            print("👉 Nhập xong thì Enter 2 lần để kết thúc:")
            lines = []
            while True:
                line = input().strip()
                if not line and lines:
                    break
                if line:
                    lines.append(line)
            if lines:
                current = load_proxies()
                current.extend(lines)
                current = list(dict.fromkeys(current))
                save_proxies(current)
                print(f"[✅] Đã thêm {len(lines)} proxy")

        elif sub == "X":
            if not proxies:
                print("[!] Danh sách trống")
                continue
            print("  Nhập số thứ tự để xóa (vd: 1 hoặc 1,3,5):")
            raw = input("👉 Xóa: ").strip()
            if not raw:
                continue
            to_remove = set()
            for part in raw.replace(" ", "").split(","):
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(proxies):
                        to_remove.add(proxies[idx - 1])
            new_list = [p for p in proxies if p not in to_remove]
            removed = len(proxies) - len(new_list)
            save_proxies(new_list)
            print(f"[✅] Đã xóa {removed} proxy")

        elif sub == "C":
            confirm = input("⚠️ Xóa TẤT CẢ proxy? (y/n): ").strip().lower()
            if confirm == "y":
                save_proxies([])
                print("[✅] Đã xóa tất cả proxy")
        else:
            print("[!] Lựa chọn không hợp lệ")


class ImageTextOverlay:
    """Thêm text lên ảnh với font Unicode"""
    
    @staticmethod
    def add_text_to_image(image_data: bytes, text: str, position: tuple = (10, 10), 
                          font_size: int = 20, color: tuple = (255, 255, 255)) -> bytes:
        """
        Thêm text vào ảnh và trả về bytes của ảnh mới
        """
        if not PIL_AVAILABLE:
            print("  [⚠️] Pillow chưa được cài đặt, không thể thêm text")
            return image_data
            
        try:
            # Mở ảnh từ bytes
            img = Image.open(io.BytesIO(image_data))
            
            # Tạo đối tượng draw
            draw = ImageDraw.Draw(img)
            
            # Thử tải font Unicode
            font = None
            font_paths = [
                "arial.ttf",
                "Arial.ttf",
                "DejaVuSans.ttf",
                "FreeSans.ttf",
                "Roboto-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:/Windows/Fonts/arial.ttf",
            ]
            
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
            
            # Tính toán kích thước text
            bbox = draw.textbbox(position, text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Vẽ background cho text
            padding = 5
            draw.rectangle(
                [position[0] - padding, position[1] - padding, 
                 position[0] + text_width + padding, position[1] + text_height + padding],
                fill=(0, 0, 0, 180)
            )
            
            # Vẽ text
            draw.text(position, text, fill=color, font=font)
            
            # Chuyển ảnh thành bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            print(f"  [!] Lỗi thêm text vào ảnh: {e}")
            return image_data


def countdown_sleep(seconds: float, label: str = "Job tiếp theo"):
    """Đếm ngược trên cùng 1 dòng trước khi chạy job tiếp theo."""
    if seconds <= 0:
        return
    total = int(seconds)
    frac = seconds - total
    for remaining in range(total, 0, -1):
        mins, secs = divmod(remaining, 60)
        print(f"\r⏳ {label} sau: {mins:02d}:{secs:02d}  ", end="", flush=True)
        time.sleep(1)
    if frac > 0:
        time.sleep(frac)
    print(f"\r✅ Bắt đầu {label}..." + " " * 20)


# ================== 🍪 QUẢN LÝ COOKIE ==================
_COOKIES_FILE = "fb_cookies.json"

def load_cookies() -> list:
    if not os.path.exists(_COOKIES_FILE):
        return []
    try:
        data = json.loads(open(_COOKIES_FILE, encoding="utf-8").read())
        return data if isinstance(data, list) else []
    except:
        return []

def save_cookies(cookies: list):
    try:
        with open(_COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print(f"[💾] Đã lưu {len(cookies)} cookie → {_COOKIES_FILE}")
    except Exception as e:
        print(f"[!] Lưu cookie lỗi: {e}")

def extract_uid_from_cookie(cookie: str) -> str:
    m = re.search(r'c_user=(\d+)', cookie)
    return m.group(1) if m else ""

def menu_cookie_manager():
    """Mục [5] - Thêm / Xóa / Xem danh sách cookie + UID."""
    while True:
        cookies = load_cookies()
        print("\n" + "=" * 70)
        print("🍪 QUẢN LÝ COOKIE")
        print("=" * 70)
        print(f"  Tổng cookie đã lưu: {len(cookies)}")
        if cookies:
            print("-" * 70)
            for i, c in enumerate(cookies, 1):
                uid = c.get("uid", "?")
                name = c.get("name", "")
                note = c.get("note", "")
                print(f"  [{i}] UID: {uid}  |  {name or '(chưa check)'}  {('— ' + note) if note else ''}")
            print("-" * 70)
        print("  [A] Thêm cookie")
        print("  [X] Xóa cookie")
        print("  [L] Danh sách UID (chi tiết)")
        print("  [C] Check nhanh tất cả cookie (lấy tên + trạng thái)")
        print("  [0] Quay lại menu chính")
        print("=" * 70)
        sub = input("👉 Chọn: ").strip().upper()

        if sub == "0" or sub == "":
            break

        elif sub == "A":
            raw = input("👉 Dán cookie (có c_user): ").strip()
            if not raw:
                print("[!] Cookie trống")
                continue
            uid = extract_uid_from_cookie(raw)
            if not uid:
                print("[!] Cookie không có c_user!")
                continue
            if any(c.get("uid") == uid for c in cookies):
                print(f"[!] UID {uid} đã có trong danh sách — bỏ qua")
                continue
            note = input("👉 Ghi chú (Enter bỏ qua): ").strip()
            cookies.append({"uid": uid, "cookie": raw, "name": "", "note": note, "live": None})
            save_cookies(cookies)
            print(f"[✅] Đã thêm UID {uid}")

        elif sub == "X":
            if not cookies:
                print("[!] Danh sách trống")
                continue
            print("  Nhập số thứ tự để xóa (vd: 1 hoặc 1,3,5) — hoặc UID:")
            raw = input("👉 Xóa: ").strip()
            if not raw:
                continue
            to_remove = set()
            for part in raw.replace(" ", "").split(","):
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(cookies):
                        to_remove.add(cookies[idx - 1]["uid"])
                    else:
                        to_remove.add(part)
                else:
                    to_remove.add(part)
            new_list = [c for c in cookies if c.get("uid") not in to_remove]
            removed = len(cookies) - len(new_list)
            save_cookies(new_list)
            print(f"[✅] Đã xóa {removed} cookie")

        elif sub == "L":
            if not cookies:
                print("[!] Danh sách trống")
                continue
            print("\n" + "=" * 70)
            print("📋 DANH SÁCH UID")
            print("=" * 70)
            for i, c in enumerate(cookies, 1):
                live = c.get("live")
                status = "✅ LIVE" if live is True else ("❌ DIE" if live is False else "⚪ chưa check")
                print(f"  [{i}] UID: {c.get('uid')}")
                print(f"       Tên : {c.get('name') or '(chưa có)'}")
                print(f"       Note: {c.get('note') or '-'}")
                print(f"       TT  : {status}")
                print("-" * 40)
            try:
                with open("uids.txt", "w", encoding="utf-8") as f:
                    f.write(f"Tổng: {len(cookies)} UID\n")
                    f.write("=" * 50 + "\n")
                    for c in cookies:
                        f.write(f"{c.get('uid')}|{c.get('name','')}|{c.get('note','')}\n")
                print("💾 Đã xuất uids.txt")
            except:
                pass

        elif sub == "C":
            if not cookies:
                print("[!] Danh sách trống")
                continue
            
            proxy = SETTINGS.get("proxy", "")
            
            print(f"\n[🔍] Check {len(cookies)} cookie... (proxy: {proxy[:30] if proxy else 'None'})")
            for i, c in enumerate(cookies, 1):
                uid = c.get("uid", "?")
                print(f"\n  [{i}/{len(cookies)}] UID {uid}...")
                try:
                    sess = FacebookSession(c["cookie"], proxy=proxy if proxy else None)
                    if not sess.extract_uid():
                        c["live"] = False
                        c["name"] = ""
                        print(f"      ❌ Không có c_user")
                        continue
                    ok = sess.check_cookie()
                    c["live"] = bool(ok)
                    c["name"] = sess.name or ""
                    if ok:
                        print(f"      ✅ LIVE — {c['name']}")
                    else:
                        print(f"      ❌ DIE / Checkpoint")
                except Exception as e:
                    c["live"] = False
                    print(f"      ❌ Lỗi: {e}")
                time.sleep(1)
            save_cookies(cookies)
            live_n = sum(1 for c in cookies if c.get("live") is True)
            die_n = sum(1 for c in cookies if c.get("live") is False)
            print(f"\n[📊] Kết quả: LIVE={live_n} | DIE={die_n} | Tổng={len(cookies)}")
            try:
                with open("uids.txt", "w", encoding="utf-8") as f:
                    f.write(f"Tổng: {len(cookies)} | LIVE: {live_n} | DIE: {die_n}\n")
                    f.write("=" * 50 + "\n")
                    for c in cookies:
                        st = "LIVE" if c.get("live") is True else ("DIE" if c.get("live") is False else "?")
                        f.write(f"{c.get('uid')}|{c.get('name','')}|{st}|{c.get('note','')}\n")
                print("💾 Đã cập nhật uids.txt")
            except:
                pass
        else:
            print("[!] Lựa chọn không hợp lệ")


class AdvancedCookieEncryption:
    @staticmethod
    def encrypt_full(data: str) -> str:
        encrypted = base64.b64encode(data.encode()).decode()
        encrypted = encrypted[::-1]
        encrypted = hashlib.sha256(encrypted.encode()).hexdigest()
        return encrypted

    @staticmethod
    def get_secure_display(data: str) -> str:
        return AdvancedCookieEncryption.encrypt_full(data)[:30] + "..."


class PinterestImageFetcher:
    """Tìm ảnh gái xinh từ nhiều nguồn: Pinterest, Google Images scrape."""

    AVATAR_KEYWORDS = [
    ]
    COVER_KEYWORDS = [
    ]

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    @staticmethod
    def _search_bing_images(keyword: str, proxy: str = None) -> list:
        try:
            url = "https://www.bing.com/images/search"
            params = {"q": keyword, "form": "HDRSC2"}
            headers = {
                **PinterestImageFetcher.HEADERS,
                "Referer": "https://www.bing.com/images/",
            }
            
            proxies = None
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
            
            resp = requests.get(url, params=params, headers=headers, timeout=20, proxies=proxies)
            if resp.status_code != 200:
                return []

            urls = []
            for m in re.finditer(r'&quot;murl&quot;:&quot;(.*?)&quot;', resp.text):
                u = html.unescape(m.group(1)).replace("\\/", "/")
                if u.startswith("http"):
                    urls.append(u)

            if not urls:
                for m in re.finditer(r'"murl":"(https?://[^"]+)"', resp.text):
                    u = m.group(1).replace("\\/", "/")
                    if u.startswith("http"):
                        urls.append(u)

            seen = set()
            return [u for u in urls if not (u in seen or seen.add(u))][:50]
        except Exception as e:
            print(f"   [!] Bing Images lỗi: {e}")
            return []

    @staticmethod
    def _search_google_images(keyword: str, proxy: str = None) -> list:
        try:
            url = (
                "https://www.google.com/search"
                f"?q={quote(keyword)}&tbm=isch&tbs=isz:m"
            )
            
            proxies = None
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
            
            resp = requests.get(
                url,
                headers=PinterestImageFetcher.HEADERS,
                timeout=20,
                proxies=proxies
            )
            if resp.status_code != 200:
                return []

            candidates = re.findall(
                r'https?://[^\s"<>\\]+',
                html.unescape(resp.text)
            )

            seen = set()
            urls = []
            for u in candidates:
                u = u.replace("\\/", "/")
                if (
                    u.startswith("http")
                    and "gstatic" not in u
                    and "google." not in u
                    and len(u) < 1000
                    and u not in seen
                ):
                    seen.add(u)
                    urls.append(u)
            return urls[:30]
        except Exception as e:
            print(f"   [!] Google Images lỗi: {e}")
            return []

    @staticmethod
    def _download_url(img_url: str, min_size: int = 30000, proxy: str = None) -> Optional[bytes]:
        try:
            headers = {
                **PinterestImageFetcher.HEADERS,
                'Referer': 'https://www.pinterest.com/',
            }
            
            proxies = None
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
            
            resp = requests.get(img_url, headers=headers, timeout=20, allow_redirects=True, proxies=proxies)
            if resp.status_code == 200 and len(resp.content) >= min_size:
                ct = resp.headers.get('content-type', '')
                if 'image' in ct or img_url.endswith(('.jpg', '.jpeg', '.png')):
                    return resp.content
        except:
            pass
        return None

    _used_urls: set = set()

    @staticmethod
    def reset_used():
        PinterestImageFetcher._used_urls = set()

    @staticmethod
    def fetch_image(keywords: list, label: str = "ảnh", proxy: str = None) -> Optional[bytes]:
        import urllib.parse

        kws = list(keywords)
        random.shuffle(kws)
        all_urls = []

        print("   [→] Tìm Bing Images...")
        for keyword in kws[:4]:
            print(f"   [🔍] Tìm Bing: '{keyword}'...")
            urls = PinterestImageFetcher._search_bing_images(keyword, proxy=proxy)
            all_urls.extend((keyword, u) for u in urls)

        if not all_urls:
            print("   [→] Bing không có kết quả — thử Google Images...")
            for keyword in kws[:4]:
                print(f"   [🔍] Tìm Google: '{keyword}'...")
                urls = PinterestImageFetcher._search_google_images(keyword, proxy=proxy)
                all_urls.extend((keyword, u) for u in urls)

        BAD_WORDS = {
            "cat", "cats", "kitten", "kitty", "meow",
            "dog", "puppy", "animal", "pet",
            "car", "landscape", "wallpaper", "logo",
            "flower", "food", "meme", "anime",
        }

        GOOD_WORDS = {
            "girl", "woman", "female", "portrait",
            "selfie", "face", "beauty", "model",
            "asian", "vietnamese", "korean",
        }

        def score(item):
            keyword, url = item
            low = (keyword + " " + urllib.parse.unquote(url)).lower()

            if any(w in low for w in BAD_WORDS):
                return -10000

            s = sum(3 for w in GOOD_WORDS if w in low)
            if any(ext in low for ext in (".jpg", ".jpeg", ".png", ".webp")):
                s += 1
            return s

        candidates = []
        seen = set()
        for keyword, url in all_urls:
            if not url or url in seen or url in PinterestImageFetcher._used_urls:
                continue
            seen.add(url)
            candidates.append((score((keyword, url)), keyword, url))

        candidates = [x for x in candidates if x[0] >= 0]
        candidates.sort(key=lambda x: x[0], reverse=True)

        print(f"   [→] Tổng {len(all_urls)} URL, {len(candidates)} URL đã lọc")

        for _, keyword, url in candidates[:30]:
            data = PinterestImageFetcher._download_url(url, proxy=proxy)
            if not data or len(data) < 5 * 1024:
                continue

            PinterestImageFetcher._used_urls.add(url)
            print(f"   [✓] {label} OK ({len(data)/1024:.1f} KB)")
            return data

        print(f"   [⚠️] Không tìm được {label} phù hợp — bỏ qua upload")
        return None


class SmartImageHandler:
    @staticmethod
    def get_avatar(proxy: str = None) -> Optional[bytes]:
        keyword = SETTINGS.get("keyword_avatar", "gái xinh rõ mặt")
        print(f"   [🔍] Đang tải Avatar với từ khóa: '{keyword}'...")
        data = PinterestImageFetcher.fetch_image(
            [keyword] + PinterestImageFetcher.AVATAR_KEYWORDS, 
            "Avatar nữ", 
            proxy=proxy
        )
        if data:
            print(f"   [✓] Avatar nữ OK ({len(data)/1024:.1f} KB)")
        return data

    @staticmethod
    def get_cover(proxy: str = None) -> Optional[bytes]:
        keyword = SETTINGS.get("keyword_cover", "gái xinh chụp ảnh full người")
        print(f"   [🔍] Đang tải Ảnh bìa với từ khóa: '{keyword}'...")
        data = PinterestImageFetcher.fetch_image(
            [keyword] + PinterestImageFetcher.COVER_KEYWORDS,
            "Ảnh bìa", 
            proxy=proxy
        )
        if data:
            print(f"   [✓] Ảnh bìa OK ({len(data)/1024:.1f} KB)")
        return data


class ContentGenerator:
    HO_VIET = [
        "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan",
        "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương",
        "Lý", "Đinh", "Mai", "Tạ", "Đoàn"
    ]

    TEN_DEM_NAM = [
        "Văn", "Hữu", "Đức", "Quang", "Minh", "Thành", "Thanh",
        "Anh", "Gia", "Hoàng", "Bảo", "Đình", "Xuân", "Nhật",
        "Khánh", "Trọng", "Tuấn", "Đăng"
    ]

    TEN_NAM = [
        "Anh", "Bình", "Cường", "Dũng", "Đạt", "Hải", "Hiếu",
        "Hùng", "Khang", "Khánh", "Long", "Minh", "Nam", "Phong",
        "Phúc", "Quân", "Quang", "Sơn", "Thành", "Thắng", "Tuấn",
        "Tùng", "Việt", "Vinh", "Duy", "Huy", "Đức", "Tài"
    ]

    TEN_DEM_NU = [
        "Thị", "Ngọc", "Thu", "Thanh", "Minh", "Bảo", "Khánh",
        "Phương", "Quỳnh", "Diễm", "Tuyết", "Mai", "Kim", "Hồng",
        "Như", "Ánh", "Trúc", "Yến"
    ]

    TEN_NU = [
        "Anh", "An", "Chi", "Dung", "Giang", "Hà", "Hân", "Hoa",
        "Hương", "Lan", "Linh", "Mai", "My", "Ngân", "Nga", "Ngọc",
        "Nhi", "Nhung", "Oanh", "Phương", "Quỳnh", "Thảo", "Trang",
        "Trâm", "Uyên", "Vy", "Yến", "Ly"
    ]

    # Tên Mỹ
    FIRST_NAMES_US = [
        "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
        "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
        "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian",
        "George", "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob",
        "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott",
        "Brandon", "Benjamin", "Samuel", "Raymond", "Gregory", "Frank", "Alexander",
        "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Nathan",
        "Adam", "Henry", "Zachary", "Todd", "Walter", "Kyle", "Ethan", "Noah", "Liam",
        "Mason", "Logan", "Oliver", "Elijah", "Carter", "Grayson", "Hunter", "Cameron",
        "Connor", "Evan", "Dylan", "Austin", "Jordan", "Cooper", "Reed", "Parker"
    ]
    
    LAST_NAMES_US = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
        "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
        "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
        "Carter", "Roberts", "Turner", "Phillips", "Evans", "Collins", "Edwards",
        "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Morgan", "Peterson", "Cooper",
        "Reed", "Bailey", "Bell", "Howard", "Ward", "Cox", "Diaz", "Richardson",
        "Wood", "Watson", "Brooks", "Bennett", "Gray", "James", "Reyes", "Cruz"
    ]

    BIOS = [
        "✨ Tạo bởi Trần Viết Thiệu ✨",
    ]

    @staticmethod
    def generate_viet_name() -> Tuple[str, str]:
        ho = random.choice(ContentGenerator.HO_VIET)
        if random.choice([True, False]):
            ten_dem = random.choice(ContentGenerator.TEN_DEM_NAM)
            ten = random.choice(ContentGenerator.TEN_NAM)
        else:
            ten_dem = random.choice(ContentGenerator.TEN_DEM_NU)
            ten = random.choice(ContentGenerator.TEN_NU)
        return f"{ho} {ten_dem} {ten}", random.choice(ContentGenerator.BIOS)
    
    @staticmethod
    def generate_us_name() -> Tuple[str, str]:
        first = random.choice(ContentGenerator.FIRST_NAMES_US)
        last = random.choice(ContentGenerator.LAST_NAMES_US)
        return f"{first} {last}", random.choice(ContentGenerator.BIOS)

    @staticmethod
    def generate() -> Tuple[str, str]:
        if SETTINGS.get("ten_type", "viet") == "my":
            return ContentGenerator.generate_us_name()
        return ContentGenerator.generate_viet_name()


class FacebookSession:
    def __init__(self, cookie: str, proxy: str = None):
        self.cookie = cookie
        self.uid = None
        self.name = None
        self.fb_dtsg = None
        self.lsd = None
        self.jazoest = None
        self.rev = None
        self.proxy = proxy

        self.session = requests.Session()
        
        if proxy:
            proxy_dict = {
                'http': proxy,
                'https': proxy,
            }
            self.session.proxies.update(proxy_dict)
            print(f"[🌐] Dùng proxy: {proxy[:50]}...")

        self.session.headers.update({
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'viewport-width': '1920',
        })

        cookie_dict = {}
        for item in cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key] = value

        for key, value in cookie_dict.items():
            self.session.cookies.set(key, value, domain='.facebook.com')

    def extract_uid(self) -> bool:
        match = re.search(r'c_user=(\d+)', self.cookie)
        if match:
            self.uid = match.group(1)
            print(f"[✓] UID: {self.uid}")
            return True
        return False

    def check_cookie(self) -> bool:
        try:
            print("\n[🔍] Kiểm tra cookie...")
            url = f"https://mbasic.facebook.com/"
            response = self.session.get(url, timeout=20, allow_redirects=False)

            if response.status_code in [301, 302]:
                location = response.headers.get('Location', '')
                if 'login' in location.lower():
                    print("[❌] Cookie DIE")
                    return False
                if 'checkpoint' in location.lower():
                    print("[❌] Checkpoint")
                    return False

            html = response.text

            if 'login' in html.lower()[:1000]:
                print("[❌] Cookie DIE")
                return False

            if 'checkpoint' in html.lower():
                print("[❌] Checkpoint")
                return False

            name_match = re.search(r'<title>(.*?)</title>', html)
            if name_match:
                self.name = name_match.group(1).strip()
                print(f"[✓] Tên: {self.name}")

            print("[✅] Cookie LIVE")
            return True

        except Exception as e:
            print(f"[!] Lỗi check: {e}")
            return False

    def get_tokens(self) -> bool:
        try:
            print("\n[⚡] Đang lấy token...")
            url = "https://www.facebook.com/"
            print("[→] Truy cập facebook.com...")
            response = self.session.get(url, timeout=30)

            if response.status_code != 200:
                print(f"[!] Status code: {response.status_code}")
                return False

            html = response.text
            print(f"[→] Nhận HTML: {len(html)} bytes")

            print("[→] Tìm fb_dtsg...")
            dtsg_patterns = [
                r'"DTSGInitialData".*?"token":"([^"]+)"',
                r'"dtsg":.*?"token":"([^"]+)"',
                r'name="fb_dtsg" value="([^"]+)"',
                r'\["DTSGInitialData",\[\],\{.*?"token":"([^"]+)"',
            ]

            for i, pattern in enumerate(dtsg_patterns):
                matches = re.findall(pattern, html)
                if matches:
                    self.fb_dtsg = matches[0]
                    print(f"[✓] fb_dtsg (pattern {i+1}): {self.fb_dtsg[:30]}...")
                    break

            print("[→] Tìm lsd...")
            lsd_patterns = [
                r'"LSDToken".*?"token":"([^"]+)"',
                r'name="lsd" value="([^"]+)"',
                r'"lsd":"([^"]+)"',
            ]

            for i, pattern in enumerate(lsd_patterns):
                matches = re.findall(pattern, html)
                if matches:
                    self.lsd = matches[0]
                    print(f"[✓] lsd (pattern {i+1}): {self.lsd[:30]}...")
                    break

            print("[→] Tìm rev và spin_r...")
            spin_match = re.search(r'"__spin_r":(\d+)', html)
            if spin_match:
                self.rev = spin_match.group(1)
                print(f"[✓] spin_r/rev: {self.rev}")

            print("[→] Tìm client_revision...")
            rev_match = re.search(r'"client_revision":(\d+)', html)
            if rev_match:
                self.rev = rev_match.group(1)
                print(f"[✓] rev: {self.rev}")

            if not self.lsd and self.fb_dtsg:
                self.lsd = self.fb_dtsg
                print("[→] Dùng fb_dtsg làm lsd")

            if self.fb_dtsg:
                self.jazoest = self._calc_jazoest(self.fb_dtsg)
                print(f"[✓] jazoest (từ fb_dtsg): {self.jazoest}")

            if not self.rev:
                self.rev = "1017800000"
                print(f"[→] Rev dự phòng: {self.rev}")

            if self.fb_dtsg:
                print("[✅] Lấy token THÀNH CÔNG")
                return True
            else:
                print("[❌] Không tìm thấy fb_dtsg")
                return False

        except Exception as e:
            print(f"[❌] Lỗi: {e}")
            return False

    def _calc_jazoest(self, dtsg: str) -> str:
        return "2" + str(sum(ord(c) for c in dtsg))

    def _auto_find_docid(self, mutation_name: str, page_id: str = None) -> Optional[str]:
        print(f"  [🔍] Đang tự tìm doc_id mới cho {mutation_name}...")

        def _extract_scripts(html):
            urls = re.findall(
                r'"(https://static\.xx\.fbcdn\.net/rsrc\.php/[^"]+\.js(?:\?[^"]*)?)"',
                html
            )
            return list(dict.fromkeys(urls))

        def _search_in_js(js, name):
            m = re.search(
                rf'\{{id:"(\d{{10,}})"[^}}]{{0,200}}name:"{re.escape(name)}"',
                js
            )
            if m: return m.group(1)

            m = re.search(
                rf'name:"{re.escape(name)}"[^}}]{{0,200}}\{{?id:"(\d{{10,}})"',
                js
            )
            if m: return m.group(1)

            m = re.search(
                rf'"{re.escape(name)}"\s*,\s*"(\d{{10,}})"',
                js
            )
            if m: return m.group(1)

            m = re.search(
                rf'"(\d{{10,}})"\s*,\s*"{re.escape(name)}"',
                js
            )
            if m: return m.group(1)

            idx = js.find(name)
            while idx != -1:
                chunk_start = max(0, idx - 500)
                chunk_end   = min(len(js), idx + 500)
                chunk = js[chunk_start:chunk_end]
                for pat in [
                    r'"id"\s*:\s*"(\d{10,})"',
                    r'\bid\s*:\s*"(\d{10,})"',
                    r'docID\s*:\s*"(\d{10,})"',
                    r'doc_id\s*:\s*"(\d{10,})"',
                ]:
                    cm = re.search(pat, chunk)
                    if cm:
                        return cm.group(1)
                idx = js.find(name, idx + 1)

            return None

        try:
            all_script_urls = []

            if page_id:
                clean = re.sub(r';\s*i_user=[^;]+', '', self.cookie).strip()
                page_cookie = clean + f'; i_user={page_id}'
                tmp = requests.Session()
                tmp.headers.update(self.session.headers)
                if self.proxy:
                    tmp.proxies.update({'http': self.proxy, 'https': self.proxy})
                for item in page_cookie.split(';'):
                    item = item.strip()
                    if '=' in item:
                        k, v = item.split('=', 1)
                        tmp.cookies.set(k.strip(), v.strip(), domain='.facebook.com')
                for url in [
                    f'https://www.facebook.com/{page_id}/settings/?tab=access',
                    f'https://www.facebook.com/{page_id}/settings/',
                ]:
                    try:
                        r = tmp.get(url, timeout=20)
                        all_script_urls += _extract_scripts(r.text)
                    except:
                        pass

            for url in [
                'https://www.facebook.com/pages/?category=your_pages',
                'https://www.facebook.com/',
            ]:
                try:
                    r = self.session.get(url, timeout=20)
                    all_script_urls += _extract_scripts(r.text)
                except:
                    pass

            all_script_urls = list(dict.fromkeys(all_script_urls))
            print(f"  [→] Tìm trong {len(all_script_urls)} JS bundles...")

            for url in all_script_urls[:30]:
                try:
                    sr = self.session.get(url, timeout=15)
                    if len(sr.text) < 5000:
                        continue
                    found = _search_in_js(sr.text, mutation_name)
                    if found:
                        print(f"  [✅] Tìm được doc_id mới: {found}")
                        save_docid(mutation_name, found)
                        return found
                except:
                    continue

        except Exception as e:
            print(f"  [!] _auto_find_docid lỗi: {e}")

        print(f"  [⚠️] Không tự tìm được doc_id — anh cần lấy thủ công qua DevTools")
        return None

    def _get_page_context_token(self, page_id: str):
        try:
            clean = re.sub(r';\s*i_user=[^;]+', '', self.cookie).strip()
            page_cookie = clean + f'; i_user={page_id}'

            tmp = requests.Session()
            tmp.headers.update(self.session.headers)
            if self.proxy:
                tmp.proxies.update({'http': self.proxy, 'https': self.proxy})
            for item in page_cookie.split(';'):
                item = item.strip()
                if '=' in item:
                    k, v = item.split('=', 1)
                    tmp.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

            for url in [
                f'https://www.facebook.com/{page_id}/settings/?tab=access',
                f'https://www.facebook.com/{page_id}/settings/',
                f'https://www.facebook.com/{page_id}',
            ]:
                try:
                    r = tmp.get(url, timeout=20)
                    html = r.text
                    dtsg = None
                    for pat in [
                        r'"DTSGInitialData".*?"token":"([^"]+)"',
                        r'name="fb_dtsg"[^>]*value="([^"]+)"',
                        r'"fb_dtsg":\{"token":"([^"]+)"',
                        r'"dtsg":\{"token":"([^"]+)"',
                    ]:
                        m = re.search(pat, html)
                        if m:
                            dtsg = m.group(1)
                            break
                    lsd = None
                    for pat in [r'"LSDToken".*?"token":"([^"]+)"', r'name="lsd"[^>]*value="([^"]+)"']:
                        m = re.search(pat, html)
                        if m:
                            lsd = m.group(1)
                            break
                    if dtsg:
                        jazoest = self._calc_jazoest(dtsg)
                        if not lsd:
                            lsd = dtsg
                        print(f"  [✓] Page context token: dtsg={dtsg[:20]}... lsd={lsd[:15]}...")
                        return dtsg, lsd, jazoest, tmp
                except:
                    continue
        except Exception as e:
            print(f"  [!] _get_page_context_token error: {e}")
        return None, None, None, None

    def _reauth_password(self, page_id: str, password: str, dtsg: str, lsd: str, jazoest: str,
                         page_session=None) -> bool:
        sess = page_session or self.session
        CRN = "comet.genericcometdonotuse.CometProfilePlusProfessionalDashboardAdminPermissionsRoute"
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.facebook.com",
            "referer": f"https://www.facebook.com/{page_id}/settings/?tab=access",
            "x-fb-lsd": lsd,
        }

        base_data = {
            "av": self.uid, "__aaid": "0", "__user": self.uid,
            "__a": "1", "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
            "dpr": "3", "__ccg": "EXCELLENT", "__rev": self.rev,
            "__comet_req": "1", "__crn": CRN,
            "fb_dtsg": dtsg, "jazoest": jazoest, "lsd": lsd,
            "__spin_r": self.rev, "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "fb_api_caller_class": "RelayModern",
            "server_timestamps": "true",
        }

        try:
            data_q = {**base_data, "__req": "s",
                      "fb_api_req_friendly_name": "ProfilePlusReauthPasswordStepQuery",
                      "variables": "{}",
                      "doc_id": DOC_IDS["ProfilePlusReauthPasswordStepQuery"]}
            r = sess.post("https://www.facebook.com/api/graphql/", data=data_q, headers=headers, timeout=20)
            rtext = r.text
            if rtext.startswith("for (;;);"): rtext = rtext[9:]
            print(f"  [→] ReauthQuery status: {r.status_code} | resp: {rtext[:200]}")
        except Exception as e:
            print(f"  [!] ReauthQuery error: {e}")
        time.sleep(1)

        def _do_submit(variables):
            data = {**base_data, "__req": "t",
                    "fb_api_req_friendly_name": "ProfilePlusMarkReauthedMutation",
                    "variables": json.dumps(variables),
                    "doc_id": DOC_IDS["ProfilePlusMarkReauthedMutation"]}
            resp = sess.post("https://www.facebook.com/api/graphql/", data=data, headers=headers, timeout=30)
            text = resp.text
            if text.startswith("for (;;);"): text = text[9:]
            print(f"  [→] Reauth submit status: {resp.status_code}")
            print(f"  [→] Reauth response FULL: {text[:500]}")
            try:
                result = json.loads(text)
                if result.get("__ar"):
                    err_code = result.get("error", "")
                    err_sum = result.get("errorSummary", "")
                    print(f"  [!] Reauth AR {err_code}: {err_sum}")
                    return False, f"ar_{err_code}"
                if result.get("errors"):
                    err = result["errors"][0].get("message", "")
                    code = result["errors"][0].get("code", "")
                    print(f"  [!] Reauth lỗi ({code}): {err}")
                    return False, err
                if result.get("data") is not None:
                    return True, None
                return False, "no data"
            except Exception as e:
                return False, str(e)

        if password:
            print("  [→] Thử reauth với password (format PWD_BROWSER:5)...")
            ts = str(int(time.time()))
            pwd_encoded = f"#PWD_BROWSER:5:{ts}:{password}"
            ok, err = _do_submit({
                "input": {
                    "password": {"sensitive_string_value": pwd_encoded},
                    "actor_id": page_id,
                    "client_mutation_id": "2"
                }
            })
            if ok:
                print("  [✓] Reauth thành công!")
                return True

            print("  [→] Thử reauth format PWD_BROWSER:0...")
            pwd_encoded0 = f"#PWD_BROWSER:0:{ts}:{password}"
            ok, err = _do_submit({
                "input": {
                    "password": {"sensitive_string_value": pwd_encoded0},
                    "actor_id": page_id,
                    "client_mutation_id": "2"
                }
            })
            if ok:
                print("  [✓] Reauth thành công (format 0)!")
                return True

            if err and ("incorrect" in str(err).lower() or "password" in str(err).lower()):
                print("  [❌] Mật khẩu sai!")
                return False

        print("  [!] Reauth thất bại — thử tiếp invite dù sao")
        return False

    def _search_user_for_invite(self, page_id: str, admin_uid: str, dtsg: str, lsd: str,
                                jazoest: str, page_session=None) -> bool:
        sess = page_session or self.session
        try:
            variables = {"search_term": ""}
            data = {
                "av": page_id, "__aaid": "0",
                "__user": page_id,
                "__a": "1", "__req": "q",
                "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
                "dpr": "3", "__ccg": "EXCELLENT", "__rev": self.rev,
                "__comet_req": "1",
                "fb_dtsg": dtsg, "jazoest": jazoest, "lsd": lsd,
                "__spin_r": self.rev, "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useProfilePlusAddPermissionsSearchDataSourceQuery",
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": DOC_IDS["useProfilePlusAddPermissionsSearchDataSourceQuery"]
            }
            sess.post(
                "https://www.facebook.com/api/graphql/",
                data=data,
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.facebook.com",
                    "referer": f"https://www.facebook.com/{page_id}/settings/?tab=access",
                    "x-fb-lsd": lsd,
                },
                timeout=20
            )
            time.sleep(0.5)

            variables2 = {"search_term": admin_uid}
            data["variables"] = json.dumps(variables2)
            data["__req"] = "r"
            resp2 = sess.post(
                "https://www.facebook.com/api/graphql/",
                data=data,
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.facebook.com",
                    "referer": f"https://www.facebook.com/{page_id}/settings/?tab=access",
                    "x-fb-lsd": lsd,
                },
                timeout=20
            )
            text = resp2.text
            if text.startswith("for (;;);"): text = text[9:]
            print(f"  [→] Search user response: {text[:150]}")
            return True
        except Exception as e:
            print(f"  [!] Search user error: {e}")
            return False

    def _cancel_existing_invite(self, page_id: str, admin_uid: str, dtsg: str, lsd: str,
                                 jazoest: str, page_session=None) -> bool:
        sess = page_session or self.session
        import re as _re
        invite_ids = []
        biz_ids = []

        try:
            clean_cookie = re.sub(r';\s*i_user=[^;]+', '', self.cookie).strip()
            page_cookie = clean_cookie + f'; i_user={page_id}'
            headers_html = {**dict(sess.headers), 'cookie': page_cookie}
            r = sess.get(
                f'https://www.facebook.com/{page_id}/settings/?tab=access',
                headers=headers_html, timeout=20)
            html = r.text
            print(f"  [→] Settings HTML size: {len(html)}")

            invite_ids = _re.findall(r'"profile_admin_invite_id"\s*:\s*"(\d+)"', html)
            biz_ids = _re.findall(r'"profile_with_biz_tools_id"\s*:\s*"(\d+)"', html)
            print(f"  [→] Found invite_ids: {invite_ids}, biz_ids: {biz_ids[:3]}")
        except Exception as e:
            print(f"  [!] Fetch settings lỗi: {e}")

        if not invite_ids:
            print(f"  [→] Không có invite cũ pending")
            return True

        for inv_id in invite_ids:
            print(f"  [→] Cancel invite cũ: {inv_id}")
            biz_id = biz_ids[0] if biz_ids else page_id
            cancel_vars = json.dumps({
                "input": {
                    "profile_admin_invite_id": inv_id,
                    "profile_with_biz_tools_id": biz_id,
                    "client_mutation_id": "1"
                },
                "scale": 3
            })
            cancel_data = {
                "av": page_id, "__user": page_id, "__a": "1", "__req": "q",
                "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
                "dpr": "3", "__ccg": "EXCELLENT", "__rev": self.rev,
                "__comet_req": "1", "fb_dtsg": dtsg, "jazoest": jazoest,
                "lsd": lsd, "__spin_r": self.rev, "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "ProfilePlusCancelAdminInviteMutation",
                "variables": cancel_vars, "server_timestamps": "true",
                "doc_id": "26342317678732682"
            }
            try:
                cr = sess.post("https://www.facebook.com/api/graphql/", data=cancel_data,
                    headers={"content-type": "application/x-www-form-urlencoded",
                             "origin": "https://www.facebook.com", "x-fb-lsd": lsd}, timeout=20)
                ct = cr.text
                if ct.startswith("for (;;);"): ct = ct[9:]
                print(f"  [→] Cancel response: {ct[:200]}")
            except Exception as e:
                print(f"  [!] Cancel lỗi: {e}")
        time.sleep(1)
        return True

    def _invite_core_app_admin(self, page_id: str, admin_uid: str, dtsg: str, lsd: str,
                               jazoest: str, page_session=None) -> bool:
        sess = page_session or self.session
        MUTATION = "ProfilePlusCoreAppAdminInviteMutation"
        print(f"  [->] {MUTATION}...")
        CRN = "comet.genericcometdonotuse.CometProfilePlusProfessionalDashboardAdminPermissionsRoute"
        print(f"  [->] Dung token: dtsg={dtsg[:20]}...")
        time.sleep(0.5)

        variables = {
            "input": {
                "additional_profile_id": page_id,
                "admin_id": admin_uid,
                "grant_full_control": True,
                "actor_id": page_id,
                "client_mutation_id": str(random.randint(1, 9))
            },
            "scale": 3
        }

        def _build_data(doc_id):
            return {
                "av": page_id,
                "__aaid": "0",
                "__user": page_id,
                "__a": "1",
                "__req": "u",
                "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
                "dpr": "3",
                "__ccg": "EXCELLENT",
                "__rev": self.rev,
                "__hsi": str(int(time.time() * 1000)),
                "__comet_req": "1",
                "__crn": CRN,
                "fb_dtsg": dtsg,
                "jazoest": jazoest,
                "lsd": lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": MUTATION,
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": doc_id
            }

        def _parse_response(text):
            result = json.loads(text)
            if result.get("__ar"):
                err_code = result.get("error", "")
                err_sum = result.get("errorSummary", "")
                print(f"  [!] AR {err_code}: {err_sum}")
                if str(err_code) == "1357032":
                    print("  [->] AR 1357032 — coi như invite OK")
                    return True, None, None
                return False, None, "other"
            errors = result.get("errors", [])
            if errors:
                msg = errors[0].get("message", "")
                code = errors[0].get("code", 0)
                print(f"  [!] GQL error ({code}): {msg}")
                if "field_exception" in msg.lower() or code == 1675030:
                    return False, None, "field_exception"
                return False, None, "other"
            data_val = result.get("data")
            if data_val is not None:
                invite_obj = data_val.get("profile_plus_core_admin_invite", {}) or {}
                edges = invite_obj.get("profile_with_biz_tools", {}) or {}
                admins = edges.get("core_app_admins_for_additional_profile", {}) or {}
                edge_list = admins.get("edges", []) or []
                extracted_invite_id = None
                for edge in edge_list:
                    node = edge.get("node", {}) or {}
                    inv_id = node.get("profile_admin_invite_id") or node.get("id")
                    if inv_id:
                        extracted_invite_id = str(inv_id)
                        break
                if not extracted_invite_id:
                    m_inv = re.search(r'"profile_admin_invite_id"\s*:\s*"(\d+)"', text)
                    if not m_inv:
                        m_inv = re.search(r'"AdditionalProfileCoreAppAdminInfo"[^}]*"id"\s*:\s*"(\d+)"', text)
                    if m_inv:
                        extracted_invite_id = m_inv.group(1)
                if extracted_invite_id:
                    print(f"  [OK] THÀNH CÔNG! invite_id={extracted_invite_id}")
                else:
                    print(f"  [OK] Invite OK!")
                return True, extracted_invite_id, None
            return False, None, "other"

        def _do_request(doc_id):
            resp = sess.post(
                "https://www.facebook.com/api/graphql/",
                data=_build_data(doc_id),
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.facebook.com",
                    "referer": f"https://www.facebook.com/{page_id}/settings/?tab=access",
                    "x-fb-lsd": lsd,
                    "x-fb-friendly-name": MUTATION,
                    "x-asbd-id": "129477",
                },
                timeout=30
            )
            text = resp.text
            if text.startswith("for (;;);"): text = text[9:]
            print(f"  [->] Response: {text[:800]}")
            return text

        try:
            current_docid = DOC_IDS[MUTATION]
            print(f"  [->] Dùng doc_id: {current_docid}")
            text = _do_request(current_docid)
            ok, inv_id, err_type = _parse_response(text)

            if ok:
                return True, inv_id
            if err_type == "field_exception":
                print(f"  [❌] field_exception: Session chưa được reauth hoặc page bị hạn chế")
        except Exception as e:
            print(f"  [!] Exception: {e}")
        return False, None

    def transfer_page(self, page_id: str, parent_uid: str, parent_cookie: str = None,
                      password: str = None) -> bool:
        print(f"\n[🔄] Chuyển page {page_id} → acc mẹ {parent_uid}...")

        print("[→] Lấy page context token (i_user=page_id)...")
        page_dtsg, page_lsd, page_jazoest, page_session = self._get_page_context_token(page_id)

        if not page_dtsg:
            print("[!] Không lấy được page context token, dùng user token...")
            page_dtsg = self.fb_dtsg
            page_lsd = self.lsd
            page_jazoest = self._calc_jazoest(self.fb_dtsg) if self.fb_dtsg else self.jazoest
            page_session = self.session

        print(f"\n[→] Bước 1: Search UID {parent_uid}...")
        self._search_user_for_invite(
            page_id, parent_uid, page_dtsg, page_lsd, page_jazoest, page_session
        )
        time.sleep(1)

        print(f"\n[→] Bước 2: Reauth mật khẩu...")
        if password:
            reauth_ok = self._reauth_password(
                page_id, password, page_dtsg, page_lsd, page_jazoest, page_session
            )
            if not reauth_ok:
                print("[!] Reauth thất bại - thử tiếp nhưng có thể bị lỗi permission")
            else:
                print("[✓] Reauth OK!")
                time.sleep(1)
        else:
            print("[!] Không có password → bỏ qua reauth (có thể thất bại)")

        print(f"\n[→] Bước 3: Invite UID {parent_uid} làm admin...")
        invite_ok = self._invite_core_app_admin(
            page_id, parent_uid, page_dtsg, page_lsd, page_jazoest, page_session
        )

        if not invite_ok:
            print("[❌] Invite admin thất bại!")
            return False
        print("[✓] Invite thành công!")

        if parent_cookie:
            print("\n[→] Bước 4: Accept invite bằng cookie mẹ...")
            time.sleep(3)
            accept_ok = self._accept_admin_invite(page_id, parent_uid, parent_cookie)
            if accept_ok:
                print("[✓] Acc mẹ đã accept!")
            else:
                print("[!] Accept tự động thất bại - acc mẹ cần tự vào accept")
        else:
            print("[!] Không có cookie mẹ - acc mẹ cần tự vào accept invite")

        time.sleep(5)
        print("\n[→] Bước 5: Acc con leave page...")
        clean_cookie = re.sub(r';\s*i_user=[^;]+', '', self.cookie).strip()
        page_cookie_ctx = clean_cookie + f'; i_user={page_id}'
        leave_ok = self._do_leave_page(page_id, page_cookie_ctx, page_dtsg, page_lsd, page_jazoest)
        if leave_ok:
            print(f"[✅] Chuyển page {page_id} thành công!")
        else:
            print("[!] Leave thất bại - invite đã xong, acc mẹ cần tự rời page")
        return True

    def _accept_admin_invite(self, page_id: str, parent_uid: str, parent_cookie: str) -> bool:
        try:
            me_session = requests.Session()
            me_session.headers.update(self.session.headers)
            if self.proxy:
                me_session.proxies.update({'http': self.proxy, 'https': self.proxy})
            for item in parent_cookie.split(';'):
                item = item.strip()
                if '=' in item:
                    k, v = item.split('=', 1)
                    me_session.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

            resp_page = me_session.get(f'https://www.facebook.com/notifications/', timeout=20)
            html = resp_page.text
            me_dtsg, me_lsd, me_rev = None, None, self.rev or '1017800000'
            for pat in [r'"DTSGInitialData".*?"token":"([^"]+)"', r'name="fb_dtsg"[^>]*value="([^"]+)"']:
                m = re.search(pat, html)
                if m: me_dtsg = m.group(1); break
            for pat in [r'"LSDToken".*?"token":"([^"]+)"', r'name="lsd"[^>]*value="([^"]+)"']:
                m = re.search(pat, html)
                if m: me_lsd = m.group(1); break
            rv = re.search(r'"client_revision":(\d+)', html)
            if rv: me_rev = rv.group(1)

            if not me_dtsg:
                print("[!] Không lấy được token acc mẹ để accept")
                return False

            me_jazoest = "2" + str(sum(ord(c) for c in me_dtsg))
            if not me_lsd: me_lsd = me_dtsg
            uid_m = re.search(r'c_user=(\d+)', parent_cookie)
            me_uid = uid_m.group(1) if uid_m else parent_uid

            variables = {"input": {
                "additional_profile_id": page_id,
                "actor_id": me_uid,
                "client_mutation_id": str(random.randint(1, 9))
            }}
            data = {
                "av": me_uid, "__user": me_uid, "__a": "1",
                "__req": str(random.randint(1, 20)),
                "fb_dtsg": me_dtsg, "jazoest": me_jazoest, "lsd": me_lsd,
                "__rev": me_rev, "__comet_req": "15",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "ProfilePlusCoreAppAdminAcceptInviteMutation",
                "variables": json.dumps(variables), "server_timestamps": "true",
                "doc_id": DOC_IDS.get("ProfilePlusCoreAppAdminAcceptInviteMutation") or "4621077591302496"
            }
            resp = me_session.post('https://www.facebook.com/api/graphql/', data=data,
                headers={'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                         'origin': 'https://www.facebook.com',
                         'referer': f'https://www.facebook.com/{page_id}/',
                         'x-fb-lsd': me_lsd}, timeout=30)

            if resp.status_code != 200:
                print(f"  [!] Accept HTTP {resp.status_code}")
                return False

            text = resp.text
            if text.startswith("for (;;);"): text = text[9:]
            print(f"  [->] Accept response: {text[:200]}")
            try:
                result = json.loads(text)
                if result.get("__ar"):
                    print(f"  [!] Accept AR error {result.get('error')}: {result.get('errorSummary','')}")
                    return False
                if result.get("errors"):
                    print(f"  [!] Accept GQL error: {result['errors'][0].get('message','')}")
                    return False
                if result.get("data") is not None:
                    return True
            except:
                pass
            return True
        except Exception as e:
            print(f"[!] Accept error: {e}")
            return False

    def _do_leave_page(self, page_id, page_cookie, dtsg, lsd, jazoest) -> bool:
        try:
            leave_session = requests.Session()
            leave_session.headers.update(self.session.headers)
            if self.proxy:
                leave_session.proxies.update({'http': self.proxy, 'https': self.proxy})
            for item in page_cookie.split(';'):
                item = item.strip()
                if '=' in item:
                    k, v = item.split('=', 1)
                    leave_session.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

            variables = {"input": {
                "profile_id": page_id, "invitee_id": self.uid,
                "actor_id": page_id,
                "client_mutation_id": str(random.randint(1, 9))
            }}
            data = {
                "av": page_id,
                "__user": page_id,
                "__a": "1",
                "__req": str(random.randint(1, 20)),
                "fb_dtsg": dtsg, "jazoest": jazoest, "lsd": lsd,
                "__rev": self.rev, "__comet_req": "15",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "ProfilePlusRemoveAdminMutation",
                "variables": json.dumps(variables), "server_timestamps": "true",
                "doc_id": DOC_IDS.get("ProfilePlusRemoveAdminMutation") or "28389739383083827"
            }
            resp = leave_session.post('https://www.facebook.com/api/graphql/', data=data,
                headers={'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                         'origin': 'https://www.facebook.com',
                         'referer': f'https://www.facebook.com/{page_id}/settings/',
                         'x-fb-lsd': lsd}, timeout=30)

            if resp.status_code != 200:
                print(f"[!] Leave HTTP {resp.status_code}")
                return False

            text = resp.text
            if text.startswith("for (;;);"): text = text[9:]
            print(f"  [->] Leave response: {text[:200]}")
            try:
                result = json.loads(text)
                if result.get("__ar"):
                    print(f"  [!] Leave AR error: {result.get('error')} - {result.get('errorSummary','')}")
                    return False
                if result.get("errors"):
                    err_msg = result['errors'][0].get('message','')
                    print(f"  [!] Leave GQL error: {err_msg}")
                    if "not found" in err_msg.lower() or "field_exception" in err_msg.lower():
                        BACKUP_LEAVE_DOCIDS = [
                            "7435279336527234",
                            "5435279336527234",
                            "9673725249401044",
                        ]
                        for backup_id in BACKUP_LEAVE_DOCIDS:
                            try:
                                print(f"  [→] Thử leave doc_id backup: {backup_id}")
                                data["doc_id"] = backup_id
                                r2 = leave_session.post(
                                    'https://www.facebook.com/api/graphql/', data=data,
                                    headers={'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                                             'origin': 'https://www.facebook.com',
                                             'referer': f'https://www.facebook.com/{page_id}/settings/',
                                             'x-fb-lsd': lsd}, timeout=30)
                                t2 = r2.text
                                if t2.startswith("for (;;);"): t2 = t2[9:]
                                r2j = json.loads(t2)
                                if r2j.get("data") is not None and not r2j.get("errors"):
                                    print(f"  [✅] Leave thành công với backup doc_id: {backup_id}")
                                    save_docid("ProfilePlusRemoveAdminMutation", backup_id)
                                    return True
                            except:
                                continue
                    return False
                if result.get("data") is not None:
                    return True
            except:
                pass
            return True
        except Exception as e:
            print(f"[!] Leave error: {e}")
            return False

    def check_pages(self) -> list:
        pages = []
        seen_ids = set()

        def add_page(pid, pname):
            pid = str(pid).strip()
            pname = str(pname).strip()
            if pid and pid not in seen_ids and pid.isdigit() and len(pid) >= 5 and pid != str(self.uid):
                seen_ids.add(pid)
                pages.append({'id': pid, 'name': pname})

        try:
            print("\n[🔍] Đang lấy danh sách Profile Plus...")
            print("[→] Fetch /pages/?category=your_pages ...")
            try:
                resp = self.session.get(
                    "https://www.facebook.com/pages/?category=your_pages", timeout=25)
                html = resp.text
                print(f"[→] HTML size: {len(html)} bytes")

                def decode_name(s):
                    try: return json.loads('"' + s + '"')
                    except: return s

                for m in re.finditer(r'"id"\s*:\s*"(\d{10,})"[^}]{0,300}"name"\s*:\s*"([^"]{2,80})"', html):
                    add_page(m.group(1), decode_name(m.group(2)))
                for m in re.finditer(r'"name"\s*:\s*"([^"]{2,80})"[^}]{0,300}"id"\s*:\s*"(\d{10,})"', html):
                    add_page(m.group(2), decode_name(m.group(1)))
                for m in re.finditer(r'"__typename"\s*:\s*"Page"[\s\S]{0,200}?"id"\s*:\s*"(\d+)"[\s\S]{0,200}?"name"\s*:\s*"([^"]+)"', html):
                    add_page(m.group(1), m.group(2))
            except Exception as e:
                print(f"[!] Method chính lỗi: {e}")

        except Exception as e:
            print(f"[❌] Lỗi check pages: {e}")

        print(f"\n{'='*60}")
        print(f"  📊 TỔNG SỐ PROFILE PLUS: {len(pages)}")
        print(f"{'='*60}")
        for i, p in enumerate(pages, 1):
            print(f"  [{i}] {p['name']} | ID: {p['id']}")
        print(f"{'='*60}\n")
        return pages

    def create_page(self, name: str, bio: str) -> Dict[str, Any]:
        try:
            print(f"\n[⏳] Tạo Page: {name}...")
            self.session.get('https://www.facebook.com/pages/creation/', timeout=20)
            time.sleep(1)

            category = random.choice([169421023103905, 2347428775505624])
            variables = {
                "input": {
                    "bio": bio, "categories": [str(category)],
                    "creation_source": "comet", "name": name,
                    "actor_id": self.uid,
                    "client_mutation_id": str(random.randint(1, 9999))
                }
            }
            data = {
                "av": self.uid, "__user": self.uid, "__a": "1",
                "__req": str(random.randint(1, 20)),
                "__hs": "19743.HYP:comet_pkg.2.1..2.1", "dpr": "1",
                "__ccg": "EXCELLENT", "__rev": self.rev, "__comet_req": "15",
                "fb_dtsg": self.fb_dtsg, "jazoest": self.jazoest, "lsd": self.lsd,
                "__spin_r": self.rev, "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "AdditionalProfilePlusCreationMutation",
                "variables": json.dumps(variables), "server_timestamps": "true",
                "doc_id": "23863457623296585"
            }
            headers = {
                'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': 'https://www.facebook.com/pages/creation/',
                'x-fb-lsd': self.lsd,
            }
            response = self.session.post('https://www.facebook.com/api/graphql/',
                data=data, headers=headers, timeout=30)
            print(f"[→] Response code: {response.status_code}")

            text = response.text
            if text.startswith('for (;;);'): text = text[9:]

            try:
                result = json.loads(text)
            except:
                return {"success": False, "error": "Invalid JSON"}

            if result.get('errors') and result['errors']:
                return {"success": False, "error": result['errors'][0].get('message', 'Unknown')}

            if result.get('data'):
                d = result['data']
                if 'additional_profile_plus_create' in d:
                    pd = d['additional_profile_plus_create']
                    if isinstance(pd, dict):
                        if pd.get('error_message'):
                            return {"success": False, "error": pd['error_message'], "rate_limit": True}
                        for key in ['additional_profile', 'page']:
                            if pd.get(key) and isinstance(pd[key], dict) and 'id' in pd[key]:
                                page_id = pd[key]['id']
                                print(f"[✅] Tạo Page thành công! ID: {page_id}")
                                return {"success": True, "page_id": page_id}

            return {"success": False, "error": "Unknown error"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_page_upload_token(self, page_id: str):
        try:
            clean = re.sub(r';\s*i_user=[^;]+', '', self.cookie).strip()
            page_cookie = clean + f'; i_user={page_id}'
            tmp = requests.Session()
            tmp.headers.update(self.session.headers)
            if self.proxy:
                tmp.proxies.update({'http': self.proxy, 'https': self.proxy})
            for item in page_cookie.split(';'):
                item = item.strip()
                if '=' in item:
                    k, v = item.split('=', 1)
                    tmp.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

            for url in [
                f'https://www.facebook.com/{page_id}',
                f'https://www.facebook.com/pages/?category=your_pages',
            ]:
                try:
                    r = tmp.get(url, timeout=20)
                    html = r.text
                    dtsg = None
                    for pat in [
                        r'"DTSGInitialData".*?"token":"([^"]+)"',
                        r'name="fb_dtsg"[^>]*value="([^"]+)"',
                        r'"fb_dtsg":\{"token":"([^"]+)"',
                    ]:
                        m = re.search(pat, html)
                        if m:
                            dtsg = m.group(1)
                            break
                    if dtsg:
                        jazoest = self._calc_jazoest(dtsg)
                        lsd = dtsg
                        for pat in [r'"LSDToken".*?"token":"([^"]+)"']:
                            m = re.search(pat, html)
                            if m:
                                lsd = m.group(1)
                                break
                        print(f"  [✓] Page upload token OK: dtsg={dtsg[:20]}...")
                        return dtsg, jazoest, lsd, tmp
                except:
                    continue
        except Exception as e:
            print(f"  [!] _get_page_upload_token lỗi: {e}")
        return None, None, None, None

    def _call_gql_set_photo(self, page_id: str, fbid: str,
                             page_dtsg: str, page_jazoest: str, page_lsd: str,
                             page_sess, mutation_name: str, doc_id: str,
                             extra_vars: dict = None) -> bool:
        variables = {
            "input": {
                "actor_id": page_id,
                "profile_id": page_id,
                "photo_id": fbid,
                "client_mutation_id": "1",
            },
            "scale": 3,
        }
        if extra_vars:
            variables["input"].update(extra_vars)

        gd = {
            "av": page_id, "__user": page_id,
            "__a": "1", "__req": str(random.randint(5, 20)),
            "__rev": self.rev, "__ccg": "EXCELLENT", "dpr": "3",
            "fb_dtsg": page_dtsg, "jazoest": page_jazoest, "lsd": page_lsd,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": mutation_name,
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": doc_id,
        }
        try:
            gr = page_sess.post(
                "https://www.facebook.com/api/graphql/",
                data=gd,
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://www.facebook.com",
                    "referer": f"https://www.facebook.com/{page_id}",
                    "x-fb-lsd": page_lsd,
                    "x-fb-friendly-name": mutation_name,
                },
                timeout=30)
            gt = gr.text
            if gt.startswith("for (;;);"): gt = gt[9:]
            print(f"  [→] {mutation_name}: {gt[:200]}")
            try:
                gj = json.loads(gt)
                if gj.get("errors"):
                    msg = gj["errors"][0].get("message", "")
                    if "not found" in msg.lower():
                        print(f"  [!] doc_id {doc_id} hết hạn")
                        return False
                    print(f"  [!] GQL error: {msg}")
                    return False
                if gj.get("__ar") and not gj.get("errors"):
                    payload = gj.get("payload", {}) or {}
                    if payload.get("errorSummary") or payload.get("error"):
                        print(f"  [!] AR error: {payload}")
                        return False
                    print(f"  [✅] {mutation_name}: OK (ar-no-error)")
                    return True
                if gj.get("data") is not None:
                    print(f"  [✅] {mutation_name}: OK (data)")
                    return True
            except json.JSONDecodeError:
                if gr.status_code == 200 and len(gt) > 5:
                    print(f"  [✅] {mutation_name}: OK (non-json 200)")
                    return True
        except Exception as e:
            print(f"  [!] {mutation_name} exception: {e}")
        return False

    def _upload_photo_get_fbid(self, page_id: str, image_data: bytes,
                                filename: str, page_dtsg: str, page_jazoest: str,
                                page_lsd: str, page_sess, proxy_text: str = None) -> Optional[str]:
        
        # Thêm text vào ảnh nếu có proxy_text
        if proxy_text:
            image_data = ImageTextOverlay.add_text_to_image(
                image_data,
                f"🌐 {proxy_text}",
                position=(10, 10),
                font_size=20,
                color=(255, 255, 255)
            )
        
        files = {'file': (filename, image_data, 'image/jpeg')}
        data = {
            'profile_id': page_id, 'photo_source': '57',
            'av': page_id, '__user': page_id,
            'fb_dtsg': page_dtsg, 'jazoest': page_jazoest, 'lsd': page_lsd,
            '__a': '1', '__req': '2', '__rev': self.rev,
            '__ccg': 'EXCELLENT', 'dpr': '3',
        }
        try:
            resp = page_sess.post(
                'https://www.facebook.com/profile/picture/upload/',
                files=files, data=data,
                headers={
                    'origin': 'https://www.facebook.com',
                    'referer': f'https://www.facebook.com/{page_id}',
                    'x-fb-lsd': page_lsd,
                },
                timeout=60)
            txt = resp.text
            print(f"  [→] Upload raw: status={resp.status_code} | {txt[:250]}")
            if resp.status_code != 200:
                return None
            if txt.startswith("for (;;);"): txt = txt[9:]
            try:
                rj = json.loads(txt)
                payload = rj.get("payload", {}) or {}
                fbid = payload.get("fbid") or payload.get("photo_id") or rj.get("fbid")
                if fbid:
                    return str(fbid)
            except:
                pass
            m = re.search(r'"fbid"\s*:\s*"?(\d+)"?', txt)
            if m:
                return m.group(1)
        except Exception as e:
            print(f"  [!] _upload_photo_get_fbid lỗi: {e}")
        return None

    def upload_avatar(self, page_id: str, image_data: bytes, proxy_text: str = None) -> Optional[str]:
        print(f"\n[📤] Upload Avatar cho Page {page_id}...")
        
        # Thêm text proxy vào ảnh nếu có
        if proxy_text:
            print(f"  [📝] Thêm text proxy vào avatar: {proxy_text}")
        
        page_dtsg, page_jazoest, page_lsd, page_sess = self._get_page_upload_token(page_id)
        if not page_dtsg:
            print("  [⚠️] Dùng user token thay thế")
            page_dtsg, page_jazoest, page_lsd, page_sess = (
                self.fb_dtsg, self.jazoest, self.lsd, self.session)

        print("  [→] Bước 1: Upload ảnh...")
        fbid = self._upload_photo_get_fbid(
            page_id, image_data, 'avatar.jpg',
            page_dtsg, page_jazoest, page_lsd, page_sess, proxy_text)

        if not fbid:
            print("[❌] AVATAR: Không lấy được fbid")
            return False
        print(f"  [✓] fbid = {fbid}")

        AVATAR_DOC_IDS = {
            "ProfileCometProfilePictureSetMutation": "25310860631923926",
        }
        for mut in ["ProfileCometProfilePictureSetMutation",
                    "ProfileCometSetProfilePictureMutation"]:
            cached = DOC_IDS.get(mut)
            if cached:
                AVATAR_DOC_IDS[mut] = cached

        for mut_name, doc_id in AVATAR_DOC_IDS.items():
            print(f"  [→] Thử {mut_name} doc_id={doc_id}...")
            variables = json.dumps({
                "input": {
                    "attribution_id_v2": "ProfileCometCollectionRoot.react,comet.profile.collection.followers,via_cold_start",
                    "caption": "",
                    "existing_photo_id": fbid,
                    "expiration_time": None,
                    "profile_id": page_id,
                    "profile_pic_method": "EXISTING",
                    "profile_pic_source": "TIMELINE",
                    "scaled_crop_rect": {"height": 1, "width": 1, "x": 0, "y": 0},
                    "skip_cropping": True,
                    "skip_prompt": True,
                    "actor_id": page_id,
                    "client_mutation_id": "1",
                    "isPage": False,
                    "isProfile": True,
                    "sectionToken": "UNKNOWN",
                    "collectionToken": "UNKNOWN",
                },
                "scale": 3,
            })
            gd = {
                "av": page_id, "__aaid": "0", "__user": page_id,
                "__a": "1", "__req": "x", "__rev": self.rev,
                "__hs": "20505.HYP:comet_pkg.2.1...0",
                "dpr": "3", "__ccg": "EXCELLENT",
                "__crn": "comet.fbweb.CometProfileTimelineListViewRoute",
                "fb_dtsg": page_dtsg, "jazoest": page_jazoest, "lsd": page_lsd,
                "__spin_r": self.rev, "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": mut_name,
                "variables": variables,
                "server_timestamps": "true",
                "doc_id": doc_id,
            }
            try:
                gr = page_sess.post(
                    "https://www.facebook.com/api/graphql/",
                    data=gd,
                    headers={
                        "content-type": "application/x-www-form-urlencoded",
                        "origin": "https://www.facebook.com",
                        "referer": f"https://www.facebook.com/{page_id}",
                        "x-fb-lsd": page_lsd,
                        "x-fb-friendly-name": mut_name,
                    },
                    timeout=30)
                gt = gr.text
                if gt.startswith("for (;;);"): gt = gt[9:]
                print(f"  [→] Response: {gt[:300]}")
                try:
                    gj = json.loads(gt)
                    if gj.get("errors"):
                        msg = gj["errors"][0].get("message", "")
                        if "not found" in msg.lower():
                            print(f"  [!] doc_id {doc_id} hết hạn → tìm mới...")
                            new_doc = self._auto_find_docid(mut_name, page_id)
                            if new_doc:
                                save_docid(mut_name, new_doc)
                                AVATAR_DOC_IDS[mut_name] = new_doc
                            continue
                        print(f"  [!] GQL error: {msg}")
                        continue
                    if gj.get("data") is not None and not gj.get("errors"):
                        print("[✅] AVATAR: THÀNH CÔNG")
                        return fbid
                    if gj.get("__ar") and not gj.get("errors"):
                        err_sum = (gj.get("payload") or {}).get("errorSummary", "")
                        if not err_sum:
                            print("[✅] AVATAR: THÀNH CÔNG (ar-ok)")
                            return fbid
                        print(f"  [!] AR error: {err_sum}")
                except json.JSONDecodeError:
                    if gr.status_code == 200:
                        print("[✅] AVATAR: THÀNH CÔNG (200)")
                        return fbid
            except Exception as e:
                print(f"  [!] Exception: {e}")

        print("  [→] Fallback: tự tìm doc_id từ JS bundle...")
        for mut in ["ProfileCometProfilePictureSetMutation",
                    "ProfileCometSetProfilePictureMutation"]:
            new_doc = self._auto_find_docid(mut, page_id)
            if new_doc:
                save_docid(mut, new_doc)
                ok = self._call_gql_set_photo(
                    page_id, fbid, page_dtsg, page_jazoest, page_lsd, page_sess,
                    mut, new_doc)
                if ok:
                    print(f"[✅] AVATAR: THÀNH CÔNG (auto-find {mut})")
                    return fbid

        print("[❌] AVATAR: THẤT BẠI")
        return None

    def upload_cover(self, page_id: str, cover_fbid: str, proxy_text: str = None) -> bool:
        """Đặt Cover bằng CHÍNH FBID của ảnh đã upload làm Avatar."""
        if not cover_fbid:
            print("  [⚠️] Cover FBID trống — bỏ qua")
            return False

        print(f"\n[🖼️] Dùng Avatar FBID làm Cover: {cover_fbid}")
        
        if proxy_text:
            print(f"  [📝] Proxy hiển thị trên ảnh bìa: {proxy_text}")

        page_dtsg, page_jazoest, page_lsd, page_sess = self._get_page_upload_token(page_id)
        if not page_dtsg:
            print("  [⚠️] Dùng user token thay thế")
            page_dtsg, page_jazoest, page_lsd, page_sess = (
                self.fb_dtsg, self.jazoest, self.lsd, self.session
            )

        COVER_MUTATIONS = [
            ("ProfileCometCoverPhotoUpdateMutation", "31388044007461211"),
            ("ProfileCometCoverPhotoUpdateMutation", DOC_IDS.get("ProfileCometCoverPhotoUpdateMutation", "")),
            ("CometProfileCoverPhotoUpdateMutation", DOC_IDS.get("CometProfileCoverPhotoUpdateMutation", "")),
        ]
        seen_ids = set()
        filtered = []
        for mut, did in COVER_MUTATIONS:
            if did and did not in seen_ids:
                seen_ids.add(did)
                filtered.append((mut, did))

        def call_cover(mut_name: str, doc_id: str) -> Optional[bool]:
            variables = json.dumps({
                "input": {
                    "attribution_id_v2": "ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start",
                    "cover_photo_id": str(cover_fbid),
                    "focus": {"x": 0.5, "y": 0.5},
                    "target_user_id": page_id,
                    "actor_id": page_id,
                    "client_mutation_id": "2",
                },
                "scale": 3,
                "contextualProfileContext": None,
            })
            data = {
                "av": page_id,
                "__aaid": "0",
                "__user": page_id,
                "__a": "1",
                "__req": "1a",
                "__rev": self.rev,
                "__hs": "20505.HYP:comet_pkg.2.1...0",
                "dpr": "3",
                "__ccg": "EXCELLENT",
                "__crn": "comet.fbweb.CometProfileTimelineListViewRoute",
                "fb_dtsg": page_dtsg,
                "jazoest": page_jazoest,
                "lsd": page_lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": mut_name,
                "variables": variables,
                "server_timestamps": "true",
                "doc_id": doc_id,
            }
            try:
                resp = page_sess.post(
                    "https://www.facebook.com/api/graphql/",
                    data=data,
                    headers={
                        "content-type": "application/x-www-form-urlencoded",
                        "origin": "https://www.facebook.com",
                        "referer": f"https://www.facebook.com/{page_id}",
                        "x-fb-lsd": page_lsd,
                        "x-fb-friendly-name": mut_name,
                    },
                    timeout=30,
                )
                text = resp.text
                if text.startswith("for (;;);"):
                    text = text[9:]
                print(f"  [→] Cover response: {text[:300]}")

                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    return True if resp.status_code == 200 and len(text) > 5 else False

                if result.get("errors"):
                    msg = result["errors"][0].get("message", "")
                    print(f"  [!] GQL error: {msg}")
                    return None if "not found" in msg.lower() else False

                if result.get("data") is not None:
                    return True

                if result.get("__ar"):
                    payload = result.get("payload") or {}
                    if not payload.get("errorSummary") and not payload.get("error"):
                        return True
                    print(f"  [!] AR error: {payload.get('errorSummary') or payload.get('error')}")
                    return False
            except Exception as e:
                print(f"  [!] Cover exception: {e}")
                return False
            return False

        for mut_name, doc_id in filtered:
            print(f"  [→] Thử {mut_name} doc_id={doc_id}...")
            result = call_cover(mut_name, doc_id)
            if result is True:
                print("[✅] ẢNH BÌA: THÀNH CÔNG — dùng chính Avatar FBID")
                save_docid(mut_name, doc_id)
                return True
            if result is None:
                print(f"  [!] doc_id {doc_id} hết hạn → tự tìm doc_id mới...")
                new_doc = self._auto_find_docid(mut_name, page_id)
                if new_doc:
                    save_docid(mut_name, new_doc)
                    retry = call_cover(mut_name, new_doc)
                    if retry is True:
                        print("[✅] ẢNH BÌA: THÀNH CÔNG — dùng chính Avatar FBID")
                        return True

        print("[❌] ẢNH BÌA: THẤT BẠI")
        return False


# ================== MAIN ==================

def run_transfer(session, page_id, parent_uid, password, parent_cookie):
    print(f"\n{'='*70}")
    print(f"  📌 PAGE ID : {page_id}")
    print(f"  👤 UID MẸ  : {parent_uid}")
    print(f"{'='*70}")

    print(f"\n┌─ [BƯỚC 1/7] 🔑 Lấy Page Context Token (i_user={page_id})...")
    page_dtsg, page_lsd, page_jazoest, page_session = session._get_page_context_token(page_id)
    if not page_dtsg:
        print(f"│  [⚠️] Không lấy được page token → fallback user token")
        page_dtsg    = session.fb_dtsg
        page_lsd     = session.lsd
        page_jazoest = session._calc_jazoest(session.fb_dtsg) if session.fb_dtsg else session.jazoest
        page_session = session.session
        print(f"└─ [⚠️] BƯỚC 1: Dùng user token (tiếp tục nhưng có thể fail)")
    else:
        print(f"└─ [✅] BƯỚC 1: Page token OK — dtsg={page_dtsg[:25]}...")

    print(f"\n┌─ [BƯỚC 2/7] 🔍 Tìm UID {parent_uid} + vào trang cấp quyền...")
    search_ok = session._search_user_for_invite(
        page_id, parent_uid, page_dtsg, page_lsd, page_jazoest, page_session
    )
    if not search_ok:
        print(f"└─ [❌] BƯỚC 2 THẤT BẠI: Không tìm được UID → Dừng lại")
        return False
    print(f"└─ [✅] BƯỚC 2: Tìm UID thành công — đã vào trang cấp quyền truy cập")
    time.sleep(1)

    print(f"\n┌─ [BƯỚC 3/7] 🛡️  Cấp quyền truy cập cho UID {parent_uid}...")
    print(f"│  [→] Kiểm tra và hủy invite cũ nếu có...")
    session._cancel_existing_invite(page_id, parent_uid, page_dtsg, page_lsd, page_jazoest, page_session)
    time.sleep(1)

    print(f"\n┌─ [BƯỚC 4/7] 🔑 Nhập mật khẩu xác nhận (reauth)...")
    if not password:
        print(f"└─ [⚠️] BƯỚC 4: Không có password → bỏ qua (dễ bị lỗi permission ở bước 5)")
    else:
        user_dtsg    = session.fb_dtsg
        user_lsd     = session.lsd
        user_jazoest = session.jazoest
        user_sess    = session.session
        print(f"│  [→] Dùng user token để reauth: dtsg={user_dtsg[:20]}...")
        reauth_ok = session._reauth_password(
            page_id, password, user_dtsg, user_lsd, user_jazoest, user_sess
        )
        if reauth_ok:
            print(f"└─ [✅] BƯỚC 4: Reauth thành công!")
        else:
            print(f"└─ [⚠️] BƯỚC 4: Reauth trả lỗi — tiếp tục gửi invite")
        time.sleep(1)

    print(f"\n┌─ [BƯỚC 5/7] ➡️  Nhấn Tiếp — gửi invite admin...")
    invite_result = session._invite_core_app_admin(
        page_id, parent_uid, page_dtsg, page_lsd, page_jazoest, page_session
    )
    if isinstance(invite_result, tuple):
        invite_ok, got_invite_id = invite_result
    else:
        invite_ok, got_invite_id = invite_result, None

    if not invite_ok:
        print(f"└─ [❌] BƯỚC 5 THẤT BẠI: Invite không gửi được → Dừng lại")
        return False
    print(f"└─ [✅] BƯỚC 5: Invite gửi thành công! invite_id={got_invite_id}")
    time.sleep(3)

    print(f"\n┌─ [BƯỚC 6/7] ✅ Acc mẹ accept lời mời...")
    if not parent_cookie:
        print(f"└─ [⚠️] BƯỚC 6: Không có cookie mẹ → bỏ qua, acc mẹ tự vào accept")
        return True

    me_session = requests.Session()
    me_session.headers.update(session.session.headers)
    if session.proxy:
        me_session.proxies.update({'http': session.proxy, 'https': session.proxy})
    for item in parent_cookie.split(';'):
        item = item.strip()
        if '=' in item:
            k, v = item.split('=', 1)
            me_session.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

    uid_m = re.search(r'c_user=(\d+)', parent_cookie)
    if not uid_m:
        print(f"└─ [❌] BƯỚC 6 THẤT BẠI: Không tìm thấy c_user trong cookie mẹ")
        return False
    me_uid = uid_m.group(1)

    resp2 = me_session.get('https://www.facebook.com/', timeout=20)
    html = resp2.text
    me_dtsg, me_lsd = None, None
    for pat in [r'"DTSGInitialData".*?"token":"([^"]+)"', r'name="fb_dtsg"[^>]*value="([^"]+)"']:
        m = re.search(pat, html)
        if m: me_dtsg = m.group(1); break
    for pat in [r'"LSDToken".*?"token":"([^"]+)"', r'name="lsd"[^>]*value="([^"]+)"']:
        m = re.search(pat, html)
        if m: me_lsd = m.group(1); break
    rv = re.search(r'"client_revision":(\d+)', html)
    me_rev = rv.group(1) if rv else session.rev or '1017800000'
    sr = re.search(r'"__spin_r":(\d+)', html)
    me_spin_r = sr.group(1) if sr else me_rev

    if not me_dtsg:
        print(f"└─ [❌] BƯỚC 6 THẤT BẠI: Không lấy được token acc mẹ")
        return False

    me_jazoest = "2" + str(sum(ord(c) for c in me_dtsg))
    if not me_lsd: me_lsd = me_dtsg
    print(f"│  [✓] Token acc mẹ OK — dtsg={me_dtsg[:20]}...")

    invite_id = None
    try:
        inv_resp = me_session.get(
            f'https://www.facebook.com/profile/invites/?profile_id={page_id}',
            timeout=20)
        inv_html = inv_resp.text
        m = re.search(r'"profile_admin_invite_id"\s*:\s*"(\d+)"', inv_html)
        if m:
            invite_id = m.group(1)
            print(f"│  [✓] invite_id = {invite_id}")
        if not invite_id:
            m = re.search(r'"__typename"\s*:\s*"ProfileAdminInvite"[^}]*"id"\s*:\s*"(\d+)"', inv_html)
            if not m:
                m = re.search(r'"id"\s*:\s*"(\d+)"[^}]*"__typename"\s*:\s*"ProfileAdminInvite"', inv_html)
            if m:
                invite_id = m.group(1)
                print(f"│  [✓] invite_id (typename) = {invite_id}")
    except Exception as e:
        print(f"│  [!] Fetch invite page lỗi: {e}")

    if not invite_id and got_invite_id:
        invite_id = got_invite_id
        print(f"│  [✓] invite_id từ BƯỚC 4 = {invite_id}")
    if not invite_id:
        print(f"│  [⚠️] Không tìm được invite_id → dùng page_id fallback")
        invite_id = page_id

    variables = {
        "input": {
            "client_mutation_id": "1",
            "actor_id": me_uid,
            "is_accept": True,
            "profile_admin_invite_id": invite_id,
            "user_id": me_uid
        },
        "scale": 3
    }
    data = {
        "av": me_uid, "__aaid": "0", "__user": me_uid, "__a": "1",
        "__req": str(random.randint(10, 30)),
        "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
        "dpr": "3", "__ccg": "EXCELLENT", "__rev": me_rev, "__comet_req": "15",
        "__crn": "comet.fbweb.PageCometLaunchpointInvitesRoute",
        "fb_dtsg": me_dtsg, "jazoest": me_jazoest, "lsd": me_lsd,
        "__spin_r": me_spin_r, "__spin_b": "trunk",
        "__spin_t": str(int(time.time())),
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "ProfilePlusCometAcceptOrDeclineAdminInviteMutation",
        "variables": json.dumps(variables),
        "server_timestamps": "true",
        "doc_id": "33525122957135374"
    }
    resp = me_session.post('https://www.facebook.com/api/graphql/', data=data,
        headers={
            'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.facebook.com',
            'referer': f'https://www.facebook.com/profile/invites/?profile_id={page_id}',
            'x-fb-lsd': me_lsd,
            'x-fb-friendly-name': 'ProfilePlusCometAcceptOrDeclineAdminInviteMutation',
        }, timeout=30)

    if resp.status_code != 200:
        print(f"└─ [❌] BƯỚC 5 THẤT BẠI: HTTP {resp.status_code}")
        return False

    text = resp.text
    if text.startswith("for (;;);"): text = text[9:]
    print(f"│  [→] Accept response: {text[:300]}")

    try:
        result = json.loads(text)
        if result.get("__ar"):
            err_code = str(result.get("error",""))
            err_sum  = result.get("errorSummary","")
            if err_code == "1357053":
                print(f"└─ [⚠️] BƯỚC 6: Acc mẹ bị hạn chế tài khoản FB (1357053)")
                print(f"└─ [💡] Acc mẹ cần vào Settings → tự accept lời mời thủ công")
                return False
            print(f"└─ [❌] BƯỚC 6 THẤT BẠI: AR {err_code} — {err_sum}")
            return False
        if result.get("errors"):
            msg  = result['errors'][0].get('message','')
            code = str(result['errors'][0].get('code',''))
            if code == "1357053" or "1357053" in msg:
                print(f"└─ [⚠️] BƯỚC 6: Acc mẹ bị hạn chế tài khoản FB (1357053)")
                print(f"└─ [💡] Acc mẹ cần vào Settings → tự accept lời mời thủ công")
                return False
            print(f"└─ [❌] BƯỚC 6 THẤT BẠI: GQL — {msg}")
            return False
        if result.get("data") is not None:
            print(f"└─ [✅] BƯỚC 6: Accept thành công!")
        else:
            print(f"└─ [⚠️] BƯỚC 6: Không có data — acc mẹ kiểm tra thủ công")
    except Exception as e:
        print(f"└─ [⚠️] BƯỚC 6: Parse lỗi ({e}) — tiếp tục")

    time.sleep(3)

    print(f"\n┌─ [BƯỚC 7/7] 🚪 Gỡ acc reg khỏi page...")
    clean_cookie = re.sub(r';\s*i_user=[^;]+', '', session.cookie).strip()
    page_cookie_ctx = clean_cookie + f'; i_user={page_id}'
    leave_ok = session._do_leave_page(page_id, page_cookie_ctx, page_dtsg, page_lsd, page_jazoest)
    if leave_ok:
        print(f"└─ [✅] BƯỚC 7: Gỡ acc reg thành công!")
    else:
        print(f"└─ [⚠️] BƯỚC 7: Gỡ thất bại — acc mẹ đã có page, acc con tự rời sau")

    print(f"\n{'='*70}")
    print(f"  🎉 CHUYỂN PAGE THÀNH CÔNG!")
    print(f"  📋 Page {page_id} → UID Mẹ {parent_uid}")
    print(f"  🔗 https://facebook.com/{page_id}")
    print(f"{'='*70}")
    return True


def run_accept_invite(page_id, parent_uid, parent_cookie, rev="1017800000"):
    print(f"\n{'='*70}")
    print(f"  📌 PAGE ID : {page_id}")
    print(f"  👤 ACC MẸ  : {parent_uid}")
    print(f"{'='*70}")

    try:
        me_session = requests.Session()
        me_session.headers.update({
            'authority': 'www.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        })
        proxy = SETTINGS.get("proxy", "")
        if proxy:
            me_session.proxies.update({'http': proxy, 'https': proxy})
        for item in parent_cookie.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                me_session.cookies.set(k.strip(), v.strip(), domain='.facebook.com')

        uid_m = re.search(r'c_user=(\d+)', parent_cookie)
        if not uid_m:
            print("  [❌] Không tìm thấy c_user trong cookie mẹ!")
            return False
        me_uid = uid_m.group(1)
        print(f"  [✓] UID acc mẹ: {me_uid}")

        print(f"\n┌─ [BƯỚC 1/3] 🔑 Lấy token acc mẹ...")
        invite_url = f"https://www.facebook.com/profile/invites/?profile_id={page_id}"
        resp_page = me_session.get(invite_url, timeout=20)
        html = resp_page.text
        me_dtsg, me_lsd = None, None

        for pat in [r'"DTSGInitialData".*?"token":"([^"]+)"', r'name="fb_dtsg"[^>]*value="([^"]+)"']:
            m = re.search(pat, html)
            if m: me_dtsg = m.group(1); break

        if not me_dtsg:
            resp2 = me_session.get('https://www.facebook.com/', timeout=20)
            html = resp2.text
            for pat in [r'"DTSGInitialData".*?"token":"([^"]+)"', r'name="fb_dtsg"[^>]*value="([^"]+)"']:
                m = re.search(pat, html)
                if m: me_dtsg = m.group(1); break

        for pat in [r'"LSDToken".*?"token":"([^"]+)"', r'name="lsd"[^>]*value="([^"]+)"']:
            m = re.search(pat, html)
            if m: me_lsd = m.group(1); break
        rv = re.search(r'"client_revision":(\d+)', html)
        if rv: rev = rv.group(1)
        spin_r = re.search(r'"__spin_r":(\d+)', html)
        spin_r_val = spin_r.group(1) if spin_r else rev

        if not me_dtsg:
            print("└─ [❌] BƯỚC 1 THẤT BẠI: Không lấy được token acc mẹ!")
            return False

        me_jazoest = "2" + str(sum(ord(c) for c in me_dtsg))
        if not me_lsd: me_lsd = me_dtsg
        print(f"└─ [✅] BƯỚC 1: Token OK — dtsg={me_dtsg[:25]}...")

        print(f"\n┌─ [BƯỚC 2/3] 🔍 Lấy invite_id của page {page_id}...")
        invite_id = None
        m = re.search(r'"profile_admin_invite_id"\s*:\s*"(\d+)"', html)
        if m: invite_id = m.group(1)
        if not invite_id:
            m = re.search(rf'"profile_id"\s*:\s*"{page_id}"[^}}]{{0,300}}"id"\s*:\s*"(\d+)"', html)
            if m: invite_id = m.group(1)

        if invite_id:
            print(f"└─ [✅] BƯỚC 2: invite_id = {invite_id}")
        else:
            print(f"└─ [⚠️] BƯỚC 2: Không tìm thấy invite_id → dùng page_id làm fallback")
            invite_id = page_id

        print(f"\n┌─ [BƯỚC 3/3] ✅ Accept invite...")
        variables = {
            "input": {
                "client_mutation_id": "1",
                "actor_id": me_uid,
                "is_accept": True,
                "profile_admin_invite_id": invite_id,
                "user_id": me_uid
            },
            "scale": 3
        }

        data = {
            "av": me_uid, "__aaid": "0", "__user": me_uid, "__a": "1",
            "__req": str(random.randint(10, 30)),
            "__hs": "20504.HYP:comet_plat_default_pkg.2.1...0",
            "dpr": "3", "__ccg": "EXCELLENT", "__rev": rev, "__comet_req": "15",
            "__crn": "comet.fbweb.PageCometLaunchpointInvitesRoute",
            "fb_dtsg": me_dtsg, "jazoest": me_jazoest, "lsd": me_lsd,
            "__spin_r": spin_r_val, "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "ProfilePlusCometAcceptOrDeclineAdminInviteMutation",
            "variables": json.dumps(variables),
            "server_timestamps": "true",
            "doc_id": "33525122957135374"
        }

        resp = me_session.post(
            'https://www.facebook.com/api/graphql/',
            data=data,
            headers={
                'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'referer': f'https://www.facebook.com/profile/invites/?profile_id={page_id}',
                'x-fb-lsd': me_lsd,
                'x-fb-friendly-name': 'ProfilePlusCometAcceptOrDeclineAdminInviteMutation',
            }, timeout=30
        )

        if resp.status_code != 200:
            print(f"└─ [❌] BƯỚC 3 THẤT BẠI: HTTP {resp.status_code}")
            return False

        text = resp.text
        if text.startswith("for (;;);"): text = text[9:]
        print(f"  [→] Response: {text[:400]}")

        try:
            result = json.loads(text)
            if result.get("__ar"):
                print(f"└─ [❌] BƯỚC 3 THẤT BẠI: AR {result.get('error')} — {result.get('errorSummary','')}")
                return False
            if result.get("errors"):
                print(f"└─ [❌] BƯỚC 3 THẤT BẠI: GQL — {result['errors'][0].get('message','')}")
                return False
            if result.get("data") is not None:
                print(f"└─ [✅] BƯỚC 3: Accept THÀNH CÔNG!")
                print(f"\n{'='*70}")
                print(f"  🎉 ACC MẸ ĐÃ NHẬN PAGE {page_id} THÀNH CÔNG!")
                print(f"  🔗 https://facebook.com/{page_id}")
                print(f"{'='*70}")
                return True
        except Exception as e:
            print(f"└─ [❌] Parse lỗi: {e}")
            return False

        print(f"└─ [❌] BƯỚC 3 THẤT BẠI: Không có data trong response")
        return False

    except Exception as e:
        print(f"  [❌] Lỗi: {e}")
        return False


def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    print("=" * 70)
    print("       🚀 REG PRO5 - AUTO TẠO PAGE & UPLOAD ẢNH 🚀")
    print("=" * 70)
    print("  [1] Reg Page (tạo page + dùng Avatar làm Cover tự động)")
    print("  [2] Check tổng số Page của acc")
    print("  [3] Chuyển Page → Acc Mẹ (Invite + Accept + Leave)")
    print("  [4] Setting (chỉnh delay & số lượng job)")
    print("  [5] Cookie (thêm / xóa / danh sách UID)")
    print("  [6] Proxy (thêm / xóa / danh sách proxy)")
    print("=" * 70)
    ten_type_display = "🇻🇳 Việt" if SETTINGS.get("ten_type", "viet") == "viet" else "🇺🇸 Mỹ"
    print(f"  ⚙️  Setting: so_luong={SETTINGS['so_luong']} | delay={SETTINGS['delay']}s | Tên: {ten_type_display}")
    print(f"  🖼️  Từ khóa Avatar: {SETTINGS.get('keyword_avatar', 'gái xinh rõ mặt')}")
    print(f"  🖼️  Từ khóa Cover: {SETTINGS.get('keyword_cover', 'gái xinh chụp ảnh full người')}")
    print(f"  🌐 Proxy: {SETTINGS.get('proxy', 'None')[:30] if SETTINGS.get('proxy') else 'None'}")
    print(f"  🍪 Cookie đã lưu: {len(load_cookies())}")
    print("=" * 70)

    choice = input("\n👉 Chọn chức năng (1/2/3/4/5/6): ").strip()

    # ── [6] Proxy manager ──
    if choice == "6":
        menu_proxy_manager()
        return

    # ── [5] Cookie manager ──
    if choice == "5":
        menu_cookie_manager()
        return

    # ── [4] Setting ──
    if choice == "4":
        print("\n" + "=" * 70)
        print("⚙️  SETTING - Cấu hình")
        print("=" * 70)
        print(f"  Hiện tại:")
        print(f"    • Số lượng job        : {SETTINGS['so_luong']}")
        print(f"    • Delay giữa mỗi job  : {SETTINGS['delay']}s")
        print(f"    • Loại tên             : {'🇻🇳 Tiếng Việt' if SETTINGS.get('ten_type', 'viet') == 'viet' else '🇺🇸 Tiếng Mỹ'}")
        print(f"    • Từ khóa Avatar      : {SETTINGS.get('keyword_avatar', 'gái xinh rõ mặt')}")
        print(f"    • Từ khóa Ảnh bìa     : {SETTINGS.get('keyword_cover', 'gái xinh chụp ảnh full người')}")
        print(f"    • Proxy               : {SETTINGS.get('proxy', 'None')}")
        print("=" * 70)

        # Số lượng job
        while True:
            try:
                raw = input(f"\n👉 Số lượng job mới (Enter giữ {SETTINGS['so_luong']}): ").strip()
                if raw == "":
                    break
                val = int(raw)
                if val < 1:
                    print("  [!] Số lượng phải >= 1")
                    continue
                SETTINGS["so_luong"] = val
                break
            except ValueError:
                print("  [!] Vui lòng nhập số nguyên hợp lệ")

        # Delay
        while True:
            try:
                raw = input(f"👉 Delay mới (giây, Enter giữ {SETTINGS['delay']}): ").strip()
                if raw == "":
                    break
                val = float(raw)
                if val < 0:
                    print("  [!] Delay không được âm")
                    continue
                SETTINGS["delay"] = val
                break
            except ValueError:
                print("  [!] Vui lòng nhập số hợp lệ")

        # Loại tên
        current_type = SETTINGS.get("ten_type", "viet")
        print(f"\n👉 Loại tên hiện tại: {'🇻🇳 Tiếng Việt' if current_type == 'viet' else '🇺🇸 Tiếng Mỹ'}")
        print("   [1] 🇻🇳 Tiếng Việt")
        print("   [2] 🇺🇸 Tiếng Mỹ")
        type_choice = input("👉 Chọn (1/2, Enter giữ nguyên): ").strip()
        if type_choice == "1":
            SETTINGS["ten_type"] = "viet"
            print("   ✅ Đã chọn tên Tiếng Việt")
        elif type_choice == "2":
            SETTINGS["ten_type"] = "my"
            print("   ✅ Đã chọn tên Tiếng Mỹ")

        # Từ khóa Avatar
        current_av = SETTINGS.get("keyword_avatar", "gái xinh rõ mặt")
        print(f"\n👉 Từ khóa Avatar hiện tại: '{current_av}'")
        raw = input("👉 Nhập từ khóa mới (Enter giữ nguyên): ").strip()
        if raw:
            SETTINGS["keyword_avatar"] = raw
            print(f"   ✅ Đã cập nhật: {raw}")

        # Từ khóa Ảnh bìa
        current_cv = SETTINGS.get("keyword_cover", "gái xinh chụp ảnh full người")
        print(f"\n👉 Từ khóa Ảnh bìa hiện tại: '{current_cv}'")
        raw = input("👉 Nhập từ khóa mới (Enter giữ nguyên): ").strip()
        if raw:
            SETTINGS["keyword_cover"] = raw
            print(f"   ✅ Đã cập nhật: {raw}")

        # Proxy
        print(f"\n👉 Proxy hiện tại: {SETTINGS.get('proxy', 'None')}")
        raw = input("👉 Proxy mới (Enter giữ nguyên): ").strip()
        if raw:
            SETTINGS["proxy"] = raw

        save_settings()
        print(f"\n[✅] Setting đã cập nhật!")
        print(f"    • Số lượng job : {SETTINGS['so_luong']}")
        print(f"    • Delay        : {SETTINGS['delay']}s")
        print(f"    • Loại tên     : {'🇻🇳 Tiếng Việt' if SETTINGS.get('ten_type', 'viet') == 'viet' else '🇺🇸 Tiếng Mỹ'}")
        print(f"    • Từ khóa Avatar: {SETTINGS.get('keyword_avatar', 'gái xinh rõ mặt')}")
        print(f"    • Từ khóa Cover : {SETTINGS.get('keyword_cover', 'gái xinh chụp ảnh full người')}")
        print(f"    • Proxy        : {SETTINGS.get('proxy', 'None')}")
        print("=" * 70)
        return

    # Các chức năng 1/2/3 cần cookie
    saved = load_cookies()
    cookie = ""
    if saved:
        print(f"\n[🍪] Có {len(saved)} cookie đã lưu:")
        for i, c in enumerate(saved, 1):
            print(f"  [{i}] UID {c.get('uid')} — {c.get('name') or '(chưa check)'}")
        print("  [0] Nhập cookie thủ công")
        pick = input("👉 Chọn cookie (số / 0): ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(saved):
            cookie = saved[int(pick) - 1]["cookie"]
            print(f"[✓] Dùng cookie UID {saved[int(pick) - 1].get('uid')}")

    if not cookie:
        cookie = input("\n👉 Nhập Cookie acc con: ").strip()
    if not cookie:
        print("❌ Vui lòng nhập cookie!")
        return

    # Lấy proxy từ settings
    proxy = SETTINGS.get("proxy", "")
    
    session = FacebookSession(cookie, proxy=proxy if proxy else None)

    if not session.extract_uid():
        print("❌ Cookie không có c_user!")
        return

    if not session.check_cookie():
        print("❌ Cookie không hợp lệ!")
        return

    if not session.get_tokens():
        print("❌ Không lấy được token!")
        return

    # ── [1] REG PAGE ──
    if choice == "1":
        so_luong = SETTINGS["so_luong"]
        delay_sec = SETTINGS["delay"]
        proxy = SETTINGS.get("proxy", "")
        
        # Rút gọn proxy để hiển thị trên ảnh
        proxy_display = proxy
        if proxy_display and len(proxy_display) > 40:
            proxy_display = proxy_display[:35] + "..."

        print("\n" + "=" * 70)
        print("🎯 TẠO PAGE & DÙNG AVATAR LÀM COVER")
        print("=" * 70)
        print(f"[⚙️] Dùng Setting: so_luong={so_luong} | delay={delay_sec}s")
        print(f"[🌐] Proxy: {proxy[:30] if proxy else 'None'}")
        print("    (Chỉnh tại mục [4] Setting)")
        print("=" * 70)

        success_count = 0
        fail_count = 0

        for job_idx in range(1, so_luong + 1):
            print(f"\n{'#'*70}")
            print(f"  🚀 JOB [{job_idx}/{so_luong}]")
            print(f"{'#'*70}")

            name, bio = ContentGenerator.generate()
            print(f"\n📝 Tên: {name}")
            print(f"📝 Bio: {bio}")

            result = session.create_page(name, bio)
            if not result.get("success"):
                print(f"❌ Tạo page thất bại: {result.get('error')}")
                fail_count += 1
                if job_idx < so_luong:
                    countdown_sleep(delay_sec, f"Job [{job_idx + 1}/{so_luong}]")
                continue

            page_id = result.get("page_id")
            print(f"\n[✅] Page ID: {page_id} — chờ 2 giây trước khi upload ảnh...")
            time.sleep(2)

            PinterestImageFetcher.reset_used()

            print(f"\n{'─'*60}")
            print(f"  [📸] UPLOAD AVATAR")
            print(f"{'─'*60}")
            avatar = SmartImageHandler.get_avatar(proxy=proxy if proxy else None)
            avatar_fbid = None
            if avatar:
                # Truyền proxy_text vào upload_avatar
                avatar_fbid = session.upload_avatar(page_id, avatar, proxy_text=proxy_display if proxy else None)
            else:
                print("  [⚠️] Không lấy được ảnh Avatar")

            ok_av = bool(avatar_fbid)

            time.sleep(2)

            print(f"\n{'─'*60}")
            print(f"  [🖼️] ÁP DỤNG AVATAR FBID LÀM COVER")
            print(f"{'─'*60}")
            ok_cv = False
            if avatar_fbid:
                ok_cv = session.upload_cover(page_id, avatar_fbid, proxy_text=proxy_display if proxy else None)
            else:
                print("  [⚠️] Avatar không có FBID → không thể đặt Cover")

            print("\n" + "=" * 70)
            print(f"🎉 HOÀN THÀNH JOB [{job_idx}/{so_luong}]!")
            print("=" * 70)
            print(f"✅ Page ID  : {page_id}")
            print(f"✅ Tên      : {name}")
            print(f"✅ Link     : https://facebook.com/{page_id}")
            print(f"{'✅' if ok_av else '❌'} Avatar    : {'THÀNH CÔNG' if ok_av else 'THẤT BẠI'}")
            print(f"{'✅' if ok_cv else '❌'} Ảnh bìa  : {'THÀNH CÔNG' if ok_cv else 'THẤT BẠI'}")
            if proxy:
                print(f"🌐 Proxy    : {proxy}")
            print("=" * 70)

            try:
                with open("success.txt", "a", encoding="utf-8") as f:
                    f.write(f"{page_id}|{name}|av={'ok' if ok_av else 'fail'}|cv={'ok' if ok_cv else 'fail'}|proxy={proxy if proxy else 'None'}|{datetime.now()}\n")
                print("💾 Đã lưu vào success.txt")
            except:
                pass

            success_count += 1

            if job_idx < so_luong:
                countdown_sleep(delay_sec, f"Job [{job_idx + 1}/{so_luong}]")

        print(f"\n{'='*70}")
        print(f"  📊 TỔNG KẾT REG PAGE")
        print(f"{'='*70}")
        print(f"  ✅ Thành công : {success_count}/{so_luong}")
        print(f"  ❌ Thất bại   : {fail_count}/{so_luong}")
        if proxy:
            print(f"  🌐 Proxy sử dụng: {proxy}")
        print(f"{'='*70}")

    # ── [2] CHECK PAGES ──
    elif choice == "2":
        pages = session.check_pages()
        if pages:
            try:
                with open("pages.txt", "w", encoding="utf-8") as f:
                    f.write(f"UID: {session.uid} | Tổng: {len(pages)} page\n")
                    f.write("=" * 60 + "\n")
                    for p in pages:
                        f.write(f"{p['id']} | {p['name']}\n")
                print(f"💾 Đã lưu danh sách vào pages.txt")
            except:
                pass
        else:
            print("[!] Không tìm thấy page nào")

    # ── [3] CHUYỂN PAGE ──
    elif choice == "3":
        print("\n" + "=" * 70)
        print("🔄 CHUYỂN PAGE → ACC MẸ (Invite + Accept + Leave)")
        print("=" * 70)

        print("\n[?] Bạn muốn:")
        print("  [A] Chuyển 1 page cụ thể (nhập Page ID)")
        print("  [B] Chuyển TẤT CẢ pages")
        sub = input("👉 Chọn (A/B): ").strip().upper()

        parent_uid = input("\n👉 Nhập UID Acc Mẹ: ").strip()
        if not parent_uid:
            print("❌ Cần nhập UID acc mẹ!")
            return

        parent_cookie = input("👉 Nhập Cookie Acc Mẹ (bỏ trống nếu không có): ").strip()
        if not parent_cookie:
            parent_cookie = None
            print("[!] Không có cookie mẹ → chỉ invite, không auto accept")

        print("\n💡 Facebook yêu cầu xác nhận mật khẩu trước khi invite.")
        password = input("👉 Nhập mật khẩu acc con (bỏ trống để bỏ qua): ").strip()
        if not password:
            password = None
            print("[!] Bỏ qua reauth - có thể thất bại")

        if sub == "A":
            page_id = input("\n👉 Nhập Page ID cần chuyển: ").strip()
            if not page_id:
                print("❌ Cần nhập Page ID!")
                return
            ok = run_transfer(session, page_id, parent_uid, password, parent_cookie)
            if not ok:
                print(f"\n❌ Chuyển page thất bại! Xem log bước nào lỗi ở trên.")

        elif sub == "B":
            pages = session.check_pages()
            if not pages:
                print("[!] Không có page nào!")
                return

            print(f"\n[→] Sẽ chuyển {len(pages)} page → UID {parent_uid}")

            success_count = 0
            fail_count = 0
            for i, p in enumerate(pages, 1):
                print(f"\n{'='*70}")
                print(f"  [{i}/{len(pages)}] {p['name']} ({p['id']})")
                ok = run_transfer(session, p['id'], parent_uid, password, parent_cookie)
                if ok:
                    success_count += 1
                else:
                    fail_count += 1
                if i < len(pages):
                    time.sleep(5)

            print(f"\n{'='*70}")
            print(f"  ✅ Thành công: {success_count}/{len(pages)}")
            print(f"  ❌ Thất bại  : {fail_count}/{len(pages)}")
            print(f"{'='*70}")

    else:
        print("❌ Chức năng không hợp lệ!")


if __name__ == "__main__":
    main()