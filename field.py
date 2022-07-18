"""
对Help中每一个参数进行描述定义
"""

HELP = {
        "create_task": {
            "help_text": "创建任务",
            "exclusive_group": [["object_key", "list_file"]],
            "task_type": {
                "choices": ["prefix", "list", "url_list", "object"],
                "help": "prefix前缀,object指具体文件或者文件名; list/url_list则需要将指定文件写入文本并上传至同一区域可访问的目的桶",
                "default": "object",
            },
            "object_key": {
                "help": "字符串, 当task_type为prefix/object时, 多个用逗号隔开",
                "required": False
            },
            "list_file": {
                "help": "文件, 当task_type为list/url_list时使用, 请确认文件已上传至obs桶内",
                "required": False
            }
        },
        "show_task": {
            "help_text": "展示指定任务",
            "task_id": {
                "help": "任务id, 每次创建任务可生成",
                "required": True
            }
        },
        "list_task": {
            "help_text": "列出所有任务",
            "action": "store_true",
            "limit": {
                "help": "展示数量, 默认20",
                "default": 20,
            }
        },
        "start_task": {
            "help_text": "开始任务(一般用于暂停任务之后)",
            "task_id": {
                "help": "任务id, 每次创建任务可生成",
                "required": True
            },
            "failtype": {
                "help": "全部重传(False), 失败重传(True)",
                "action": "store_true",
                "default": False
            }
        },
        "stop_task": {
            "help_text": "暂停任务",
            "task_id": {
                "help": "任务id, 每次创建任务可生成",
                "required": True
            }
        },
        "delete_task": {
            "help_text": "删除任务",
            "task_id": {
                "help": "任务id, 每次创建任务可生成",
                "required": True
            }
        },
        "traffic_task": {
            "help_text": "任务流量控制",
            "task_id": {
                "help": "任务id, 每次创建任务可生成",
                "required": True
            },
            "start_time": {
                "help": "任务开始时间, 格式(HH:MM)",
                "required": True
            },
            "end_time": {
                "help": "任务结束时间, 格式(HH:MM)",
                "required": True
            },
            "bindwidth": {
                "help": "流量大小, 1024*1024为最小值(Mb)",
                "type": int,
                "required": True
            }
        }
    }
