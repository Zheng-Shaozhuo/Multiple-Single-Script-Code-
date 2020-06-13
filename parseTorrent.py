#!/usr/bin/env python
# coding=utf-8

import os
import codecs

# pip install bencode.py
from bencode import bdecode

class ParserTorrent(object):
    def __init__(self):
        """
        初始化函数
        """
        pass


    def get_meta_info(self, torrent):
        """
        返回解码后的 meta info 字典
        """
        # OrderedDict([
        #     ('announce-list', [['http://0205.uptm.ch:6969/announce'], ...,['udp://webmail.wookiespmc.com:6969/announce']]), 
        #     ('info', OrderedDict([
        #         ('length', 1300266714), 
        #         ('name', 'Holly Lace - Interview 27.09.19.mp4'), 
        #         ('piece length', 2097152), 
        #         ('pieces', '...')
        #         ])
        #     )
        # ])
        if os.path.isfile(torrent) is False:
            return None
        with open(torrent, "r") as f:
            try:
                return bdecode(f.read())
            except:
                return None


    def get_file_info(self, info):
        """
        获取单文件信息
        """
        ifile = {}
        if 'path' in info:
            ifile['name'] = info['path']
        elif 'name.utf-8' in info:
            ifile['name'] = info['name.utf-8']
        elif 'name' in info:
            ifile['name'] = info['name']
        else:
            pass
        if 'length' in info:
            ifile['size'] = round(float(info['length']) / 1024 / 1024, 2)
        return ifile


    def get_files_info(self, meta_info):
        """
        获取文件信息
        """
        ifiles = []
        if 'files' in meta_info['info']:
            # 有目录存在
            for _info  in meta_info['info']['files']:
                ifiles.append(self.get_file_info(_info))
        else:
            # 单文件
            ifiles.append(self.get_file_info(meta_info['info']))

        return ifiles


    def get_meta_detail(self, torrent):
        """
        获取详情
        """
        mdetail = {}
        meta_info = self.get_meta_info(torrent)
        if meta_info is None:
            return mdetail

        # create_date
        # 存放的是种子文件创建的时间
        if 'creation date' in meta_info:
            mdetail['create_date'] = meta_info['creation date']
        # createby
        # 生成种子文件的BT客户端软件的信息，如客户端名、版本号
        if 'createby' in meta_info:
            mdetail['createby'] = meta_info['createby']
        # comment
        # 关于torrent文件的描述信息
        if 'comment' in meta_info:
            mdetail['comment'] = meta_info['comment']
        # name
        if 'info' in meta_info and 'name' in meta_info['info']:
            mdetail['name'] = meta_info['info']['name']
        mdetail['files'] = self.get_files_info(meta_info)
        if len(mdetail['files']) > 0:
            mdetail['size'] = 0
            for _file in mdetail['files']:
                mdetail['size'] += _file.get('size', 0)
        return mdetail


if __name__ == "__main__":
    pass
