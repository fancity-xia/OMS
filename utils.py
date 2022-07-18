"""
调用华为云OMS API实现oss云存储数据迁移至OBS, 考虑带宽？考虑并发(任务并发数为5,如果超过OMS服务是否自动排队等待)？ 考虑队列？
使用python3 SDK接口将数据下载至指定路径
"""
import requests
from config import OSS, OBS, AK, SK
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkoms.v2.region.oms_region import OmsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkoms.v2 import *
import logging
import time
import tabulate
from collections import OrderedDict
from field import HELP
import argparse
import json
import sys
import signal
import re
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(pathname)s %(funcName)s %(message)s",
                    datefmt="%m-%d-%Y %I:%M:%S")


class InvalidParameter(Exception):
    pass


class SignalTimeoutError(Exception):
    pass


def acquire_token(user):
    """
    SDK比API更香
    """
    token_url = "https://" + user["iam_endpoint"] + "/v3/auth/tokens"
    token_body = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "domain": {
                            "name": user["domain_name"]
                        },
                        "name": user["iam_username"],
                        "password": user["iam_password"]
                    }
                }
            },
            "scope": {
                "project": {
                    "id": user["project_id"]
                }
            }
        }
    }
    header = {
        "Content-Type": "application/json;charset=utf8"
    }
    return requests.post(url=token_url, json=token_body, headers=header)


class OMS:

    def __init__(self, ak, sk):
        credentials = BasicCredentials(ak, sk)
        self.client = OmsClient.new_builder().with_credentials(credentials). \
            with_region(OmsRegion.value_of(OBS["region"])).build()

    def create_task(self, task_type, object_key="", list_file=""):
        """
        :param task_type: object,prefix, list,url_list
        :param object_key: [str]
        :param list_file: [file]
        :return:
        """
        try:
            request = CreateTaskRequest()
            dst_node_dst_node_req = DstNodeReq(**OBS)
            # if not isinstance(filelist, list):
            #    raise InvalidParameter(f"无效filelist参数值{filelist}, 必须为list")
            if task_type in ["object", "prefix"]:
                filelist = re.split(',', object_key)
                if len(filelist) == 0 or not filelist[0]:
                    Signal(interrupt, 100)
                src_node_src_node_req = SrcNodeReq(
                    **OSS,
                    object_key=filelist
                )
            elif task_type in ["list", "url_list"]:
                # if len(list_file) > 1:
                #    raise InvalidParameter(f"无效filelist参数值{filelist},len必须为1")
                src_node_src_node_req = SrcNodeReq(
                    **OSS,
                    list_file=ListFile(list_file_key=list_file, obs_bucket=OBS["bucket"])
                )
            else:
                raise InvalidParameter(f"无效task_type参数值{task_type}")
            request.body = CreateTaskReq(
                enable_failed_object_recording=True,
                enable_restore=False,
                # smn_config=smn_config_smn_config,
                enable_kms=False,
                dst_node=dst_node_dst_node_req,
                src_node=src_node_src_node_req,
                task_type=task_type,
            )
            response = self.client.create_task(request)
            logging.debug(response)
            return response, "response"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def list_task(self, limit=20):
        try:
            request = ListTasksRequest()
            request.limit = limit
            response = self.client.list_tasks(request)
            logging.debug(response)
            return response, "list"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def delete_task(self, task_id):
        try:
            request = DeleteTaskRequest()
            request.task_id = task_id
            response = self.client.delete_task(request)
            logging.debug(response)
            return response, "no-response"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def show_task(self, task_id):
        try:
            request = ShowTaskRequest()
            request.task_id = task_id
            response = self.client.show_task(request)
            logging.debug(response)
            return response, "dict"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def start_task(self, failtype, task_id):
        try:
            request = StartTaskRequest()
            request.task_id = task_id
            request.body = StartTaskReq(
                migrate_failed_object=failtype,
                dst_sk=OBS['sk'],
                dst_ak=OBS['ak'],
                src_sk=OSS['sk'],
                src_ak=OSS['ak']
            )
            response = self.client.start_task(request)
            logging.debug(response)
            print(response)
            return response, "no-response"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def stop_task(self, task_id):
        try:
            request = StopTaskRequest()
            request.task_id = task_id
            response = self.client.stop_task(request)
            logging.debug(response)
            return response, "no-response"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)

    def traffic_task(self, task_id, start_time, end_time, bindwidth):
        try:
            request = UpdateBandwidthPolicyRequest()
            request.task_id = task_id
            list_bandwidth_policy = [
                BandwidthPolicyDto(
                    end=end_time,
                    start=start_time,
                    max_bandwidth=bindwidth,
                )
            ]
            request.body = UpdateBandwidthPolicyReq(bandwidth_policy=list_bandwidth_policy)
            response = self.client.update_bandwidth_policy(request)
            logging.debug(response)
            return response, "no-response"
        except exceptions.ClientRequestException as e:
            logging.error(e.status_code)
            logging.error(e.request_id)
            logging.error(e.error_code)
            logging.error(e.error_msg)
            sys.exit(1)


def time_transfer_date(timestamp):
    ltime = time.localtime(timestamp/1000)
    return time.strftime("%Y-%m-%d %H:%M:%S", ltime)


def interrupt():
    raise SignalTimeoutError("是否将仓库内所有数据拷贝至OBS")


def Signal(func, second=None):
    """
    交互验证
    :param func: 中断函数, 建议使用raise报错
    :param second: seconds
    :return:
    """
    signal.signal(signal.SIGALRM, func)
    if not isinstance(second, int):
        second = 60
    signal.alarm(second)
    try:
        yn = input("是否继续运行? (Y/N) :")
    except SignalTimeoutError:
        yn = 'N'
    signal.alarm(0)
    if yn.strip().upper() == 'N':
        sys.exit(1)
    elif yn.upper() == 'Y':
        pass
    else:
        logging.info("等待超时, 退出0")
        sys.exit(1)


class Show:
    STATUS = {
        1: "等待调度",
        2: "正在执行",
        3: "停止",
        4: "失败",
        5: "成功"
    }

    def __init__(self, taskobj, retype):
        if retype in ["response", "dict"]:
            self.parser_search_task(taskobj.to_json_object())
        elif retype in ["no-response"]:  # start, stop 无响应值
            print("执行成功")
        else:
            self.parser_list_task(taskobj.to_json_object())

    @staticmethod
    def parser_list_task(tasklist):
        templist = []
        for task in tasklist['tasks']:
            temp = OrderedDict()
            for element in ["id", "name", "task_type"]:
                temp[element] = task[element]
            temp["src_bucket"] = task["src_node"]["bucket"]
            temp["cloud_type"] = task["src_node"]["cloud_type"]
            temp["dst_bucket"] = task["dst_node"]["bucket"]
            temp["status"] = Show.STATUS[task["status"]]
            temp["start_time"] = time_transfer_date(task["start_time"])
            task["end_time"] = task["start_time"] + task["total_time"]
            temp["end_time"] = time_transfer_date(task["end_time"])
            templist.append(temp)
        print(tabulate.tabulate(templist, headers="keys", tablefmt='fancy_grid', showindex=True))

    @staticmethod
    def parser_search_task(taskjson):
        if taskjson:
            print(json.dumps(taskjson, indent=4))


class Help:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Aliyun[oss] To HuaWeiYun[obs]")
        self.funcparsers = self.parser.add_subparsers(dest="cmd", title="任务控制台", help="")
        self.sparser()

    def sparser(self):
        for cmd in HELP.keys():
            tmp = self.funcparsers.add_parser(name=cmd, help=HELP[cmd]['help_text'])
            # flagbool = True  # 用于判断是否有参数, 如果没有参数需要将该cmd输入改为布尔值
            HELP[cmd].setdefault("exclusive_group", [[]])
            paramlist = []
            for exclusive_groups in HELP[cmd]["exclusive_group"]:
                if not len(exclusive_groups) > 1:
                    continue
                paramlist.extend(exclusive_groups)
                group = tmp.add_mutually_exclusive_group(required=True)
                for pg in exclusive_groups:
                    second_tmp = group.add_argument(f"--{pg}")
                    # second_tmp = tmp.add_argument(f"--{pg}")
                    for attribution in HELP[cmd][pg].keys():
                        setattr(second_tmp, attribution, HELP[cmd][pg][attribution])
            for param in HELP[cmd].keys():
                if param in paramlist:
                    continue
                if isinstance(HELP[cmd][param], dict):
                    second_tmp = tmp.add_argument(f"--{param}")
                    for attribution in HELP[cmd][param].keys():
                        setattr(second_tmp, attribution, HELP[cmd][param][attribution])
                else:
                    setattr(tmp, param, HELP[cmd][param])

    def eparser(self):
        args = self.parser.parse_args()
        kwargs = vars(args)
        cmd = kwargs.pop("cmd")
        if not cmd:
            self.parser.print_help()
            sys.exit(1)
        return cmd, kwargs


def test():
    # logging.info(acquire_token(USER))
    h = OMS(AK, SK)

    # h.create_migrate_task("object", ["F13YTSCCKF2526-03_FISiinR/WHB5EXONPEP00043189/
    # 201127_M003_V300081707_L04_FISiinR004518-655/"])
    # h.create_migrate_task("prefix", ["F13YTSCCKF2526-03_FISiinR/WHB5EXONPEP00043189/
    # 201127_M003_V300081707_L04_FISiinR004518-655/201127_M003_V300081707_L04_FISiinR004515-705/"])
    # url_list需要先将数据传输到某个桶里面 然后再访问该桶的这个文件, 文本内使用aliyun之类的URL路径
    # list  文件传输到桶里, 文本内 使用文件路径
    h.list_task()
    # h.show_task()
    #  1：等待调度 2：正在执行 3：停止 4：失败 5：成功


if __name__ == '__main__':
    test()
