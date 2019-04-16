# Controller to start inferencing from the given url
import subprocess
import threading
import time
import os
import object_detection as od
import pafy

INFERENCE_PIPE = '/url-feed/run/inference.mkv'
RTMP_STREAM = 'rtmp://localhost/show/stream'

#
#  The processing of the video stream from an URL flows as follows
#
#  Step 1. ingressURL => | _model.infer | => INFERENCE_PIPE
#  Step 2. INFERENCE_PIPE => | _streamToRTMP | => RTMP_STREAM
#
#  The above RTMP_Stream is then finally served over the web via nginx.
#  RTMP_STREAM => | nginx | => web
#


class StreamController:
    def __init__(self):
        self._runCount = 0
        self._lock = threading.Lock()
        self._serve_inference_proc = None
        self._inference_pipe = INFERENCE_PIPE
        self._rtmp_stream = RTMP_STREAM
        self._model = od.objectDetectionModel()
        self._model.setup()

        self._video_metadata = {}

    def _stream_to_RTMP(self):
        # Cleanup if required
        if self._serve_inference_proc is not None and self._serve_inference_proc.returncode is None:
            self._serve_inference_proc.kill()
            self._serve_inference_proc.wait()
            os.remove(INFERENCE_PIPE)

        self._serve_inference_proc = subprocess.Popen(
            ['/usr/bin/ffmpeg',
             '-re',
             '-i', self._inference_pipe,
             '-vcodec', 'libx264',
             '-vprofile', 'high444',
             '-g', '30',
             '-probesize', '32',
             '-acodec', 'aac',
             '-strict', '-2',
             '-f', 'flv',
             self._rtmp_stream])

    def _begin_inference(self, ingressURL, video_url):
        # Stop and Wait for any existing inference to finish
        self._lock.acquire()
        self._model.stopInference = True
        while self._runCount > 0:
            self._lock.release()
            print("Waiting for existing inference to finish")
            time.sleep(1)
            self._lock.acquire()
        self._model.stopInference = False
        self._runCount += 1
        self._lock.release()
        print("Starting inference on %s" % (ingressURL))
        # Serve the video inference, Step 2 above. Its fine to start it before Step 1.
        self._stream_to_RTMP()

        # Infer Video, Step 1. above. This will keep working on the stream until done.
        self._model.infer(video_url, self._inference_pipe)
        if self._serve_inference_proc is not None:
            self._serve_inference_proc.kill()
            self._serve_inference_proc.wait()
        self._lock.acquire()
        self._runCount -= 1
        self._lock.release()
        print("Finished inference")

    def start_inference(self, ingressURL):
        # This will throw an exception if the ingressURL is not a valid youtube url
        metadata = self.metadata(ingressURL)
        thr = threading.Thread(
            target=self._begin_inference,
            args=(ingressURL, metadata['video_url']))
        thr.name = "inference"
        thr.daemon = True
        thr.start()

    def _get_metadata(self, url):
        if url not in self._video_metadata:
            v = pafy.new(url)
            self._video_metadata[url] = {
                'video_url': v.getbestvideo().url,
                'thumb_url': v.bigthumbhd or v.bigthumb or v.thumb,
            }

    def metadata(self, url):
        self._get_metadata(url)
        return self._video_metadata[url]
