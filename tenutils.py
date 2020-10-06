#python3
#-*-coding:utf-8-*-

import base64, io, json
from tenaisdk import tenaiBot

tenai = tenaiBot(appid, apikey)

def writeFileForTest(filename, text):
    with open(filename, 'wb') as f:
        f.write(text.encode('utf-8'))
        f.close()

def writeMp3(filename, base64Str):
    bytecode = base64.b64decode(base64Str)
    with open(filename, 'wb') as f:
        f.write(bytecode)
        f.close()

def base642FileObject(base64Str):
    return io.BytesIO(base64.b64decode(base64Str))

def getVoiceMediaId(robot, base64Str, retry = 3):
    mediaid = ''
    while retry:
        try:
            data = robot.client.upload_media('voice', base642FileObject(base64Str))
            break
        except Exception as e:
            retry -= 1
    mediaid = data['media_id']
    return mediaid

def text2VoiceReply(robot, message, text):
    base64Str = tenai.text2Voice(text)
    return robot.VoiceReply(message = message, media_id = getVoiceMediaId(robot, base64Str))


