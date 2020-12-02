# encoding: utf-8
import base64
import requests
from requests.exceptions import ReadTimeout, HTTPError, RequestException
from io import BytesIO
from zzcore import StdAns


class Ans(StdAns):
    """
    Rewriting the StdAns class to respond to commands.
    """
    def GETMSG(self):
        """
        Handling the commands.
        :return:
        if successfully identified: a string containing:
            caller uid;
            face probability;
            spoofing probability;
            quantified beauty score.
        """
        if len(self.parms) < 2:
            return "没有检测到待测图像。\n您可以这样使用打分指令：\n\"/rate\" + 空格 + 待测图片。\n祝您使用愉快。"
        url = str(self.parms[1].split("url=")[1].rstrip("]"))
        if not url:
            return "url解析错误：未发现待测图片。"
        try:
            response = requests.get(url)
            img_base64 = base64.b64encode(BytesIO(response.content).read())
        except ReadTimeout:
            return "request error: timeout. "
        except HTTPError:
            return "request error: HTTP error. "
        except RequestException:
            return "other request errors. "

        api_key = "zY9TrzMC2WWXnWZAHxBpFRzh"
        secret_key = "iX8h7nSIOekaEt6mEvwGFmCOFzGspodw"
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}' \
            .format(api_key, secret_key)
        response = requests.get(host)
        # access_token = ""
        if not response:
            return "token fetching error: no response. "
        try:
            access_token = response.json()["access_token"]
        except KeyError:
            return "token fetching error: missing access_token. "
        # if response:
        #     access_token = response.json()["access_token"]
            # msg += access_token + "\n"

        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/detect" + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        params = {"image": img_base64,
                  "image_type": "BASE64",
                  "max_face_num": "1",
                  "face_field": "face_num,beauty,probability,face_type,completeness,spoofing"}
        response = requests.post(request_url,
                                 data=params,
                                 headers=headers)
        if response:
            if response.json()["error_msg"] != "SUCCESS":
                return "图像错误。\n可能是由于您的图像清晰度/角度/光线不理想，算法未检测出人脸。\n请更换图片再试一次。"
            # msg = str(response.json()["result"]["face_list"][0]["beauty"])
            msg = ""
            msg += "恭喜您，{}提交的图像成功识别！\n".format(self.uid)
            msg += "是人脸的置信区间：{}\n".format(response.json()["result"]["face_list"][0]["face_probability"])
            msg += "是合成图片的置信区间：{}\n".format(round(float(response.json()["result"]["face_list"][0]["spoofing"]), 3))
            is_human = int((response.json()["result"]["face_list"][0]["face_type"]["type"] == "human"))
            prob = float(response.json()["result"]["face_list"][0]["face_type"]["probability"])
            msg += "二次元浓度：{}\n".format(round(float((1 - is_human) * prob + is_human * (1 - prob)), 3))
            # msg += "人工人浓度：{}\n".format(round(float(response.json()["result"]["face_list"][0]["spoofing"]), 3))
            score_raw = float(response.json()["result"]["face_list"][0]["beauty"])
            msg += "最终评分：{}分，即{}p。".format(round(score_raw / 10., 3), round(score_raw / 10. / 2.5, 3))
            return msg
        return "rating server error: timeout"
