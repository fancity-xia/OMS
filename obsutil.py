from obs import ObsClient
from obs import PutObjectHeader
from config import OBS, ENDPOINT
import traceback
import os
import datetime
import sys


def time_now():
    """
    时间戳
    :return:
    """
    return datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d%H%M%S")


class Obsutil:
    def __init__(self):
        self.headers = PutObjectHeader()
        self.headers.contentType = 'text/plain'
        self.obsclient = ObsClient(access_key_id=OBS["ak"], secret_access_key=OBS['sk'], server=ENDPOINT)

    def put(self, localfile, remotefile=""):
        try:
            # if not remotefile:
            remotefile = os.path.basename(localfile)
            resp = self.obsclient.putFile(OBS['bucket'], remotefile, localfile, headers=self.headers)
            if resp.status < 300:
                print('requestId:', resp.requestId)
                print('etag:', resp.body.etag)
                print('versionId:', resp.body.versionId)
                print('storageClass:', resp.body.storageClass)
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
            return remotefile
        except:
            print(traceback.format_exc())

    def delete(self, remotefile):
        try:
            resp = self.obsclient.deleteObject(OBS['bucket'], remotefile)
            if resp.status < 300:
                print('requestId:', resp.requestId)
                print('deleteMarker:', resp.body.deleteMarker)
                print('versionId:', resp.body.versionId)
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
        except:
            print(traceback.format_exc())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"python3 {sys.argv[0]} <localfile>")
        sys.exit(1)
    obsobj = Obsutil()
    remote = obsobj.put(sys.argv[1])
    print(obsobj.delete(remote))

