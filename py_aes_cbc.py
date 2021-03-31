#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import json
import base64
from Crypto.Cipher import AES   # pip install pycrypto

class AesCrypter(object):
    """
    CBC 模式
    AES/CBC/PKCS7Padding 填充
    """
    def __init__(self, key):
        self.iv = self.key = key

    def encrypt(self, data):
        """
        加密
        """
        data = self.pkcs7padding(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = cipher.encrypt(data)
        return base64.b64encode(encrypted)

    def decrypt(self, data):
        """
        解密
        """
        data = base64.b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted = cipher.decrypt(data).decode('utf8')
        decrypted = self.pkcs7unpadding(decrypted)
        return decrypted

    def pkcs7padding(self, data):
        """
        填充方式, 密文需为16字节倍数, 不足则使用iv(偏移值填充)
        """
        bs = AES.block_size
        padding = bs - len(data) % bs
        if not padding: padding = bs
        padding_text = chr(padding) * padding
        return data + padding_text

    def pkcs7unpadding(self, data):
        pad = ord(data[-1])
        return data[:-pad]


def main():
    """
    main
    """
    token = "eyJhbGciOiJIUzI1NiJ9"
    key = token[2:18]
    e = AesCrypter(key)
    encData = ""
    ret = e.decrypt(encData)
    print ("decrypt", ret)
    # ostr = json.dumps(json.loads(ret))
    # print (str(e.encrypt(ostr), encoding='utf8'))
    # ret = e.decrypt(encData)
    # print ("decrypt", ret)

if __name__ == '__main__':
    main()
