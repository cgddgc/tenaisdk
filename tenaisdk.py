#!python3
# _*_coding:utf-8_*_
import base64
import urllib.parse, requests, time, uuid, random, hashlib, json
import logging

#import tenutils



class tenaiBot:
    def __init__(self, appid, apikey, loglevel=logging.DEBUG):
        self.appid = appid
        self.apikey = apikey
        self.tenlog = logging.getLogger('tenaibot')
        self.tenlog.setLevel(loglevel)
        clilog = logging.StreamHandler()
        clilog.setLevel(loglevel)
        clilog.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s", '%Y-%m-%d  %H:%M:%S %a'))

        self.tenlog.addHandler(clilog)

    def getMd5(self, s):        #计算md5
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    def getRandomStr(self, length=None):        #生成随机字符串，nonce_str
        c = length or random.randrange(5, 31)
        s = str(uuid.uuid1())
        smd5 = self.getMd5(s)
        return smd5[0:c]

    def sendPost(self, url, data):
        return requests.post(url, data)

    def sendGet(self, url):
        return requests.get(url)

    def chat(self, text, sessionid, retry=5):       #智能闲聊
        restext = '服务器繁忙，请稍后重试'
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat'
        jsondata = {'app_id': self.appid,
                    'time_stamp': int(time.time()),
                    'nonce_str': self.getRandomStr(),
                    'session': sessionid,
                    'question': text}
        signStr = self.getSign(jsondata)
        jsondata['sign'] = signStr
        self.tenlog.debug(jsondata)
        while retry:
            try:
                res = self.sendPost(apiUrl, jsondata)
                restext = json.loads(res.text.encode('utf-8'))['data']['answer']
                break
            except Exception as e:
                self.tenlog.error(e)
                time.sleep(0.5)
                retry -= 1
        # tenlog.debug(res.text)

        self.tenlog.info(restext)
        return restext

    def getSign(self, jsondata):        #签名函数
        paramList = list(jsondata.keys())
        paramList.sort()
        tstr = '&'.join(
            ['{}={}'.format(key, urllib.parse.quote_plus(str(jsondata[key]).encode('utf-8'))) for key in paramList])
        tstr += '&app_key=' + self.apikey
        # self.tenlog.debug(tstr)
        tstrmd5 = self.getMd5(tstr).upper()

        return tstrmd5

    def text2Voice_tts(self, text, vformat=3, vspeed=100, vspeaker=1, vaht=0, vapc=58, vvolume=0):  #语音合成（tts）
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/aai/aai_tts'

        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'speaker': str(vspeaker),
                    'format': str(vformat),
                    'volume': str(vvolume),
                    'speed': str(vspeed),
                    'text': text,
                    'aht': str(vaht),
                    'apc': str(vapc)}
        jsondata['sign'] = self.getSign(jsondata)
        getParam = urllib.parse.urlencode(jsondata)
        # self.tenlog.debug(getParam)
        url = '{}?{}'.format(apiUrl, getParam)
        res = self.sendGet(url)
        resdata = json.loads(res.text)
        resCode = resdata['ret']
        resMsg = ''
        if resCode == 0:
            # self.tenlog.debug(resdata['data']['speech'])
            resMsg = resdata['data']['speech']
            tenutils.writeMp3('test.mp3', resMsg)
        else:
            resMsg = resdata['msg']
            # self.tenlog.debug(res.text)

        return resCode, resMsg

    def text2Voice_tta(self, text, vspeaker=0, vspeed=0):       #语音合成（优图）
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/aai/aai_tta'
        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'speed': str(vspeed),
                    'text': text,
                    'model_type': str(vspeaker)}
        jsondata['sign'] = self.getSign(jsondata)
        getParam = urllib.parse.urlencode(jsondata)
        url = '{}?{}'.format(apiUrl, getParam)

        res = self.sendGet(url)
        resdata = json.loads(res.text)

        resCode = resdata['ret']
        resMsg = ''

        if resdata['ret'] == 0:
            resMsg = resdata['data']['voice']
            # self.tenlog.debug(resdata['data']['voice'])
            tenutils.writeMp3('test2.mp3', resMsg)
        else:
            resMsg = resdata['msg']
            # self.tenlog.debug(res.text)

        return resCode, resMsg

    def text2Voice(self, text, vspeaker=0, a=2, s=5):
        voiceb64str = ''

        while a:
            ret, voicemsg = self.text2Voice_tta(text, vspeaker=vspeaker)
            # print(ret, type(ret))
            if not (ret == 0):
                a -= 1
                time.sleep(0.6)
            else:
                voiceb64str = voicemsg
                break
        # print(a,s)

        if voiceb64str == '':
            while s:
                ret, voicemsg = self.text2Voice_tts(text, vspeaker=7)
                # print(ret, type(ret))
                if not (ret == 0):
                    s -= 1
                    time.sleep(0.6)
                else:
                    voiceb64str = voicemsg
                    break
        # self.tenlog.debug(voiceb64str)
        tenutils.writeMp3('testtest.mp3', voiceb64str)
        return voiceb64str

    def wordCom(self, text):
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/nlp/nlp_wordcom'
        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'text': text}
        jsondata['sign'] = self.getSign(jsondata)
        res = self.sendPost(apiUrl, jsondata)
        self.tenlog.debug(res.text)
        return res.text

    def img2text(self, imgpath):            #一句话描述图片
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/vision/vision_imgtotext'
        imgdata = ''
        with open(imgpath, 'rb') as f:
            imgdata = base64.b64encode(f.read()).decode('utf-8')
            f.close()

        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'image': imgdata,
                    'session_id': self.getRandomStr()}
        jsondata['sign'] = self.getSign(jsondata)
        res = self.sendPost(apiUrl, jsondata)
        self.tenlog.debug(res.text)
        return res.text

    def generalocr(self, imgpath):            #通用OCR
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'
        imgdata = ''
        with open(imgpath, 'rb') as f:
            imgdata = base64.b64encode(f.read()).decode('utf-8')
            f.close()

        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'image': imgdata}
        jsondata['sign'] = self.getSign(jsondata)
        res = self.sendPost(apiUrl, jsondata)
        self.tenlog.debug(res.text)
        return res.text

    def visionPorn(self, imgpath):            #图片鉴黄
        apiUrl = 'https://api.ai.qq.com/fcgi-bin/vision/vision_porn'
        imgdata = ''
        with open(imgpath, 'rb') as f:
            imgdata = base64.b64encode(f.read()).decode('utf-8')
            f.close()

        jsondata = {'app_id': self.appid,
                    'time_stamp': str(int(time.time())),
                    'nonce_str': self.getRandomStr(),
                    'image': imgdata}
        jsondata['sign'] = self.getSign(jsondata)
        res = self.sendPost(apiUrl, jsondata)
        self.tenlog.debug(res.text)
        return res.text


if __name__ == '__main__':
    tenai = tenaiBot(appid, apikey)
    # tenai.chat('最近有什么好电影', '990878')
    # tenai.text2Voice_tts('小哥哥你好啊, 我是腾讯AI， 很高兴为您服务', vspeaker = 6, vaht = 0,)
    #tenai.text2Voice('欢迎来到英雄联盟！')
    #tenai.wordCom('心情如何')
    #tenai.img2text('4095.jpg')
    #tenai.generalocr('4095.jpg')
    #tenai.visionPorn('d880af92-02af-42ee-b2ad-e9f5161ca0bf.jpg')
    pass