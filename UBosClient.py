#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import base64
import hashli

# 导入BOS相关模块
from baidubce import exception
from baidubce.services import bos
from baidubce.services.bos import canned_acl
from baidubce.services.bos.bos_client import BosClient

# 从Python SDK导入BOS配置管理模块以及安全认证模块
from baidubce.bce_client_configuration import BceClientConfiguration
from baidubce.auth.bce_credentials import BceCredentials


class UBosClient(object):
    """
    BosClient
    """
    def __init__(self, access_key_id, secret_access_key, bucket_name='', endpoint=''):
        """
        初始化
        """
        super(UBosClient, self).__init__()

        # 创建BceClientConfiguration
        config = BceClientConfiguration(
            credentials=BceCredentials(access_key_id, secret_access_key), 
            endpoint=endpoint
        )
        # 设置请求超时时间
        config.connection_timeout_in_mills = 3000
        # 新建BosClient
        self.client = BosClient(config)
        self.bucket = bucket_name


    def check_bucket(self):
        """
        校验bucket是否存在
        """
        return not not self.client.does_bucket_exist(self.bucket)


    def check_object_key(self, object_key):
        """
        校验文件对象是否存在
        """
        if not self.check_bucket():
            return False
        try:
            self.client.get_object_meta_data(self.bucket, object_key)
            return True
        except:
            return False


    def mkdir(self, dir_name):
        """
        创建文件夹
        """
        if not self.check_bucket():
            return False
        try:
            self.client.put_object_from_string(self.bucket, '{}/'.format(dir_name), '')
            return True
        except:
            return False


    def get_all_files(self):
        """
        获取bucket所有文件对象集
        """
        file_list = []
        if not self.check_bucket():
            return file_list
        for fobj in self.client.list_all_objects(self.bucket):
            file_list.append({'name': fobj.key, 'size': fobj.size})
        return filelist


    def get_files_by_dir(self, dir_name):
        """
        获取文件夹子文件对象集
        """
        file_list = []
        if not self.check_bucket():
            return file_list
        prefix = '{}/'.format(dir_name)
        response = self.client.list_objects(self.bucket, prefix=prefix)
        for fobj in response.contents:
            if fobj.key == prefix:
                continue
            file_list.append({'name': fobj.key, 'size': fobj.size})
        return file_list


    def rmfile(self, object_key):
        """
        单一删除文件对象
        """
        if not self.check_bucket():
            return False
        self.client.delete_object(self.bucket, object_key)
        return True


    def rmfiles(self, object_keys):
        """
        批量删除
        """
        if not self.check_bucket():
            return False
        self.client.delete_multiple_objects(self.bucket, object_keys)
        return True


    def rmdir(self, dir_name):
        """
        删除目录, 需保证目录下无对象存在
        """
        if not self.check_bucket():
            return False
        prefix = '{}/'.format(dir_name)
        file_list = self.get_files_by_dir(dir_name)
        object_keys = [fobj['name'] for fobj in file_list if 'name' in fobj]
        self.rmfiles(object_keys)
        self.client.delete_object(self.bucket, prefix)
        return True


    def single_upload(self, object_key, file_path):
        """
        一次性上传
        """
        if not self.check_bucket():
            return False
        suffix = filename.split('.')[-1].lower()
        if suffix == 'mp4':
            ret = self.client.put_object_from_file(self.bucket, object_key, file_path, content_type='video/mp4')
        elif suffix in ['jpg', 'jpeg']:
            ret = self.client.put_object_from_file(self.bucket, object_key, file_path, content_type='image/jpeg')
        else:
            ret = self.client.put_object_from_file(self.bucket, object_key, file_path)
        print ret
        return True


    def get_upload_id(self, object_key):
        """
        断点续传获取upload_id
        """
        upload_id = None
        response = self.client.list_multipart_uploads(self.bucket)
        for item in response.uploads:
            if item.key == object_key:
                upload_id = item.upload_id
                break
        if not upload_id:
            upload_id = self.client.initiate_multipart_upload(self.bucket, object_key, content_type='video/mp4').upload_id
        return upload_id


    def multipart_upload(self, object_key, file_path):
        """
        断点续传
        """
        upload_id = self.get_upload_id(object_key)
        if not upload_id:
            return False
        left_size = os.path.getsize(file_path)
        offset, part_number, part_list = 0, 1, []
        while left_size > 0:
            # 设置每块为5MB
            part_size = 5 * 1024 * 1024
            if left_size < part_size:
                part_size = left_size
            for _ in (_ for _ in range(300)):
                try:
                    response = self.client.upload_part_from_file(
                        self.bucket, object_key, upload_id, part_number, part_size, file_path, offset
                    )
                    break
                except:
                    pass
            left_size -= part_size
            offset += part_size
            part_list.append({
                "partNumber": part_number,
                "eTag": response.metadata.etag
            })
            part_number += 1

        for _ in (_ for _ in range(300)):
            try:
                ret = self.client.complete_multipart_upload(self.bucket, object_key, upload_id, part_list)
                print ret
                return False
            except:
                pass


    def upload_file(self, object_key, file_path):
        """
        上传文件
        """
        file_size = os.path.getsize(file_name)
        if file_size > 5 * 1024 * 1024:
            # 断点续传
            self.multipart_upload(object_key, file_path)
        else:
            # 一次性上传
            self.single_upload(object_key, file_path)


def main():
    # 主函数
    pass


if __name__ == '__main__':
    main()
    pass
